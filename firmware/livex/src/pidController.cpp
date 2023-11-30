#include "pidController.h"

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

    // Set PID output range to match ESP3258PLC PWM
    myPID_.SetOutputLimits(0, 4095);

    // PID mode
    myPID_.SetMode(AUTOMATIC);
}

void PIDController::run()
{
    myPID_.Compute();
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
