#ifndef PIDCONTROLLER_H
#define PIDCONTROLLER_H

#include "modbusAddresses.h"
#include <PID_v1.h>
#include "Adafruit_MCP9600.h"
#include <ArduinoRS485.h>
#include <ArduinoModbus.h>
#include <ExpandedGpio.h>
#include "utilFunctions.h"

class PIDController 
{
  public:
    double setPoint, input, output;
    double Kp, Ki, Kd;
    double baseSetPoint;
    bool enabled = true;
    float outputMultiplier = 16.0588; // 4095/255, 12-bit but PID does 0-255
    long int tWrite; // Time of reading
    double gradientModifier = 0;

    PID myPID_;
    Adafruit_MCP9600 mcp_;
    ModbusTCPServer modbus_server_;
    ExpandedGpio gpio_;
    PIDAddresses addr_;

    PIDController(PIDAddresses addr);

    void initialise(Adafruit_MCP9600& mcp, ModbusTCPServer& modbus_server, ExpandedGpio& gpio);

    void run();
    void do_PID();
    void check_PID_tunings();
    bool check_PID_enabled();
};

#endif