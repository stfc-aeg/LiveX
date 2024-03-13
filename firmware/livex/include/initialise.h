#ifndef INITIALISE_H
#define INITIALISE_H

#include <Adafruit_I2CDevice.h>
#include <Adafruit_I2CRegister.h>
#include "Adafruit_MCP9600.h"
#include <Ethernet.h>
#include <ArduinoModbus.h>

#include "pidController.h"
#include "modbusServerController.h"
#include "config.h"
#include "resources.h"

void initialiseInterrupts(hw_timer_t** secondaryFlagTimer);

void initialiseThermocouples(Adafruit_MCP9600* mcp, int num_mcp, const uint8_t* mcp_addr);

void initialiseEthernet(EthernetServer ethServer, byte* mac, byte* ip, int ethPin);

void writePIDDefaults(ModbusServerController& modbus_server, PIDController PID);

#endif