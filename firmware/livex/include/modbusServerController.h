#ifndef MODBUS_SERVER_CONTROLLER_H
#define MODBUS_SERVER_CONTROLLER_H

#include <ArduinoRS485.h>
#include <ArduinoModbus.h>
#include "config.h"
#include "utilFunctions.h"

class ModbusServerController : public ModbusTCPServer
{
  public:

    int numInputRegs = MOD_NUM_INP;
    int numHoldRegs  = MOD_NUM_HOLD;
    int numCoils     = MOD_NUM_COIL;

    ModbusTCPServer modbus_server_;

    ModbusServerController();
    void initialiseModbus();

    float combineHoldingRegisters(int address);

    int writeBool(int address, int value);
    int readBool(int address);
    int floatToInputRegisters(int address, float value, int numRegisters=2);
    int floatToHoldingRegisters(int address, float value);
};

#endif