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
    // this section should be out of the PID control but implementation is unclear
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
            modbus_server_.holdingRegisterWrite(tempAddress+i, elems[i]);
        }
        tempAddress += 2;
    }

    // PID mode
    myPID_.SetMode(AUTOMATIC);
}

void PIDController::run()
{
    myPID_.Compute();
    // PID output is scale of 0-255. ESP3258PLC has 12-bit output
    output = output * outputMultiplier;
}

 // Check if PID terms in registers are different, and set them accordingly
void PIDController::check_PID_tunings(double newKp, double newKi, double newKd)
{
    if ((newKp != Kp) || (newKi != Ki) || (newKd != Kd)) 
    {
      myPID_.SetTunings(newKp, newKi, newKd);
      Kp = newKp;
      Ki = newKi;
      Kd = newKd;
    }
}
