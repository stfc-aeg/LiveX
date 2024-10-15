#include "pidController.h"

 // Set internal default values on creation.
PIDController::PIDController(PIDAddresses addr) : myPID_(&input, &output, &setPoint, Kp, Ki, Kd, DIRECT)
{
    // Best written as floats for modbus, but PID class requires doubles.
    setPoint = PID_SETPOINT_DEFAULT;
    baseSetPoint = PID_SETPOINT_DEFAULT;
    Kp = PID_KP_DEFAULT;
    Ki = PID_KI_DEFAULT;
    Kd = PID_KD_DEFAULT;
    addr_ = addr;

    // Set PID output range to match ESP3258PLC PWM
    myPID_.SetOutputLimits(0, PID_OUTPUT_LIMIT);

    myPID_.SetSampleTime(100);

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
