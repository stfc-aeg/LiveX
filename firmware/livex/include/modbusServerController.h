#ifndef MODBUS_SERVER_CONTROLLER_H
#define MODBUS_SERVER_CONTROLLER_H

#include <ArduinoRS485.h>
#include <ArduinoModbus.h>
#include "config.h"

class ModbusServerController : public ModbusTCPServer
{
  public:

    int numInputRegs = MOD_NUM_INP;
    int numHoldRegs  = MOD_NUM_HOLD;
    int numCoils     = MOD_NUM_COIL;

    ModbusServerController();
    void initialiseModbus();

    float combineHoldingRegisters(int address);
    float combineInputRegisters(int address);

    int writeBool(int address, int value);
    int readBool(int address);
    int floatToInputRegisters(int address, float value, int numRegisters=2);
    int floatToHoldingRegisters(int address, float value);
};

// Necessary structure for easy Modbus reading
union ModbusFloat
{ // This union allows two 16-bit ints to be read back as a 32-bit float
  float value;
  struct 
  {
    uint16_t low;
    uint16_t high;
} registers;
};

union FloatSplit
{
  float value;
  uint16_t parts[2];
};

#endif