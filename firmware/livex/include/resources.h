// For resources that need to be shared across multiple files and tasks.
// This enables those tasks to be separated into their own files, making the code more readable.

#ifndef RESOURCES_H
#define RESOURCES_H

#include <Ethernet.h>
#include <SPI.h>
#include <WiFi.h>
#include <ArduinoRS485.h>
#include <ArduinoModbus.h>
#include <cmath>
#include <esp32-hal-timer.h>
#include <driver/timer.h>

#include <ExpandedGpio.h>
#include "pins_is.h"
#include "initialise.h"
#include "config.h"
#include "pidController.h"
#include "modbusServerController.h"
#include "buffer.h"

#include <Adafruit_I2CDevice.h>
#include <Adafruit_I2CRegister.h>
#include "Adafruit_MCP9600.h"
#include <PID_v1.h>

// Key objects - used in main, taskPid and taskComms
extern EthernetServer modbusEthServer;
extern EthernetServer tcpEthServer;
extern ModbusServerController modbus_server;
extern FifoBuffer<BufferObject> buffer;
extern ExpandedGpio gpio; // not used in comms

// Eth clients - main and taskComms
extern EthernetClient modbusClient;
extern EthernetClient streamClient;
extern long int connectionTimer;  // Timeout

// Acquisition details - main, taskPid
extern float counter;
extern bool acquiringFlag;

// PID - main and taskPid
extern PIDAddresses pidA_addr;
extern PIDAddresses pidB_addr;
extern PIDController PID_A;
extern PIDController PID_B;

// MCP9600 - main, taskPid
extern Adafruit_MCP9600 mcp[];
extern const unsigned int num_mcp;
extern const uint8_t mcp_addr[];

// Timers - main, initialise
extern hw_timer_t *secondaryFlagTimer;
// Timer flags - main, taskPid
extern volatile bool pidFlag;
extern volatile bool secondaryFlag;

// may not be needed as used for debugging
extern volatile int interruptCounter;

// Core task definition for pinning in main
extern void Core0PIDTask(void * pvParameters);

// temporary measurements of timer consistency
// volatile long int timerTimer = micros();
// float timerTimerAvg = 0;
// volatile long int timerCounter = 0;
// volatile long int prev = 0;

// Interrupt functions - main, initialise
extern void IRAM_ATTR pidInterrupt();
extern void IRAM_ATTR secondaryFlagOnTimer();

#endif