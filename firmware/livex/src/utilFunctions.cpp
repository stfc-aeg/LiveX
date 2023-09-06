#include "utilFunctions.h"

// See union ModbusFloat. Stich two ints into one float
float combineHoldingRegisters(ModbusTCPServer& modbus_server, int address)
{
  uint16_t A = modbus_server.holdingRegisterRead(address);
  uint16_t B = modbus_server.holdingRegisterRead(address+1);

  ModbusFloat modbusFloat;
  modbusFloat.registers.high = B; // little-endian
  modbusFloat.registers.low = A;
  return modbusFloat.value;
}

 // Write a float to a pair of modbus addresses. Returns success code of second write.
int floatToHoldingRegisters(ModbusTCPServer& modbus_server, int address, float value)
{
  ModbusFloat converter;
  converter.value = value;
  
  // Two writes, as there is no 'writeHoldingRegisters' function. Little-endian word order
  modbus_server.holdingRegisterWrite(address, converter.registers.low);
  return modbus_server.holdingRegisterWrite(address+1, converter.registers.high);
}