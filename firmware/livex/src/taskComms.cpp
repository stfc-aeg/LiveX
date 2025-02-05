#include <taskComms.h>

void thermalGradient();
void autoSetPointControl();

// Check and poll connections. If no clients for 30 seconds, 'time out' and write 0 for PID/heating.
void manageComms()
{
  if(!(modbusClient.connected())) // Check if there's no existing connection...
  {
    modbusClient = modbusEthServer.available();
    if (modbusClient){
      modbus_server.accept(modbusClient);
    }
  }
  else // ...poll it if we do find one
  {
    modbus_server.poll();
    connectionTimer = millis();

    /*
      Check client connection
      If there is one, poll it and also check if the gradient/ASPC values have been updated
      If they have, then do the relevant calculation(s) with a mutex
      Otherwise these calculations do not need to be done
    */ 

    // Mutex taken and given within each statement, as both might not run
    // and no need to take it every time even if values are not updated
    if (modbus_server.readBool(MOD_SETPOINT_UPDATE_COIL))
    {
      xSemaphoreTake(gradientAspcMutex, portMAX_DELAY);
      updateSetPoints();
      xSemaphoreGive(gradientAspcMutex);
    }
    if (modbus_server.readBool(MOD_GRADIENT_UPDATE_COIL))
    {
      xSemaphoreTake(gradientAspcMutex, portMAX_DELAY);
      thermalGradient();
      xSemaphoreGive(gradientAspcMutex);
    }
    if (modbus_server.readBool(MOD_FREQ_ASPC_UPDATE_COIL))
    {
      xSemaphoreTake(gradientAspcMutex, portMAX_DELAY);
      // Handle frequency update first
      float new_freq = modbus_server.combineHoldingRegisters(MOD_FURNACE_FREQ_HOLD);
      // Assign value to correct variable
      interruptFrequency = new_freq;

      // PID sampleTime is in milliseconds
      float newSampleTime = floor(1000 / interruptFrequency);
      // Set sample time
      PID_A.myPID_.SetSampleTime(newSampleTime);
      PID_A.myPID_.SetSampleTime(newSampleTime);

      if (DEBUG)
      {
        Serial.print("new frequency: ");
        Serial.print(interruptFrequency);
        Serial.print(" | sample time: ");
        Serial.println(newSampleTime);
      }

      // This relies on frequency and rate/cooling,
      // so do it after frequency check/change.
      autoSetPointControl();
      xSemaphoreGive(gradientAspcMutex);
    }
  }

  if(streamClient.connected()) // check first, then poll
  {
    char c = streamClient.read();
    // Serial.print(".");

    BufferObject* dequeued = buffer.dequeue();
    if (dequeued != nullptr)
    {
      tcpEthServer.write((uint8_t*)dequeued, sizeof(BufferObject));
    }
  }
  else
  {
    streamClient = tcpEthServer.available();
  }

  // Disable heaters if no connection for 30 seconds. Checked only if no current connection.
  long int elapsedTime = millis() - connectionTimer;
  if (elapsedTime > INTERVAL_TIMEOUT)
  {
    Serial.println("Timeout: no connection. Disabling PID behaviour (write 0).");
    modbus_server.coilWrite(MOD_PID_ENABLE_A_COIL, 0);
    modbus_server.coilWrite(MOD_PID_ENABLE_B_COIL, 0);
    // Reset timer so writing doesn't occur every single loop
    connectionTimer = millis();
  }
}

void updateSetPoints()
{
  PID_A.baseSetPoint = modbus_server.combineHoldingRegisters(MOD_SETPOINT_A_HOLD);
  PID_B.baseSetPoint = modbus_server.combineHoldingRegisters(MOD_SETPOINT_B_HOLD);
  // When setpoints are updated, thermal gradient will also need adjusting as modifiers will change

  if (DEBUG)
  {
    Serial.print("New baseSetPoint for PID A: ");
    Serial.println(PID_A.baseSetPoint);
    Serial.print("New baseSetPoint for PID B: ");
    Serial.println(PID_B.baseSetPoint);
  }
  thermalGradient();
  // Set coil back to 0 to prevent continuously calling this function
  modbus_server.writeBool(MOD_SETPOINT_UPDATE_COIL, 0);
}

