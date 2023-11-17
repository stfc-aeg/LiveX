#ifndef INITIALISE_H
#define INITIALISE_H

#include <Adafruit_I2CDevice.h>
#include <Adafruit_I2CRegister.h>
#include "Adafruit_MCP9600.h"

#include <Ethernet.h>

#include <ArduinoModbus.h>

#include "config.h"

void initialiseThermocouples(Adafruit_MCP9600* mcp, int num_mcp, const uint8_t* mcp_addr);

void initialiseEthernet(EthernetServer ethServer, byte* mac, byte* ip, int ethPin);

void initialiseModbus(ModbusTCPServer& modbus_server, int numInputRegs, int numHoldRegs, int numCoils);

#endif