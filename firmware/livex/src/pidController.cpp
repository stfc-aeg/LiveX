#include "pidController.h"

// Eventually, output pin will be provided in PIDAddresses struct
#define PWM_PIN_A 0x400d // A0_5 

 // Set internal default values on creation.
PIDController::PIDController(PIDAddresses addr) : myPID_(&input, &output, &setPoint, Kp, Ki, Kd, DIRECT)
{
    setPoint = 25.5;
    Kp = 25.5;
    Ki = 5.0;
    Kd = 0.1;
    addr_ = addr;
    // Best written as floats for modbus, but PID class requires doubles.
}

// Provide controller with thermocouple, modbus, gpio, and write defaults
void PIDController::initialise(Adafruit_MCP9600& mcp, ModbusTCPServer& modbus_server, ExpandedGpio& gpio)
{
    modbus_server_ = modbus_server;
    mcp_ = mcp;
    gpio_ = gpio;

    // Write variables to modbus.
    float pidDefaults_[4] =
    {
        static_cast<float>(setPoint),
        static_cast<float>(Kp),
        static_cast<float>(Ki),
        static_cast<float>(Kd)
    }; // PID requires doubles, modbus works best with floats, so cast
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
long int PIDController::do_PID()
{
    input = mcp_.readThermocouple();
    setPoint = combineHoldingRegisters(modbus_server_, addr_.modSetPointHold);

    myPID_.Compute();
    // Circuitry needs reversed output. Could use native PID library reverse
    // Output is on a scale of 0-255, hence 255-output
    output = 255 - output;
    output = output * outputMultiplier; // Scale up to 4095

    Serial.print("Output value: ");
    Serial.println(output);

    gpio_.analogWrite(PWM_PIN_A, output); // Expanded pin, use custom library

    // Easier to write to/read from register with float than double. consistency
    float pidOutput = output;
    modbus_server_.writeInputRegisters(
        addr_.modPidOutputInp, (uint16_t*)(&pidOutput), 2
    );
    return millis(); // Time since last reading
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
long int PIDController::run()
{
    check_PID_tunings();
    return do_PID();
}
