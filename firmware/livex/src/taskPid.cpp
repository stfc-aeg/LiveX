#include <taskPid.h>

// Full definitions below core task
// void thermalGradient();
// void autoSetPointControl();
void runPID(PIDEnum pid);
void fillPidBuffer(BufferObject& obj);
void runOverride(PIDEnum pid);

// Task to be run on core 0 to control devices.
// This includes the PID operation, motor driving, and calculation of thermal gradient and auto set point control.
// Flags are set by timers.
void Core0PIDTask(void * pvParameters)
{
  Serial.print("Task 2 running on core ");
  Serial.println(xPortGetCoreID());
  delay(1000);

  // Without triggers, this task sets off the watchdog timer.
  // Core 1, loop()/manageComms(), services it automatically, so we can just turn it off here.
  disableCore0WDT();

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
      xSemaphoreTake(gradientAspcMutex, portMAX_DELAY);
      // Read A
      int idx = modbus_server.combineHoldingRegisters(MOD_HEATERTC_A_IDX_HOLD);
      if (0<=idx && idx<num_mcp)
      {
        float result = mcp[idx].readThermocouple();
        PID_A.input = result;
        modbus_server.floatToInputRegisters(MOD_HEATERTC_A_INP, PID_A.input);
      }

      // Read B
      idx = modbus_server.combineHoldingRegisters(MOD_HEATERTC_B_IDX_HOLD);
      if (0<=idx && idx<num_mcp)
      {
        float result = mcp[idx].readThermocouple();
        PID_B.input = result;
        modbus_server.floatToInputRegisters(MOD_HEATERTC_B_INP, PID_B.input);
      }

      // Read extra thermocouples only once per second - when counter is multiple of pid frequency
      // Small tolerance for float errors
      if (fmod(counter, interruptFrequency) <= 1e-6f)
      { // num_mcp -2 as we have read two already
        for (int i=0; i<num_mcp-2; i++)
        {
          // Read extra thermocouples
          idx = modbus_server.combineHoldingRegisters(MOD_EXTRATC_A_IDX_HOLD + (i-2)*2);
          if (0<=idx && idx<num_mcp)
          {
            float result = mcp[idx].readThermocouple();
            modbus_server.floatToInputRegisters(MOD_EXTRATC_A_INP+(i*2), result);
          }
        }
      }
      xSemaphoreGive(gradientAspcMutex);

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

        // buffer object
        float error = PID_A.setPoint - PID_A.input;
        BufferObject obj;
        fillPidBuffer(obj); // Convenience/readability function
        // Queue only if there is room in the buffer
        if (buffer.isFull()) { /* Serial.print("."); */ }
        else { buffer.enqueue(&obj); }
      }
      else
      {
        // Counter will be set to 1 when starting acquisition
        acquiringFlag = false;
      }
      // Semaphore needed for all PID runs as gradient/ASPC calculations are used
      xSemaphoreTake(gradientAspcMutex, portMAX_DELAY);

      bool override_upper = modbus_server.coilRead(MOD_OUTPUT_OVERRIDE_UPPER_COIL);
      bool override_lower = modbus_server.coilRead(MOD_OUTPUT_OVERRIDE_LOWER_COIL);
      if (override_upper) { runOverride(A); } else { runPID(A); }
      if (override_lower) { runOverride(B); } else { runPID(B); }

      // These calculations need to occur whenever the temperatures are read
      // Actual temperature difference
      float actual = fabs(PID_A.input - PID_B.input);
      modbus_server.floatToInputRegisters(MOD_GRADIENT_ACTUAL_INP, actual);
      // Calculate midpoint. Fabs in case B is higher temp
      float midpoint = fabs((PID_A.input + PID_B.input) / 2);
      modbus_server.floatToInputRegisters(MOD_AUTOSP_MIDPT_INP, midpoint);
      xSemaphoreGive(gradientAspcMutex);
      xSemaphoreGive(gradientAspcMutex);

      // Set flag back to false for timer
      pidFlag=false;
    }
    /*
      Secondary flag is gone, 'moved' to TaskComms. No timer anymore
      This task just waits for the pidFlag.

      Eventually this could include the motor control.
      Interrupt doesn't really work for that, but maybe an enum saying which is enabled
      would be good, then it can be driven and run secondarily to the pidFlag. 
    */
  }
}

// Override a PID's output to a register-specified value
// Override does not respect inversion or output scaler for simplicity
void runOverride(PIDEnum pid = PIDEnum::UNKNOWN)
{
  PIDAddresses addr;
  switch (pid)
  {
    case PIDEnum::A:
      addr = pidA_addr;
      break;
    case PIDEnum::B:
      addr = pidB_addr;
      break;
    default:
      Serial.println("Improper runOverride call, no PID specified");
      return;
  }

  // Divide by 100 because reg value is a % and it needs to be normalised to 0-1
  float out_percent = modbus_server.combineHoldingRegisters(addr.modOutputOverrideHold);
  float out_bits = POWER_OUTPUT_BITS * out_percent/100;
  gpio.analogWrite(addr.outputPin, out_bits);
}

