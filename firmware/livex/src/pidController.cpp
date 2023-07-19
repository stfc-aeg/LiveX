#include "pidController.h"

// just for now
#define PWM_PIN_A 0x400d // A0_5 

PIDController::PIDController(PIDAddresses addr) : myPID_(&input, &output, &setPoint, Kp, Ki, Kd, DIRECT)
{ // set default values on creation
    setPoint = 100;
    Kp = 25;
    Ki = 5;
    Kd = 0;
    addr_ = addr;
}

// pass it over all the things it needs
void PIDController::initialise(Adafruit_MCP9600& mcp, ModbusTCPServer& modbus_server, ExpandedGpio& gpio)
{
    modbus_server_ = modbus_server;
    mcp_ = mcp;
    gpio_ = gpio;
}

long int PIDController::do_PID()
{
    input = mcp_.readThermocouple();
    // Get setPointA here in case it has changed
    setPoint = combineHoldingRegisters(modbus_server_, addr_.modSetPointHold);
    myPID_.Compute();
    // Circuitry needs reversed output. Could use native PID library reverse
    // Output is on a scale of 0-255, hence 255-output
    output = 255 - output;
    output = output * outputMultiplier;
    // output = output * outputMultiplier; // Scale up to 4095
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

// bool PIDController::run()
// {
//     // do the enable check internally. why not. neat
// }

void PIDController::check_PID_tunings()
{ // Check if any are different, and set them if so
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

bool PIDController::check_PID_enabled()
{ // If value = 0, false
    return modbus_server_.coilRead(addr_.modPidEnableCoil);
}
