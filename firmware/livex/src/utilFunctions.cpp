#include "utilFunctions.h"

float combineHoldingRegisters(ModbusTCPServer& modbus_server, int address)
{ // See union ModbusFloat. Stich two ints into one float
  uint16_t A = modbus_server.holdingRegisterRead(address);
  uint16_t B = modbus_server.holdingRegisterRead(address+1);

  ModbusFloat modbusFloat;
  modbusFloat.registers.high = B; // little-endian
  modbusFloat.registers.low = A;
  return modbusFloat.value;
}