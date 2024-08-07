#include "modbusServerController.h"

ModbusServerController::ModbusServerController()
{
  // initialiseModbus();
}

void ModbusServerController::initialiseModbus()
{
  if (!begin())
  {
    Serial.println("Failed to start Modbus TCP Server!");
    while (1);
  }

  // Configure and intialise modbus coils/registers
  // Addresses follow Modbus convention for register type: 1, 30001, 40001.
  configureInputRegisters(TRIG_INPUT_START, TRIG_NUM_INP);
  configureHoldingRegisters(TRIG_FURNACE_INTVL_HOLD, TRIG_NUM_HOLD);
  configureCoils(TRIG_ENABLE_COIL, TRIG_NUM_COIL);

}

// Write a boolean (1 or 0) to a modbus coil.
// Return success (1) or failure (0)
int ModbusServerController::writeBool(int address, int value)
{
  return coilWrite(address, value);
}

// Read a boolean (1 or 0) from a modbus coil. Response
int ModbusServerController::readBool(int address)
{
  return coilRead(address);
}

// Write a float to a number (default 2) of modbus input registers. Return success code of write.
int ModbusServerController::floatToInputRegisters(int address, float value, int numRegisters)
{
  return writeInputRegisters
  (
    address, (uint16_t*)(&value), numRegisters
  );
}

// Write a float to a pair of modbus holding registers addresses. Returns success code of second write.
int ModbusServerController::floatToHoldingRegisters(int address, float value)
{
  ModbusFloat converter;
  converter.value = value;
  
  // Two writes, as there is no 'writeHoldingRegisters' function. Little-endian word order
  holdingRegisterWrite(address, converter.registers.low);
  return holdingRegisterWrite(address+1, converter.registers.high);
}

// See union ModbusFloat. Stich two ints into one float
float ModbusServerController::combineHoldingRegisters(int address)
{
  uint16_t A = holdingRegisterRead(address);
  uint16_t B = holdingRegisterRead(address+1);

  ModbusFloat modbusFloat;
  modbusFloat.registers.high = B; // little-endian
  modbusFloat.registers.low = A;
  return modbusFloat.value;
}
