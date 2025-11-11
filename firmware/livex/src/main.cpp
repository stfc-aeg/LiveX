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

SemaphoreHandle_t gradientAspcMutex;

// addresses for PID objects
PIDAddresses pidA_addr = {
  PIN_PWM_UPPER,
  MOD_SETPOINT_UPPER_HOLD,
  MOD_PID_UPPER_OUTPUT_INP,
  MOD_PID_UPPER_OUTPUTSUM_INP,
  MOD_PID_UPPER_ENABLE_COIL,
  MOD_HEATERTC_A_INP,
  MOD_KP_UPPER_HOLD,
  MOD_KI_UPPER_HOLD,
  MOD_KD_UPPER_HOLD
};

PIDAddresses pidB_addr = {
  PIN_PWM_LOWER,
  MOD_SETPOINT_LOWER_HOLD,
  MOD_PID_LOWER_OUTPUT_INP,
  MOD_PID_LOWER_OUTPUTSUM_INP,
  MOD_PID_LOWER_ENABLE_COIL,
  MOD_HEATERTC_B_INP,
  MOD_KP_LOWER_HOLD,
  MOD_KI_LOWER_HOLD,
  MOD_KD_LOWER_HOLD
};

PIDController PID_A(pidA_addr);
PIDController PID_B(pidB_addr);

EthernetClient modbusClient;
EthernetClient streamClient;
long int connectionTimer;

float counter = 1;
bool acquiringFlag = false;

// Thermocouples - main, taskPid
Adafruit_MCP9600 mcp[6];  // Use default constructor to make as many as needed
const unsigned int num_mcp = sizeof(mcp) / sizeof(mcp[0]);
const uint8_t mcp_addr[] = {0x60, 0x67, 0x66, 0x65, 0x64, 0x63};
const MCP9600_ThemocoupleType mcp_type[] = {MCP9600_TYPE_R, MCP9600_TYPE_R, MCP9600_TYPE_K, MCP9600_TYPE_K, MCP9600_TYPE_K, MCP9600_TYPE_R};
const int mcp_mod_addrs[] = {};

// Timers and flags - main, taskPid
hw_timer_t* pidFlagTimer = NULL;
hw_timer_t* secondaryFlagTimer = NULL;
volatile bool pidFlag = false;
volatile bool secondaryFlag = false;
// Pin interrupt flag
volatile bool rising = true;
volatile int interruptCounter = 0;

// Communicated via modbus
float interruptFrequency = 10;

void IRAM_ATTR pidFlagOnTimer()
{
  pidFlag = true;
}

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
  initialiseInterrupts(&pidFlagTimer);
  initialiseThermocouples(mcp, num_mcp, mcp_addr, mcp_type);
  writePIDDefaults(modbus_server, PID_A);
  writePIDDefaults(modbus_server, PID_B);

  // Software needs to know how many thermocouples are active
  modbus_server.floatToInputRegisters(MOD_NUM_MCP_INP, num_mcp);
  // Write default indices for active thermocouples, assume in order
  for (int i=0; i<num_mcp; i++)
  {
    modbus_server.floatToHoldingRegisters(
      MOD_HEATERTC_A_IDX_HOLD+i*2, i
    );
    modbus_server.floatToHoldingRegisters(
      MOD_TCIDX_0_TYPE_HOLD+i*2, mcp_type[i]
    );
  }

  gpio.init();
  // PID
  gpio.pinMode(PIN_PWM_UPPER, OUTPUT);
  gpio.pinMode(PIN_PWM_LOWER, OUTPUT);
  // Motor direction/speed outputs
  gpio.pinMode(PIN_MOTOR_DIRECTION, OUTPUT);
  gpio.pinMode(PIN_MOTOR_PWM, OUTPUT);
  // Motor LVDT
  gpio.pinMode(PIN_MOTOR_LVDT_IN, INPUT);

  gradientAspcMutex = xSemaphoreCreateMutex();

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
