#include "pidController.h"

// Eventually, output pin will be provided in PIDAddresses struct
#define PWM_PIN_A 0x400d // A0_5 

 // Set internal default values on creation.
PIDController::PIDController(PIDAddresses addr) : myPID_(&input, &output, &setPoint, Kp, Ki, Kd, DIRECT)
{
    // Best written as floats for modbus, but PID class requires doubles.
    setPoint = 25.5;
    baseSetPoint = 25.5;
    Kp = 25.5;
    Ki = 5.0;
    Kd = 0.1;
    addr_ = addr;
}

// Provide controller with thermocouple, modbus, gpio, and write defaults
void PIDController::initialise(ModbusTCPServer& modbus_server, ExpandedGpio& gpio)
{
    modbus_server_ = modbus_server;
    gpio_ = gpio;

    // Write variables to modbus
    // PID requires doubles, modbus works best with floats, so cast
    float pidDefaults_[4] =
    {
        static_cast<float>(setPoint),
        static_cast<float>(Kp),
        static_cast<float>(Ki),
        static_cast<float>(Kd)
    }; 
    int tempAddress = addr_.modSetPointHold;

    // Separate values as only one holding register can be written to at a time
    for (float term : pidDefaults_)
    {
        uint16_t* elems = (uint16_t*)&term;
        for (int i = 0; i<2; i++)
        {
            modbus_server.holdingRegisterWrite(tempAddress+i, elems[i]);
        }
        tempAddress += 2;
    }
}

// Check if the enable coil for this controller is true (1) or false (0)
bool PIDController::check_PID_enabled()
{
    return modbus_server_.coilRead(addr_.modPidEnableCoil);
}

// Get input and setpoint, do PID computation, and save output to a register
void PIDController::do_PID(double reading)
{
    // Get enable checks
    bool gradientEnabled = modbus_server_.coilRead(MOD_GRADIENT_ENABLE_COIL);
    bool autospEnabled = modbus_server_.coilRead(MOD_AUTOSP_ENABLE_COIL);

    input = reading;

    // Setpoint handling
    setPoint = combineHoldingRegisters(modbus_server_, addr_.modSetPointHold);

    // Override with gradient setpoint if enabled
    if (gradientEnabled)
    {
        setPoint = gradientSetPoint;
    }

    // Output calculation and processing
    myPID_.Compute();

    // output = 255 - output;
    output = output * outputMultiplier; // PID library output is on a scale of 0-255. Scale to 4095

    gpio_.analogWrite(addr_.outputPin, output);

    // Write relevant outputs
    // For consistency and ease of read/write, floats are preferable to doubles
    float thermoReading = static_cast<float>(input);

    // Write input reading to input registers
    int ret = modbus_server_.writeInputRegisters(
        addr_.modThermocoupleInp, (uint16_t*)(&thermoReading), 2
    );

    float pidOutput = output;
    // Write PID output to input registers
    modbus_server_.writeInputRegisters(
        addr_.modPidOutputInp, (uint16_t*)(&pidOutput), 2
    );

    // Increase setpoint if ASPC is enabled
    if (autospEnabled)
    {
        floatToHoldingRegisters(modbus_server_, addr_.modSetPointHold, (setPoint+autospRate));
    }
}

 // Check if PID terms in registers are different, and set them accordingly
void PIDController::check_PID_tunings()
{
    double newKp = double(combineHoldingRegisters(modbus_server_,addr_.modKpHold));
    double newKi = double(combineHoldingRegisters(modbus_server_,addr_.modKiHold));
    double newKd = double(combineHoldingRegisters(modbus_server_,addr_.modKdHold));

    if ((newKp != Kp) || (newKi != Ki) || (newKd != Kd)) 
    {
      myPID_.SetTunings(newKp, newKi, newKd);
      Kp = newKp;
      Ki = newKi;
      Kd = newKd;
    }
}

// Check PID tunings and run PID computation. Return current time
void PIDController::run(double reading)
{
    enabled = check_PID_enabled();
    if (enabled)
    {
      check_PID_tunings();
      do_PID(reading);
    }
    else
    {
      gpio_.analogWrite(addr_.outputPin, 0);
    }
}