// Thermal gradient is based off of midpoint of heater setpoints and overrides them
void thermalGradient()
{
  // Get temperature (K) per mm
  float wanted = modbus_server.combineHoldingRegisters(MOD_GRADIENT_WANTED_HOLD);
  // Get distance (mm)
  float distance = modbus_server.combineHoldingRegisters(MOD_GRADIENT_DISTANCE_HOLD);
  // Theoretical temperature gradient (k/mm * mm = k)
  float theoretical = wanted * distance;
  float gradientModifier = theoretical/2;

  // Calculate midpoint and signs
  float setPointA = PID_A.baseSetPoint;
  float setPointB = PID_B.baseSetPoint;
  float midpoint = (setPointA + setPointB) / 2.0;

  float signA, signB;

  // High heater is A (0) or B (1)?
  bool high = modbus_server.coilRead(MOD_GRADIENT_HIGH_COIL);

  if (!high)  // 0 = A = false
  {
    signA = 1.0;
    signB = -1.0;
  }
  else if (high)  // 1 = B = true
  {
    signA = -1.0;
    signB = 1.0;
  }

  // 'gradient setpoint' is what the setpoint would be to make the requested gradient
  // based on the current base setpoints
  float gradientSP_A = midpoint + (signA * gradientModifier);
  float gradientSP_B = midpoint + (signB * gradientModifier);

  // the PID's 'gradient modifier' is what would need to be applied to the bSP to get that setpoint
  // e.g.: bSP of 100/200, gradient of 20, gSP of 150+/-10, so gMod is -/+40 for PIDs respectively
  PID_A.gradientModifier = gradientSP_A - setPointA;
  PID_B.gradientModifier = gradientSP_B - setPointB;
  // A positive value means that gradient being enabled increases the active setpoint

  // Actual temperature difference
  float actual = fabs(PID_A.input - PID_B.input);

  // Write relevant values to modbus
  modbus_server.floatToInputRegisters(MOD_GRADIENT_THEORY_INP, theoretical);
  modbus_server.floatToInputRegisters(MOD_GRADIENT_ACTUAL_INP, actual);

  // Reset 'value updated' coil to not repeatedly fire this function
  modbus_server.writeBool(MOD_GRADIENT_UPDATE_COIL, 0);

  if (DEBUG)
  {
    Serial.print("gradient midpoint: ");
    Serial.println(midpoint);
    Serial.print("gradient modifier: ");
    Serial.println(gradientModifier);
  }
}

// Increment setPoint by an average rate per second
void autoSetPointControl()
{
  // Get rate
  float rate = modbus_server.combineHoldingRegisters(MOD_AUTOSP_RATE_HOLD);

  // Heating (1) or cooling (0)?
  bool heating = modbus_server.coilRead(MOD_AUTOSP_HEATING_COIL);

  if (!heating)
  { 
    // Rate should be a positive value with 'direction' determined by heating option
    rate = -rate;
  }

  // Rate is average K/s, but value depends on PID interval
  rate = rate * (static_cast<float>(1/interruptFrequency)); // e.g.: 0.5 * 20x10^3/1000x10^3 = 0.01 = 50 times per second
  PID_A.autospRate = rate;
  PID_B.autospRate = rate;

  // Get img per degree
  float imgPerDegree = modbus_server.combineHoldingRegisters(MOD_AUTOSP_IMGDEGREE_HOLD);

  // Calculate midpoint. Fabs in case B is higher temp
  float midpoint = fabs((PID_A.input + PID_B.input) / 2);
  modbus_server.floatToInputRegisters(MOD_AUTOSP_MIDPT_INP, midpoint);

  // Reset 'value updated' coil to not repeatedly fire this function
  modbus_server.writeBool(MOD_FREQ_ASPC_UPDATE_COIL, 0);

  if (DEBUG)
  {
    Serial.print("Autosp rate (per PID call): ");
    Serial.print(rate);
    Serial.print(" | interval: ");
    Serial.println(1/interruptFrequency);
  }
}