// Run a specified PID (A or B) then apply gradient, ASPC, new PID terms, etc.
void runPID(PIDEnum pid = PIDEnum::UNKNOWN)
{
  PIDController* PID = nullptr;
  PIDAddresses addr;

  // Identify which PID
  switch (pid)
  {
    case PIDEnum::A:
      PID = &PID_A;
      addr = pidA_addr;
      break;
    case PIDEnum::B:
      PID = &PID_B;
      addr = pidB_addr;
      break;
    default:
      Serial.println("Improper runPID call, no PID specified.");
      return;
  }

  if (PID != nullptr)
  {
    // Check PID enabled
    bool enabled = modbus_server.readBool(addr.modPidEnableCoil);
    int automatic = PID->myPID_.GetMode(); // Automatic is 1 (true), manual is false (0)

    // Setting PID mode. 'Automatic' is 'let PID adjust output', 'manual' is 'user chooses output'
    // Translates to: automatic=on, manual=off. If manual, PID.Compute() returns immediately.
    if (enabled && !automatic) // If turned on but not automatic
    {
      PID->myPID_.SetMode(AUTOMATIC);
    }
    else if (!enabled && automatic) // If turned off but still automatic
    {
      PID->myPID_.SetMode(MANUAL);
      PID->output = 0; // Override this to 0 while turned off
    }

    // Check PID tunings - do this even if PID is not enabled
    double newKp = double(modbus_server.combineHoldingRegisters(addr.modKpHold));
    double newKi = double(modbus_server.combineHoldingRegisters(addr.modKiHold));
    double newKd = double(modbus_server.combineHoldingRegisters(addr.modKdHold));
    PID->check_PID_tunings(newKp, newKi, newKd);

    // Setpoint and computation handling
    // The goal here is that the setPoint used in PID computation is always derived from the
    // baseSetPoint of the PID. the bSP is gotten from a register in taskComms when changed,
    // and the thermal gradient is a modifier, recalculated when the bSP is changed.

    // If gradient is enabled, take the base setpoint and add the modifier for this run
    if (modbus_server.readBool(MOD_GRADIENT_ENABLE_COIL))
    {
      PID->setPoint = PID->baseSetPoint + PID->gradientModifier;
    }
    else
    { // Otherwise, the setpoint for this run is just the base setpoint
      PID->setPoint = PID->baseSetPoint;
    }

    // Calculate PID output. When PID is not enabled, this won't do anything
    PID->run();

    // Power is now on a scale of 0->100 (acting as %)
    // The value output is still 0->4095 bits representing 0->10V
    // But we want to scale this down to 80% of the available range
    float out = POWER_OUTPUT_BITS * PID->output / PID_OUTPUT_LIMIT;
    out = out * power_output_scale;

    // Write PID output. When PID is not enabled, 
    modbus_server.floatToInputRegisters(addr.modPidOutputInp, PID->output);
    modbus_server.floatToInputRegisters(addr.modPidOutputSumInp, PID->myPID_.GetOutputSum());

    if (INVERT_OUTPUT_SIGNAL)
    {
      float inv_output = POWER_OUTPUT_BITS - out;
      gpio.analogWrite(addr.outputPin, inv_output);
    }
    else
    {
      gpio.analogWrite(addr.outputPin, out);
    }

    // Check auto set point control and modify the base setpoint if it and the PID is enabled
    if (enabled && modbus_server.readBool(MOD_AUTOSP_ENABLE_COIL))
    {
      // Only increase temperature if it would remain below or at the setpoint limit
      if (PID->baseSetPoint + PID->autospRate <= setpointLimit)
      {
        PID->baseSetPoint = PID->baseSetPoint + PID->autospRate;
      }
      else  // Otherwise turn it off
      {
        modbus_server.coilWrite(MOD_AUTOSP_ENABLE_COIL, 0);
        if (DEBUG)
        {
          Serial.println("Upper limit reached, disabling auto set point control.");
        }
      }
      
    }

    // Write the current setpoint to the register
    modbus_server.floatToHoldingRegisters(addr.modSetPointHold, PID->setPoint);
  }
}

// Take a BufferObject and populate it with PID attributes.
void fillPidBuffer(BufferObject& obj)
{
    obj.frame = counter;
    // PID_A calculations
    float error = PID_A.setPoint - PID_A.input;
    obj.temperature_upper = PID_A.input;
    obj.lastInput_upper = PID_A.myPID_.GetLastInput(); 
    obj.output_upper = PID_A.output;
    obj.outputSum_upper = PID_A.myPID_.GetOutputSum();
    obj.kp_upper = PID_A.myPID_.GetKp() * error;
    obj.ki_upper = PID_A.myPID_.GetKi() * error;
    obj.kd_upper = PID_A.myPID_.GetKd() * (PID_A.input - PID_A.myPID_.GetLastInput());
    obj.setpoint_upper = PID_A.setPoint;

    // PID_B calculations
    error = PID_B.setPoint - PID_B.input;
    obj.temperature_lower = PID_B.input;
    obj.lastInput_lower = PID_B.myPID_.GetLastInput();
    obj.output_lower = PID_B.output;
    obj.outputSum_lower = PID_B.myPID_.GetOutputSum();
    obj.kp_lower = PID_B.myPID_.GetKp() * error;
    obj.ki_lower = PID_B.myPID_.GetKi() * error;
    obj.kd_lower = PID_B.myPID_.GetKd() * (PID_B.input - PID_B.myPID_.GetLastInput());
    obj.setpoint_lower = PID_B.setPoint;
}