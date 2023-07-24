#include <Ethernet.h>
#include <SPI.h>
#include <WiFi.h>
#include <ArduinoRS485.h>
#include <ArduinoModbus.h>

#include <ExpandedGpio.h>
#include "pins_is.h"
#include "initialise.h"
#include "modbusAddresses.h"
#include "pidController.h"
#include "utilFunctions.h"

#include <Adafruit_I2CDevice.h>
#include <Adafruit_I2CRegister.h>
#include "Adafruit_MCP9600.h"
#include <PID_v1.h>

#define PWM_PIN_A 0x400d // A0_5
#define PWM_PIN_B 0x4006 // A0_6 // Hypothetical second heater output pin

static bool eth_connected = false;

EthernetServer ethServer(502);
ModbusTCPServer modbus_server;
ExpandedGpio gpio;

PIDAddresses pidA_addr = {
  PWM_PIN_A,
  MOD_SETPOINT_A_HOLD,
  MOD_PID_OUTPUT_A_INP,
  MOD_PID_ENABLE_A_COIL,
  MOD_THERMOCOUPLE_A,
  MOD_KP_A_HOLD,
  MOD_KI_A_HOLD,
  MOD_KD_A_HOLD
};

PIDAddresses pidB_addr = {
  PWM_PIN_B,
  MOD_SETPOINT_B_HOLD,
  MOD_PID_OUTPUT_B_INP,
  MOD_PID_ENABLE_B_COIL,
  MOD_THERMOCOUPLE_B,
  MOD_KP_B_HOLD,
  MOD_KI_B_HOLD,
  MOD_KD_B_HOLD
};

PIDController PID_A(pidA_addr);
PIDController PID_B(pidB_addr);

byte mac[] = { 0x10, 0x97, 0xbd, 0xca, 0xea, 0x14 };
byte ip[] = { 192, 168, 0, 159 };
byte gateway[] = { 192, 168, 0, 1 };
byte subnet[] = { 255, 255, 255, 0 };

int numHoldRegs = 16;
int numInputRegs = 16;
int numCoils = 2;

// PID and Counter setup
float counter = 0;
long int tWriteA = millis(); // Timer for write
long int tWriteB = millis();
// Output multiplier as 4095/255 does not work. This is close enough for now.

// MCP9600 setup
Adafruit_MCP9600 mcp[] = {Adafruit_MCP9600(), Adafruit_MCP9600()};
const unsigned int num_mcp = sizeof(mcp) / sizeof(mcp[0]);
const uint8_t mcp_addr[] = {0x60, 0x67};

long int tRead = millis(); // Timer for thermocouple reading
float thermoReadings[2] = { 1, 1 };
int num_thermoReadings = sizeof(thermoReadings) / sizeof(thermoReadings[0]);

// Functions for reference later
void update_state(void);
void Core0PIDTask(void * pvParameters);

void setup()
{
  Serial.begin(9600);
  delay(2000); // Serial requires a moment to be ready

  // I2C initialisation to ensure it is established before I2C calls made
  Wire.begin();

  // initialise.cpp
  initialiseEthernet(ethServer, mac, ip, PIN_SPI_SS_ETHERNET_LIB);
  initialiseThermocouples(mcp, num_mcp, mcp_addr);
  initialiseModbus(modbus_server, numInputRegs, numHoldRegs, numCoils);

  gpio.init();
  gpio.pinMode(0x400b, OUTPUT); // PIN_Q0_0
  gpio.pinMode(0x400a, OUTPUT); // PIN_Q0_1
  gpio.pinMode(0x400d, OUTPUT); // required?

  xTaskCreatePinnedToCore(
    Core0PIDTask,  /* Task function */
    "PIDTask",    /* Name of task  */
    10000,       /* Stack size    */
    NULL,       /* Parameter     */
    2,         /* Priority      */
    NULL,     /* Handle        */
    0        /* Pin to core 1 */
  );

  PID_A.initialise(mcp[0], modbus_server, gpio);
  PID_B.initialise(mcp[1], modbus_server, gpio);

  // PID mode
  PID_A.myPID_.SetMode(AUTOMATIC);
  PID_B.myPID_.SetMode(AUTOMATIC);
}

long int readThermoCouples()
{
  // Read hot junction from each mcp
  for (int idx = 0; idx < num_mcp; idx++)
  {
    thermoReadings[idx] = mcp[idx].readThermocouple();
    Serial.print((String)"Thermocouple reading (" + idx + "): ");
    Serial.println(thermoReadings[idx]);
  }
  // Write both readings
  modbus_server.writeInputRegisters(
    MOD_THERMOCOUPLE_C, (uint16_t*)(&thermoReadings), 4
  ); // Written to thermocouple_C, overlapping into D
  // Write counter
  modbus_server.writeInputRegisters(
    MOD_COUNTER_INP, (uint16_t*)(&counter), 2
  );
  counter++;
  Serial.println(counter);
  return millis();
}

void loop()
{
  // Client connections handled on core 1 (loop)
  // With pinned tasks, sets off watchdog or core dumps with unhandled exception consistently
  // Desirable to explicitly run this via pinned task but unreliable

  // Listen for incoming clients
  EthernetClient client = ethServer.available();

  if (client)
  {
    Serial.println("New client");
    modbus_server.accept(client);

    // `while` structure is not preferable but okay as it has its own core which does not
    // require other activity. Other options could be considered.
    while (client.connected())
    {
      // Serial.print(".");
      // Poll for requests while client is connected
      int ret = modbus_server.poll();
      if (ret) {
        // Nothing needed here right now.
      }
    }
    Serial.println("Client disconnected");
  }
}

void Core0PIDTask(void * pvParameters)
{
  // Core 0 task to handle PID looping
  // Currently deals with one PID control
  Serial.print("Task 2 running on core ");
  Serial.println(xPortGetCoreID());
  delay(1000);

  for(;;)
  {
    // Read thermocouples if 1000ms have elapsed
    if ( (millis()-tRead) >= 1000 ) 
    {
      tRead = readThermoCouples();
    }

    // Run if enabled, period 1000ms. If not
    if ( (millis() - tWriteA) >= 1000 ) 
    {
      PID_A.enabled = PID_A.check_PID_enabled();

      if (PID_A.enabled == true)
      { // Right now these are timed together
        // Plan for how each device is run should be considered.
        tWriteA = PID_A.run();
        tWriteB = PID_B.run();
      }
      else 
      { // If no PID enabled, write max output (reversed, 0).
        gpio.analogWrite(PWM_PIN_A, 4095);
        tWriteA = millis(); 
      }
      Serial.println("");
    }
  }
}
