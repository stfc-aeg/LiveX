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
  configureInputRegisters(MOD_COUNTER_INP, MOD_NUM_INP);
  configureHoldingRegisters(MOD_SETPOINT_A_HOLD, MOD_NUM_HOLD);
  configureCoils(MOD_PID_ENABLE_A_COIL, MOD_NUM_COIL);

  // Default enable values for each control
  coilWrite(MOD_PID_ENABLE_A_COIL, 0);
  coilWrite(MOD_PID_ENABLE_B_COIL, 0);

  coilWrite(MOD_GRADIENT_ENABLE_COIL, 0);
  coilWrite(MOD_GRADIENT_HIGH_COIL, 0);

  coilWrite(MOD_AUTOSP_ENABLE_COIL, 0);
  coilWrite(MOD_AUTOSP_HEATING_COIL, 1);

  coilWrite(MOD_MOTOR_ENABLE_COIL, 0);
  coilWrite(MOD_MOTOR_DIRECTION_COIL, 1);

  coilWrite(MOD_ACQUISITION_COIL, 0);
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

// See union ModbusFloat. Stitch two ints from holding registers into one float
float ModbusServerController::combineHoldingRegisters(int address)
{
  uint16_t A = holdingRegisterRead(address);
  uint16_t B = holdingRegisterRead(address+1);

  ModbusFloat modbusFloat;
  modbusFloat.registers.high = B; // little-endian
  modbusFloat.registers.low = A;
  return modbusFloat.value;
}

// See unionModbusFloat. Stitch two ints from input registers into one float
float ModbusServerController::combineInputRegisters(int address)
{
  uint16_t A = inputRegisterRead(address);
  uint16_t B = inputRegisterRead(address+1);

  ModbusFloat modbusFloat;
  modbusFloat.registers.high = B; // little-endian
  modbusFloat.registers.low = A;
  return modbusFloat.value;
}
