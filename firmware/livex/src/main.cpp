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
long int connectionTimer;
long int connectionTimeout = 30000;

// MCP9600 setup
Adafruit_MCP9600 mcp[] = {Adafruit_MCP9600(), Adafruit_MCP9600()};
const unsigned int num_mcp = sizeof(mcp) / sizeof(mcp[0]);
const uint8_t mcp_addr[] = {0x60, 0x67};

long int tRead = millis(); // Timer for thermocouple reading
float thermoReadings[2] = { 1, 1 };
int num_thermoReadings = sizeof(thermoReadings) / sizeof(thermoReadings[0]);

// Functions for reference later
void Core0PIDTask(void * pvParameters);

// Initialise wires, devices, and Modbus/gpio
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
  gpio.pinMode(Q0_0, OUTPUT); // PIN_Q0_0
  gpio.pinMode(Q0_1, OUTPUT); // PIN_Q0_1
  gpio.pinMode(A0_5, OUTPUT); // required?

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
  PID_A.initialise(modbus_server, gpio);
  PID_B.initialise(modbus_server, gpio);

  // PID mode
  PID_A.myPID_.SetMode(AUTOMATIC);
  PID_B.myPID_.SetMode(AUTOMATIC);
}

// Read two MCP9600 thermocouples
void readThermoCouples()
{
  // Read hot junction from each mcp
  for (int idx = 0; idx < num_mcp; idx++)
  {
    thermoReadings[idx] = mcp[idx].readThermocouple();
    Serial.print((String)"Thermocouple reading (" + idx + "): ");
    Serial.println(thermoReadings[idx]);
  }

  // Write both readings (written to thermocouple_C, overlapping to D)
  modbus_server.writeInputRegisters(
    MOD_THERMOCOUPLE_C_INP, (uint16_t*)(&thermoReadings), 4
  );

  // Write counter
  modbus_server.writeInputRegisters(
    MOD_COUNTER_INP, (uint16_t*)(&counter), 2
  );
  counter++;
  Serial.println(counter);
}

// Thermal gradient is based off of midpoint of heater setpoints and overrides them
void thermalGradient()
{
  // Get temperature (K) per mm
  float wanted = combineHoldingRegisters(modbus_server, MOD_GRADIENT_WANTED_HOLD);
  // Get distance (mm)
  float distance = combineHoldingRegisters(modbus_server, MOD_GRADIENT_DISTANCE_HOLD);
  // Theoretical temperature gradient (k/mm * mm = k)
  float theoretical = wanted * distance;
  float gradientModifier = theoretical/2;

  // Calculate midpoint and 
  float setPointA = combineHoldingRegisters(modbus_server, MOD_SETPOINT_A_HOLD);
  float setPointB = combineHoldingRegisters(modbus_server, MOD_SETPOINT_B_HOLD);
  float midpoint = (setPointA + setPointB) / 2.0;

  float signA, signB;

  // Identify if heater is above or below midpoint to determine gradient direction
  if (PID_A.setPoint == PID_B.setPoint)
  {
    // If setpoints are the same, calculations will divide by zero. Arbitrary gradient direction
    signA = 1.0;
    signB = -1.0;
  }
  else
  {
    // (+/-value) / value = +/-1
    signA = (PID_A.setPoint - midpoint)/(fabs(PID_A.setPoint - midpoint));
    signB = (PID_B.setPoint - midpoint)/(fabs(PID_B.setPoint - midpoint));
  }

  // Calculate gradient target setpoints
  PID_A.gradientSetPoint = midpoint + (signA * gradientModifier);
  PID_B.gradientSetPoint = midpoint + (signB * gradientModifier);

  // Actual temperature difference
  float actual = fabs(PID_A.input - PID_B.input);

  // Write relevant values to modbus
  modbus_server.writeInputRegisters(MOD_GRADIENT_THEORY_INP, (uint16_t*)(&theoretical), 2);
  modbus_server.writeInputRegisters(MOD_GRADIENT_ACTUAL_INP, (uint16_t*)(&actual), 2);

  // Write gradient target setpoints for UI use
  modbus_server.writeInputRegisters(MOD_GRADIENT_SETPOINT_A_INP, (uint16_t*)(&PID_A.gradientSetPoint), 2);
  modbus_server.writeInputRegisters(MOD_GRADIENT_SETPOINT_B_INP, (uint16_t*)(&PID_B.gradientSetPoint), 2);
}

 // Increment setPoint by an average rate per second
void autoSetPointControl()
{
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
  rate = rate * (static_cast<float>(intervalPID)/1000); // e.g.: 0.5 * 20/1000 = 0.01 = 50 times per second
  PID_A.autospRate = rate;
  PID_B.autospRate = rate;

  // Get img per degree
  float imgPerDegree = combineHoldingRegisters(modbus_server, MOD_AUTOSP_IMGDEGREE_HOLD);

  // Calculate midpoint. Fabs in case B is higher temp
  float midpoint = fabs((PID_A.input + PID_B.input) / 2);
  modbus_server.writeInputRegisters(MOD_AUTOSP_MIDPT_INP, (uint16_t*)(&midpoint), 2);
}

// Client connections handled on core 1 (loop)
void loop()
{
  // Listen for incoming clients
  EthernetClient client = ethServer.available();

  if (client)
  {
    Serial.println("New client");
    modbus_server.accept(client);

    while (client.connected())
    {
      // Poll for requests while client is connected
      int ret = modbus_server.poll();
      if (ret) 
      {
        // Nothing needed here right now.
      }
    }
    Serial.println("Client disconnected");
    connectionTimer = millis();
  }

  // Disable heaters if no connection for 30 seconds. Checked only if no current connection.
  long int elapsedTime = millis() - connectionTimer;
  if (elapsedTime > connectionTimeout)
  {
    modbus_server.coilWrite(MOD_PID_ENABLE_A_COIL, 0);
    modbus_server.coilWrite(MOD_PID_ENABLE_B_COIL, 0);
    // Reset timer so writing doesn't occur every single loop
    connectionTimer = millis();
  }
}

 // Core 0 task to handle device control
void Core0PIDTask(void * pvParameters)
{
  Serial.print("Task 2 running on core ");
  Serial.println(xPortGetCoreID());
  delay(1000);

  for(;;)
  {
     // Get 'current' time
    long int now = millis();

    // Run control after its specified interval
    if ( (now-tRead) >= 1000 )
    {
      tRead = millis(); // Timers read before as runtime should not influence call period
      readThermoCouples();
    }

    if ( (now - tGradient) >= intervalGradient)
    {
      tGradient = millis();
      thermalGradient();
    }

    if ( (now - tAutosp) >= intervalAutosp)
    {
      tAutosp = millis();
      autoSetPointControl();
    }

    if ( (now - tPID) >= intervalPID )
    {
      tPID = millis(); // Only need one timer, PIDs have same period

      double readingA = mcp[0].readThermocouple(); // First thermocouple for A
      double readingB = mcp[1].readThermocouple(); // Second thermocouple for B

      PID_A.run(readingA);
      PID_B.run(readingB);
      Serial.println("");
    }
  }
}
