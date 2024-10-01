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
    if (modbus_server.readBool(MOD_GRADIENT_UPDATE_COIL))
    {
      xSemaphoreTake(gradientAspcMutex, portMAX_DELAY);
      thermalGradient();
      xSemaphoreGive(gradientAspcMutex);
    }
    if (modbus_server.readBool(MOD_ASPC_UPDATE_COIL))
    {
      xSemaphoreTake(gradientAspcMutex, portMAX_DELAY);
      autoSetPointControl();
      xSemaphoreGive(gradientAspcMutex);
    }
  }

  if(streamClient.connected()) // check first, then poll
  {
    char c = streamClient.read();
    // Serial.print(".");

    // Dequeue object, if its not a nullptr, write its data out
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

  // Calculate midpoint and 
  float setPointA = modbus_server.combineHoldingRegisters(MOD_SETPOINT_A_HOLD);
  float setPointB = modbus_server.combineHoldingRegisters(MOD_SETPOINT_B_HOLD);
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

  // Calculate gradient target setpoints
  PID_A.gradientSetPoint = midpoint + (signA * gradientModifier);
  PID_B.gradientSetPoint = midpoint + (signB * gradientModifier);

  // Actual temperature difference
  float actual = fabs(PID_A.input - PID_B.input);

  // Write relevant values to modbus
  modbus_server.floatToInputRegisters(MOD_GRADIENT_THEORY_INP, theoretical);
  modbus_server.floatToInputRegisters(MOD_GRADIENT_ACTUAL_INP, actual);

  // Write gradient target setpoints for UI use
  modbus_server.floatToInputRegisters(MOD_GRADIENT_SETPOINT_A_INP, PID_A.gradientSetPoint);
  modbus_server.floatToInputRegisters(MOD_GRADIENT_SETPOINT_B_INP, PID_B.gradientSetPoint);

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
  rate = rate * (static_cast<float>(TIMER_PID)/1000000); // e.g.: 0.5 * 20x10^3/1000x10^3 = 0.01 = 50 times per second
  PID_A.autospRate = rate;
  PID_B.autospRate = rate;

  // Get img per degree
  float imgPerDegree = modbus_server.combineHoldingRegisters(MOD_AUTOSP_IMGDEGREE_HOLD);

  // Calculate midpoint. Fabs in case B is higher temp
  float midpoint = fabs((PID_A.input + PID_B.input) / 2);
  modbus_server.floatToInputRegisters(MOD_AUTOSP_MIDPT_INP, midpoint);

  // Reset 'value updated' coil to not repeatedly fire this function
  modbus_server.writeBool(MOD_ASPC_UPDATE_COIL, 0);

  if (DEBUG)
  {
    Serial.print("Autosp rate: ");
    Serial.print(rate);
    Serial.print(" | interval: ");
    Serial.print(TIMER_PID/1000000);
  }
}
