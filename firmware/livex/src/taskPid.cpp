#include <taskPid.h>

// Full definitions below core task
// void thermalGradient();
// void autoSetPointControl();
void runPID(String pid);
void fillPidBuffer(BufferObject& obj);

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
      // Get thermocouple readings for input
      PID_A.input = mcp[0].readThermocouple(); // First thermocouple for A
      PID_B.input = mcp[1].readThermocouple(); // Second thermocouple for B

      // Get third thermocouple reading
      int reading_c = mcp[2].readThermocouple();
      modbus_server.floatToInputRegisters(MOD_THERMOCOUPLE_C_INP, reading_c);

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
      runPID(A);
      runPID(B);
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
    out = out * POWER_OUTPUT_SCALE;

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
      PID->baseSetPoint = PID->baseSetPoint + PID->autospRate;
    }

    // Write the current setpoint to the register
    modbus_server.floatToHoldingRegisters(addr.modSetPointHold, PID->setPoint);
  }
}

// Take a BufferObject and populate it with PID attributes.
void fillPidBuffer(BufferObject& obj)
{
    obj.counter = counter;
    // PID_A calculations
    float error = PID_A.setPoint - PID_A.input;
    obj.temperature_a = PID_A.input;
    obj.lastInput_a = PID_A.myPID_.GetLastInput(); 
    obj.output_a = PID_A.output;
    obj.outputSum_a = PID_A.myPID_.GetOutputSum();
    obj.kp_a = PID_A.myPID_.GetKp() * error;
    obj.ki_a = PID_A.myPID_.GetKi() * error;
    obj.kd_a = PID_A.myPID_.GetKd() * (PID_A.input - PID_A.myPID_.GetLastInput());
    obj.setpoint_a = PID_A.setPoint;

    // PID_B calculations
    error = PID_B.setPoint - PID_B.input;
    obj.temperature_b = PID_B.input;
    obj.lastInput_b = PID_B.myPID_.GetLastInput();
    obj.output_b = PID_B.output;
    obj.outputSum_b = PID_B.myPID_.GetOutputSum();
    obj.kp_b = PID_B.myPID_.GetKp() * error;
    obj.ki_b = PID_B.myPID_.GetKi() * error;
    obj.kd_b = PID_B.myPID_.GetKd() * (PID_B.input - PID_B.myPID_.GetLastInput());
    obj.setpoint_b = PID_B.setPoint;
}