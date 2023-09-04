#include <Ethernet.h>
#include <SPI.h>
#include <WiFi.h>
#include <ArduinoRS485.h>
#include <ArduinoModbus.h>
#include <cmath>

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

#define PWM_PIN_A A0_5
#define PWM_PIN_B A0_6 // Hypothetical second heater output pin

static bool eth_connected = false;

EthernetServer ethServer(502);
ModbusTCPServer modbus_server;
ExpandedGpio gpio;

// Addresses for PID objects
PIDAddresses pidA_addr = {
  PWM_PIN_A,
  MOD_SETPOINT_A_HOLD,
  MOD_PID_OUTPUT_A_INP,
  MOD_PID_ENABLE_A_COIL,
  MOD_THERMOCOUPLE_A_INP,
  MOD_KP_A_HOLD,
  MOD_KI_A_HOLD,
  MOD_KD_A_HOLD
};

PIDAddresses pidB_addr = {
  PWM_PIN_B,
  MOD_SETPOINT_B_HOLD,
  MOD_PID_OUTPUT_B_INP,
  MOD_PID_ENABLE_B_COIL,
  MOD_THERMOCOUPLE_B_INP,
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

int numHoldRegs = 32;
int numInputRegs = 32;
int numCoils = 8;

// Timers setup
float counter = 0;
long int tPID = millis(); // Timer for PID
long int tGradient = millis(); // Timer for gradient update
long int tAutosp = millis(); // Auto set point control
// Interval/period for each control
long int intervalPID = 1000;
long int intervalGradient = 1000;
long int intervalAutosp = 1000;

// MCP9600 setup
Adafruit_MCP9600 mcp[] = {Adafruit_MCP9600(), Adafruit_MCP9600()};
const unsigned int num_mcp = sizeof(mcp) / sizeof(mcp[0]);
const uint8_t mcp_addr[] = {0x60, 0x67};

long int tRead = millis(); // Timer for thermocouple reading
float thermoReadings[2] = { 1, 1 };
int num_thermoReadings = sizeof(thermoReadings) / sizeof(thermoReadings[0]);

// Functions for reference later
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

  // pidController.cpp
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
    MOD_THERMOCOUPLE_C_INP, (uint16_t*)(&thermoReadings), 4
  ); // Written to thermocouple_C, overlapping into D

  // Write counter
  modbus_server.writeInputRegisters(
    MOD_COUNTER_INP, (uint16_t*)(&counter), 2
  );
  counter++;
  Serial.println(counter);
  return millis();
}

long int thermalGradient()
{
  // Get temperature (K) per mm
  float wanted = combineHoldingRegisters(modbus_server, MOD_GRADIENT_WANTED_HOLD);
  // Get distance (mm)
  float distance = combineHoldingRegisters(modbus_server, MOD_GRADIENT_DISTANCE_HOLD);
  // Theoretical temperature gradient (k/mm * mm = k)
  float theoretical = wanted * distance;

  // Apply values
  float gradientModifier = theoretical/2;
  PID_A.gradientModifier = gradientModifier;
  PID_B.gradientModifier = -gradientModifier;

  // Calculation of actual difference between heaters
  float actual = fabs(PID_A.input - PID_B.input);

  // Write relevant values to modbus
  modbus_server.writeInputRegisters(MOD_GRADIENT_THEORY_INP, (uint16_t*)(&theoretical), 2);
  modbus_server.writeInputRegisters(MOD_GRADIENT_ACTUAL_INP, (uint16_t*)(&actual), 2);
  modbus_server.writeInputRegisters(MOD_GRADIENT_MODIFIER_INP, (uint16_t*)(&gradientModifier), 2);

  return millis();
}

long int autoSetPointControl()
{ // Increment setPoint by an average rate per second

  // Get rate
  float rate = combineHoldingRegisters(modbus_server, MOD_AUTOSP_RATE_HOLD);

  // Heating (1) or cooling (0)?
  bool heating = modbus_server.coilRead(MOD_AUTOSP_HEATING_COIL);

  if (!heating)
  { 
    // Rate should be a positive value with 'direction' determined by heating option
    rate = -rate;
  }

  // Rate is average K/s, but value depends on PID interval
  rate = rate * (intervalPID/1000); // e.g.: 0.5 * 20/1000 = 0.01 = 50 times per second
  PID_A.autospRate = rate;
  PID_B.autospRate = rate;

  // Get img per degree
  float imgPerDegree = combineHoldingRegisters(modbus_server, MOD_AUTOSP_IMGDEGREE_HOLD);

  // Calculate midpoint. Fabs in case B is higher temp
  float midpoint = fabs((PID_A.input + PID_B.input) / 2);
  modbus_server.writeInputRegisters(MOD_AUTOSP_MIDPT_INP, (uint16_t*)(&midpoint), 2);

  return millis();
}

void loop()
{ // Client connections handled on core 1 (loop)

  // Listen for incoming clients
  EthernetClient client = ethServer.available();

  if (client)
  {
    Serial.println("New client");
    modbus_server.accept(client);

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
{ // Core 0 task to handle device control
  Serial.print("Task 2 running on core ");
  Serial.println(xPortGetCoreID());
  delay(1000);

  for(;;)
  {
    // Run control after its specified interval
    if ( (millis()-tRead) >= 1000 )
    {
      tRead = readThermoCouples();
    }

    if ( (millis() - tGradient) >= intervalGradient)
    {
      tGradient = thermalGradient();
    }

    if ( (millis() - tAutosp) >= intervalAutosp)
    {
      tAutosp = autoSetPointControl();
    }

    if ( (millis() - tPID) >= intervalPID ) 
    {
      PID_A.run();
      PID_B.run();
      tPID = millis(); // Only need one timer, PIDs have same period
      Serial.println("");
    }
  }
}
