#ifndef MODBUSUTILS_H
#define MODBUSUTILS_H

#include <Arduino.h>
#include <ArduinoModbus.h>

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

float combineHoldingRegisters(ModbusTCPServer* modbusServer, int address);

#endif