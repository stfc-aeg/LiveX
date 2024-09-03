#include <modbusUtils.h>

// See union ModbusFloat. Stich two ints into one float
float combineHoldingRegisters(ModbusTCPServer* modbusServer, int address)
{
  uint16_t A = modbusServer->holdingRegisterRead(address);
  uint16_t B = modbusServer->holdingRegisterRead(address+1);

  ModbusFloat modbusFloat;
  modbusFloat.registers.high = B; // little-endian
  modbusFloat.registers.low = A;
  return modbusFloat.value;
}
