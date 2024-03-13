#include <resources.h>
#include <taskComms.h>
#include <taskPid.h>

// Eth settings - main
byte mac[] = { 0x10, 0x97, 0xbd, 0xca, 0xea, 0x14 };
byte ip[] = { 192, 168, 0, 159 };
byte gateway[] = { 192, 168, 0, 1 };
byte subnet[] = { 255, 255, 255, 0 };

// Key objects
EthernetServer modbusEthServer(502);
EthernetServer tcpEthServer(4444);
ModbusServerController modbus_server;
ExpandedGpio gpio;
FifoBuffer<BufferObject> buffer(256);

// addresses for PID objects
PIDAddresses pidA_addr = {
  PIN_PWM_A,
  MOD_SETPOINT_A_HOLD,
  MOD_PID_OUTPUT_A_INP,
  MOD_PID_ENABLE_A_COIL,
  MOD_THERMOCOUPLE_A_INP,
  MOD_KP_A_HOLD,
  MOD_KI_A_HOLD,
  MOD_KD_A_HOLD
};

PIDAddresses pidB_addr = {
  PIN_PWM_B,
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

EthernetClient modbusClient;
EthernetClient streamClient;
long int connectionTimer;

float counter = 1;
bool acquiringFlag = false;

// Thermocouples - main, taskPid
Adafruit_MCP9600 mcp[] = {Adafruit_MCP9600(), Adafruit_MCP9600()};
const unsigned int num_mcp = sizeof(mcp) / sizeof(mcp[0]);
const uint8_t mcp_addr[] = {0x60, 0x67};

// Timers and flags - main, taskPid
hw_timer_t *secondaryFlagTimer = NULL;
volatile bool pidFlag = false;
volatile bool secondaryFlag = false;
// Pin interrupt flag 
volatile bool rising = true;
volatile int interruptCounter = 0;

// may be rolled into toggledInterrupt
void IRAM_ATTR pidInterrupt()
{
  if (rising)
  {
    pidFlag = true;
    interruptCounter += 1;
  }
  rising = !rising;
}

void IRAM_ATTR secondaryFlagOnTimer()
{
  secondaryFlag = true;
}

// Initialise wires, devices, and Modbus/gpio
void setup()
{
  Serial.begin(9600);
  delay(2000); // Serial requires a moment to be ready

  // I2C initialisation to ensure it is established before I2C calls made
  Wire.begin();
  // Server initialisations
  tcpEthServer.begin();
  modbus_server.initialiseModbus();
  // initialise.cpp
  initialiseEthernet(modbusEthServer, mac, ip, PIN_SPI_SS_ETHERNET_LIB);
  initialiseInterrupts(&secondaryFlagTimer);
  initialiseThermocouples(mcp, num_mcp, mcp_addr);
  writePIDDefaults(modbus_server, PID_A);
  writePIDDefaults(modbus_server, PID_B);

  gpio.init();
  // PID
  gpio.pinMode(A0_5, OUTPUT);
  // Motor direction/speed outputs
  gpio.pinMode(Q1_6, OUTPUT);
  gpio.pinMode(Q1_7, OUTPUT);
  // Motor LVDT
  gpio.pinMode(I0_7, INPUT);
  // External trigger pin
  gpio.pinMode(Q1_0, OUTPUT);

  xTaskCreatePinnedToCore(
    Core0PIDTask,  /* Task function */
    "PIDTask",    /* Name of task  */
    10000,       /* Stack size    */
    NULL,       /* Parameter     */
    2,         /* Priority      */
    NULL,     /* Handle        */
    0        /* Pin to core 1 */
  );
}

void loop()
{
  manageComms();
}
