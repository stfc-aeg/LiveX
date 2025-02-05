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
};


class PIDController
{
  public:
    double setPoint, input, output;
    double Kp, Ki, Kd;
    double baseSetPoint;
    float gradientModifier = 0;
    float autospRate = 0;

    PID myPID_;
    PIDAddresses addr_;

    PIDController(PIDAddresses addr);
    void run();
    void check_PID_tunings(double newKp, double newKi, double newKd);
};

#endif