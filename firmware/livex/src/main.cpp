#include <Ethernet.h>
#include <SPI.h>
#include <WiFi.h>
#include <ArduinoRS485.h>
#include <ArduinoModbus.h>

#include <ExpandedGpio.h>
#include "pins_is.h"
#include "devices.h"

#include <Adafruit_I2CDevice.h>
#include <Adafruit_I2CRegister.h>
#include "Adafruit_MCP9600.h"
#include <PID_v1.h>

#define PWM_PIN 0x400d // A0_5

static bool eth_connected = false;

EthernetServer ethServer(502);
ModbusTCPServer modbus_server;
ExpandedGpio gpio;

byte mac[] = { 0x10, 0x97, 0xbd, 0xca, 0xea, 0x14 };
byte ip[] = { 192, 168, 0, 159 };
byte gateway[] = { 192, 168, 0, 1 };
byte subnet[] = { 255, 255, 255, 0 };

// Modbus register values
const int coilAddress = 0; // Currently unused
const int numCoils = 8;

const int inputRegAddress = 30001;
const int numInputRegs = 16;

const int holdingRegAddress = 40001;
const int numRegs = 16;

// PID and Counter setup
float counter = 0;
long int tWrite = millis(); // Timer for write
// Output multiplier as 4095/255 does not work. This is close enough for now.
float outputMultiplier = 16.0588;

double setPoint, input, output;
double Kp = 25;
double Ki = 5;
double Kd = 0;
bool loop_PID = false;
PID myPID(&input, &output, &setPoint, Kp,Ki,Kd, DIRECT);

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

  // IS ESP32 module has Ethernet SPI CS on pin 15
  Ethernet.init(PIN_SPI_SS_ETHERNET_LIB);
  // Start the Ethernet connection and the server
  Ethernet.begin(mac, ip);
  ethServer.begin();

  // Check for Ethernet hardware present
  if (Ethernet.hardwareStatus() == EthernetNoHardware) 
  {
    Serial.println("Ethernet shield was not found.  Sorry, can't run without hardware. :(");
    while (true) 
    {
      Serial.print(".");
      delay(1000); // do nothing, no point running without Ethernet hardware
    }
  }
  if (Ethernet.linkStatus() == LinkOFF) 
  {
    Serial.println("Ethernet cable is not connected.");
  }

  // Modbus setup
  if (!modbus_server.begin()) 
  {
    Serial.println("Failed to start Modbus TCP Server!");
    while (1);
  }

  // Configure and intialise modbus coils/registers
  modbus_server.configureCoils(coilAddress, numCoils);
  modbus_server.configureInputRegisters(inputRegAddress, numInputRegs);
  modbus_server.configureHoldingRegisters(holdingRegAddress, numRegs);

  // Write in default PID values to modbus
  float pidDefaults[4] = {25, 25.1, 5.5, 0.1}; // setPoint, Kp, Ki, Kd
  int tempHoldAddr = holdingRegAddress;

  for(float term : pidDefaults)
  {
    // Registers hold 16 bits. Floats are written over two registers
    uint16_t* elems = (uint16_t*)&term;
    for (int i = 0; i<2; i++)
    {
      modbus_server.holdingRegisterWrite(tempHoldAddr+i, elems[i]);
    }
    tempHoldAddr = tempHoldAddr +2;
  }

  initialiseThermocouples(mcp, num_mcp, mcp_addr); // devices.cpp

  xTaskCreatePinnedToCore(
    Core0PIDTask,     /* Task function */
    "PIDTask",      /* Name of task  */
    10000,       /* Stack size    */
    NULL,       /* Parameter     */
    2,         /* Priority      */
    NULL,   /* Handle        */
    0        /* Pin to core 1 */
  );

  // PID setpoint and mode
  input = mcp[0].readThermocouple();
  setPoint = modbus_server.holdingRegisterRead(holdingRegAddress);
  myPID.SetMode(AUTOMATIC);

  gpio.init();
  gpio.pinMode(0x400b, OUTPUT); // PIN_Q0_0
  gpio.pinMode(0x400a, OUTPUT); // PIN_Q0_1
  gpio.pinMode(0x400d, OUTPUT); // required?
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
    inputRegAddress, (uint16_t*)(&thermoReadings), 4
  );
  // Write counter
  modbus_server.writeInputRegisters(
    inputRegAddress+4, (uint16_t*)(&counter), 2
  );
  counter++;
  Serial.print(counter);
  return millis();
}

union ModbusFloat
{ // This union allows two 16-bit ints to be read back as a 32-bit float
    float value;
    struct 
    {
        uint16_t low;
        uint16_t high;
    } registers;
};

float combineHoldingRegisters(int address)
{ // See union ModbusFloat. Stich two ints into one float
  uint16_t A = modbus_server.holdingRegisterRead(address);
  uint16_t B = modbus_server.holdingRegisterRead(address+1);

  ModbusFloat modbusFloat;
  modbusFloat.registers.high = B; // little-endian
  modbusFloat.registers.low = A;
  return modbusFloat.value;
}

long int do_PID()
{
  /* PID loop for one thermocouple
  Read thermocouple, get setpoint, compute PID, handle output, write it
  */
  input = mcp[0].readThermocouple();
  // Get setpoint here in case it has changed
  setPoint = combineHoldingRegisters(holdingRegAddress);
  myPID.Compute();
  // Circuitry needs reversed output. Could use native PID library reverse
  // Output is on a scale of 0-255, hence 255-output
  output = 255 - output;
  output = output * outputMultiplier; // Scale up to 4095
  Serial.print("Output value: ");
  Serial.println(output);

  gpio.analogWrite(PWM_PIN, output); // Expanded pin, use custom library

  // Easier to write to/read from register with float than double. consistency
  float pidOutput = output;
  modbus_server.writeInputRegisters(
    inputRegAddress+6, (uint16_t*)(&pidOutput), 2
  );
  return millis(); // Time since last reading
}

void check_PID_tunings()
{ // Check if any are different, and set them if so
  double newKp = double(combineHoldingRegisters(holdingRegAddress+2));
  double newKi = double(combineHoldingRegisters(holdingRegAddress+4));
  double newKd = double(combineHoldingRegisters(holdingRegAddress+6));
  if ((newKp != Kp) || (newKi != Ki) || (newKd != Kd)) {
    myPID.SetTunings(newKp, newKi, newKd);
    Kp = newKp;
    Ki = newKi;
    Kd = newKd;
  }
}

bool check_pid_enabled()
{ // If value = 0, false
  return modbus_server.holdingRegisterRead(holdingRegAddress+8);
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
    if ( (millis() - tWrite) >= 1000 ) 
    {
      loop_PID = check_pid_enabled();

      if (loop_PID == true)
      { // PID tunings checked each run
        check_PID_tunings();
        tWrite = do_PID();
      }
      else 
      { // If no PID enabled, write max output (reversed, 0).
        gpio.analogWrite(PWM_PIN, 4095);
        tWrite = millis();
      }
      Serial.println("");
    }
  }
}
