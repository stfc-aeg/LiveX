#ifndef PIDCONTROLLER_H
#define PIDCONTROLLER_H

#include "config.h"
#include <PID_v1.h>
#include "Adafruit_MCP9600.h"
#include <ArduinoRS485.h>
#include <ArduinoModbus.h>
#include <ExpandedGpio.h>
// #include "modbusServerController.h"

// Addresses utilised by a PIDController
struct PIDAddresses
{
  int outputPin;
  int modSetPointHold;
  int modPidOutputInp;
  int modPidOutputSumInp;
  int modPidEnableCoil;
  int modThermocoupleInp;
  int modKpHold;
  int modKiHold;
  int modKdHold;
  int modOutputOverrideHold;
  int modOutputScaleHold;
};


class PIDController
{
  public:
    double setPoint, input, output;
    double Kp, Ki, Kd;
    double baseSetPoint;
    float gradientModifier = 0;
    float autospRate = 0;
    float power_output_scale;

    PID myPID_;
    PIDAddresses addr_;

    PIDController(PIDAddresses addr);
    void run();
    void check_PID_tunings(double newKp, double newKi, double newKd);
    void check_output_scale(float new_scale);
};

#endif