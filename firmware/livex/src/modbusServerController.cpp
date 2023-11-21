#include "modbusServerController.h"

ModbusServerController::ModbusServerController() : ModbusTCPServer()
{
  initialiseModbus();
}

void ModbusServerController::initialiseModbus()
{
  if (!modbus_server_.begin()) 
  {
    Serial.println("Failed to start Modbus TCP Server!");
    while (1);
  }

  // Configure and intialise modbus coils/registers
  // Addresses follow Modbus convention for register type: 1, 30001, 40001.
  modbus_server_.configureInputRegisters(MOD_COUNTER_INP, numInputRegs);
  modbus_server_.configureHoldingRegisters(MOD_SETPOINT_A_HOLD, numHoldRegs);
  modbus_server_.configureCoils(MOD_PID_ENABLE_A_COIL, numCoils);

  // Default enable values for each control
  modbus_server_.coilWrite(MOD_PID_ENABLE_A_COIL, 0);
  modbus_server_.coilWrite(MOD_PID_ENABLE_B_COIL, 0);

  modbus_server_.coilWrite(MOD_GRADIENT_ENABLE_COIL, 0);
  modbus_server_.coilWrite(MOD_AUTOSP_ENABLE_COIL, 0);
  modbus_server_.coilWrite(MOD_AUTOSP_HEATING_COIL, 1);

  modbus_server_.coilWrite(MOD_GRADIENT_HIGH_COIL, 0);
}

// Write a boolean (1 or 0) to a modbus coil.
// Return success (1) or failure (0)
int ModbusServerController::writeBool(int address, int value)
{
  return modbus_server_.coilWrite(address, value);
}

// Read a boolean (1 or 0) from a modbus coil. Response
int ModbusServerController::readBool(int address)
{
  return modbus_server_.coilRead(address);
}

// Write a float to a number (default 2) of modbus input registers. Return success code of write.
int ModbusServerController::floatToInputRegisters(int address, float value, int numRegisters)
{
  return modbus_server_.writeInputRegisters
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
  modbus_server_.holdingRegisterWrite(address, converter.registers.low);
  return modbus_server_.holdingRegisterWrite(address+1, converter.registers.high);
}

// See union ModbusFloat. Stich two ints into one float
float ModbusServerController::combineHoldingRegisters(int address)
{
  uint16_t A = modbus_server_.holdingRegisterRead(address);
  uint16_t B = modbus_server_.holdingRegisterRead(address+1);

  ModbusFloat modbusFloat;
  modbusFloat.registers.high = B; // little-endian
  modbusFloat.registers.low = A;
  return modbusFloat.value;
}
