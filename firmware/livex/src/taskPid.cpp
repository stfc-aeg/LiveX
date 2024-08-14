#include <taskPid.h>

// Full definitions below core task
void thermalGradient();
void autoSetPointControl();
void runPID(String pid);

// Task to be run on core 0 to control devices.
// This includes the PID operation, motor driving, and calculation of thermal gradient and auto set point control.
// Flags are set by timers.
void Core0PIDTask(void * pvParameters)
{
  Serial.print("Task 2 running on core ");
  Serial.println(xPortGetCoreID());
  delay(1000);

  for(;;)
  {
    if (pidFlag)
    {
      if (LOG_INTERRUPTS && USE_EXTERNAL_INTERRUPT) {
        if (interruptCounter % LOG_INTERRUPTS_INTERVAL == 0)
        {
          Serial.println(interruptCounter);
        }
      }
      // Get thermocouple readings for input
      PID_A.input = mcp[0].readThermocouple(); // First thermocouple for A
      PID_B.input = mcp[1].readThermocouple(); // Second thermocouple for B

      // Write thermocouple output to modbus registers
      modbus_server.floatToInputRegisters(MOD_THERMOCOUPLE_A_INP, PID_A.input);
      modbus_server.floatToInputRegisters(MOD_THERMOCOUPLE_B_INP, PID_B.input);
      modbus_server.floatToInputRegisters(MOD_COUNTER_INP, counter);
      counter = counter +1;

      // Create a buffer object, add selected attributes, add it to the buffer if not full
      if (modbus_server.coilRead(MOD_ACQUISITION_COIL))
      {
        // Reset counter if we haven't already done so
        if (!acquiringFlag)
        {
          counter = 1;
          acquiringFlag = true;
        }
        // Construct object
        BufferObject obj;
        obj.counter = counter;
        obj.temperatureA = PID_A.input;
        obj.temperatureB = PID_B.input;

        // Queue only if there is room in the buffer
        if (buffer.isFull())
        {
          // Serial.print(".");
        }
        else
        {
          buffer.enqueue(&obj);
        }
      }
      else
      {
        // Counter will be set to 1 when starting acquisition
        acquiringFlag = false;
      }

      runPID("A");
      runPID("B");

      // Set flag back to false for timer
      pidFlag=false;
    }

    if (secondaryFlag)
    {
      // Thermal modifiers
      thermalGradient();
      autoSetPointControl();

      // Motor control (if enabled)
      if (modbus_server.readBool(MOD_MOTOR_ENABLE_COIL))
      {
        bool direction = modbus_server.readBool(MOD_MOTOR_DIRECTION_COIL);
        direction *= 4095; // Either 4095 (max out) or 0 (no out)

        float speed = modbus_server.combineHoldingRegisters(MOD_MOTOR_SPEED_HOLD); // exactly how this is calculated is TBC

        // analogWrite does PWM
        gpio.digitalWrite(PIN_MOTOR_DIRECTION, direction);
        gpio.analogWrite(PIN_MOTOR_PWM, speed);
      }
      else
      {
        // Write 0 (no motor) if motor control disabled
        gpio.analogWrite(PIN_MOTOR_PWM, 0);
      }

      // Always read LVDT regardless of motor enable
      float lvdt = gpio.analogRead(PIN_MOTOR_LVDT_IN);

      // No obvious conversion formula, but readings of values at positions are known.
      // Max height is at ~1700, minimum at ~200, total range of 9.5mm.
      // This covers a range of 7.28V by current positioning of LVDT.
      float position = (1700 -(lvdt)) * (9.5 / 1500); // mm/mV

      modbus_server.floatToInputRegisters(MOD_MOTOR_LVDT_INP, position);

      secondaryFlag = false;
    }
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
  modbus_server.writeInputRegisters(MOD_GRADIENT_THEORY_INP, (uint16_t*)(&theoretical), 2);
  modbus_server.writeInputRegisters(MOD_GRADIENT_ACTUAL_INP, (uint16_t*)(&actual), 2);

  // Write gradient target setpoints for UI use
  modbus_server.writeInputRegisters(MOD_GRADIENT_SETPOINT_A_INP, (uint16_t*)(&PID_A.gradientSetPoint), 2);
  modbus_server.writeInputRegisters(MOD_GRADIENT_SETPOINT_B_INP, (uint16_t*)(&PID_B.gradientSetPoint), 2);

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

  if (DEBUG)
  {
    Serial.print("Autosp rate: ");
    Serial.print(rate);
    Serial.print(" | interval: ");
    Serial.print(TIMER_PID/1000000);
  }
}

// Run a specified PID (A or B) then apply gradient, ASPC, new PID terms, etc.
void runPID(String pid)
{
  PIDController* PID = nullptr;
  PIDAddresses addr;
  // Identify which PID
  if (pid == "A")
  {
    PID = &PID_A;
    addr = pidA_addr;
  } else if (pid == "B")
  {
    PID = &PID_B;
    addr = pidB_addr;
  } else
  {
    Serial.println("Improper PID run call, no PID specified.");
    return;
  }

  if (PID != nullptr)
  {
    // Check PID enabled
    if (modbus_server.readBool(addr.modPidEnableCoil))
    {
      // Check PID tunings
      double newKp = double(modbus_server.combineHoldingRegisters(addr.modKpHold));
      double newKi = double(modbus_server.combineHoldingRegisters(addr.modKiHold));
      double newKd = double(modbus_server.combineHoldingRegisters(addr.modKdHold));
      PID->check_PID_tunings(newKp, newKi, newKd);

      // Check thermal gradient enable status and use setpoint accordingly
      if (modbus_server.readBool(MOD_GRADIENT_ENABLE_COIL))
      {
        PID->setPoint = PID->gradientSetPoint;
      }
      else
      {
        PID->setPoint = modbus_server.combineHoldingRegisters(addr.modSetPointHold);
      }

      // Calculate PID output
      PID->run();

      // Write PID output
      modbus_server.floatToInputRegisters(addr.modPidOutputInp, PID->output);

      if (INVERT_OUTPUT_SIGNAL)
      {
        float inv_output = PID_OUTPUT_LIMIT - PID->output;
        gpio.analogWrite(addr.outputPin, inv_output);
      }
      else
      {
        gpio.analogWrite(addr.outputPin, PID->output);
      }

      // Check autosp enable status. If enabled, add rate to setpoint via holding register
      if (modbus_server.readBool(MOD_AUTOSP_ENABLE_COIL))
      {
        modbus_server.floatToHoldingRegisters(addr.modSetPointHold, (PID->setPoint + PID->autospRate));
        PID->gradientSetPoint = PID->gradientSetPoint + PID->autospRate;
      }
    }
    else
    { // Write 0 if PID is not enabled.
      gpio.analogWrite(addr.outputPin, 0);
    }
  }
  else
  {
    gpio.analogWrite(addr.outputPin, 0);
  }
}
