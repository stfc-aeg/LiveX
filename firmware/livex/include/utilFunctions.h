#ifndef UTILFUNCTIONS_H
#define UTILFUNCTIONS_H

#include <ArduinoRS485.h>
#include <ArduinoModbus.h>
#include "modbusAddresses.h"

union ModbusFloat
{ // This union allows two 16-bit ints to be read back as a 32-bit float
  float value;
  struct 
  {
    uint16_t low;
    uint16_t high;
} registers;
};

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

float combineHoldingRegisters(ModbusTCPServer& modbus_server, int address);

int floatToHoldingRegisters(ModbusTCPServer& modbus_server, int address, float value);

#endif