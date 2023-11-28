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
    bool enabled = true;
    float outputMultiplier = 16.0588; // 4095/255, 12-bit but PID does 0-255
    long int tWrite; // Time of reading
    float gradientSetPoint = 0;
    float autospRate = 0;

    PID myPID_;
    Adafruit_MCP9600 mcp_;
    ModbusTCPServer modbus_server_;
    ExpandedGpio gpio_;
    PIDAddresses addr_;

    PIDController(PIDAddresses addr);
    void initialise(ModbusTCPServer& modbus_server, ExpandedGpio& gpio);

    void run();
    void check_PID_tunings(double newKp, double newKi, double newKd);
};

#endif