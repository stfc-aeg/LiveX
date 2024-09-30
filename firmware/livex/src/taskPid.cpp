#include <taskPid.h>

// Full definitions below core task
// void thermalGradient();
// void autoSetPointControl();
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
      modbus_server.floatToInputRegisters(addr.modPidOutputInp, 0);
    }
  }
  else
  {
    gpio.analogWrite(addr.outputPin, 0);
    modbus_server.floatToInputRegisters(addr.modPidOutputInp, 0);
  }
}
