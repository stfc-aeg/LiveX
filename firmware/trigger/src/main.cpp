/*
    This sketch shows the Ethernet event usage

*/

#include <Arduino.h>
#include <ETH.h>
#include <Wire.h>
#include <Ethernet.h>
#include <SPI.h>
#include <ArduinoRS485.h>
#include <ArduinoModbus.h>

#include <cmath>
#include <esp32-hal-timer.h>
#include <driver/timer.h>

#include <config.h>

static bool eth_connected = false;

TaskHandle_t Task1;

// byte mac[] = { 0x00, 0x80, 0xe1, 0x3b, 0x00, 0x1d };
byte ip[] = { 192, 168, 0, 160 };
byte gateway[] = { 192, 168, 0, 1 };
byte subnet[] = { 255, 255, 255, 0 };

WiFiServer server(502);

// EthernetServer ethServer(502);
ModbusTCPServer modbus_server;

hw_timer_t *furnaceTimer = NULL;
hw_timer_t *wideFovTimer = NULL;
hw_timer_t *narrowFovTimer = NULL;

bool furnaceEnabled = false;
bool widefovEnabled = false;
bool narrowfovEnabled = false;

volatile bool furnaceFlag = false;
volatile bool wideFovFlag = false;
volatile bool narrowFovFlag = false;

bool runningFlag = false;

void IRAM_ATTR furnaceOnTimer()
{
  digitalWrite(2, HIGH);
  furnaceFlag = true;
  furnaceEnabled = true;
}
void IRAM_ATTR wideFovOnTimer()
{
  digitalWrite(32, HIGH);
  wideFovFlag = true;
  widefovEnabled = true;
}
void IRAM_ATTR narrowFovOnTimer()
{
  digitalWrite(33, HIGH);
  narrowFovFlag = true;
  narrowfovEnabled = true;
}

void Task1Code(void * pvParameters)
{
  Serial.print("Task1 running on core ");
  Serial.println(xPortGetCoreID());

  for(;;)
  {
    // Remember that timer enable flags are set within the timers

    // We don't want to update parameters if any timers are going, for simplicity's sake

    bool furnaceSetting = modbus_server.coilRead(TRIG_FURNACE_ENABLE_COIL);
    bool widefovSetting = modbus_server.coilRead(TRIG_WIDEFOV_ENABLE_COIL);
    bool narrowfovSetting = modbus_server.coilRead(TRIG_NARROWFOV_ENABLE_COIL);

    // For each furnace: if enabled and wanted off, turn it off. If disabled and wanted on,
    // turn it on. Other combinations require no action.
    if (furnaceEnabled && !furnaceSetting)      { timerAlarmDisable(furnaceTimer); furnaceEnabled = false; }
    else if (!furnaceEnabled && furnaceSetting) { timerAlarmEnable(furnaceTimer); furnaceEnabled = true; }

    if (widefovEnabled && !widefovSetting)      { timerAlarmDisable(wideFovTimer); widefovEnabled = false; }
    else if (!widefovEnabled && widefovSetting) { timerAlarmEnable(wideFovTimer); widefovEnabled = true; }

    if (narrowfovEnabled && !narrowfovSetting)      { timerAlarmDisable(narrowFovTimer); narrowfovEnabled = false; }
    else if (!narrowfovEnabled && narrowfovSetting) { timerAlarmEnable(narrowFovTimer); narrowfovEnabled = true; }

    if (!(furnaceEnabled || widefovEnabled || narrowfovEnabled)) // No timers enabled, check parameters
    {
      // Check if any values have been updated
      bool value_updated = modbus_server.coilRead(TRIG_VAL_UPDATED_COIL);
      if (value_updated)
      {  // If they have, then update all timer intervals
        Serial.print("changing timer values:");
        int new_interval = modbus_server.holdingRegisterRead(TRIG_FURNACE_INTVL_HOLD);
        timerAlarmWrite(furnaceTimer, new_interval, true);
        Serial.print(new_interval);
        new_interval = modbus_server.holdingRegisterRead(TRIG_WIDEFOV_INTVL_HOLD);
        timerAlarmWrite(wideFovTimer, new_interval, true);
        Serial.print(new_interval);
        new_interval = modbus_server.holdingRegisterRead(TRIG_NARROWFOV_INTVL_HOLD);
        timerAlarmWrite(narrowFovTimer, new_interval, true);
        Serial.println(new_interval);
      }
    }

    if (furnaceFlag && wideFovFlag && narrowFovFlag)
    {
      Serial.print(".");
      furnaceFlag, wideFovFlag, narrowFovFlag = false;
    }
    delay(1);
  }
}

void setup()
{
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  delay(3000);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.println("Ethernet Modbus TCP Example");

  ETH.begin();
  ETH.config(ip, gateway, subnet);
  server.begin();

  // Ethernet.init(15);

  // // start the Ethernet connection and the server:
  // Ethernet.begin(mac, ip, gateway, subnet);

  // Check for Ethernet hardware present
  // if (Ethernet.hardwareStatus() == EthernetNoHardware) {
  //   Serial.println("Ethernet shield was not found.  Sorry, can't run without hardware. :(");
  //   while (true) {
  //     delay(1); // do nothing, no point running without Ethernet hardware
  //   }
  // }
  if (Ethernet.linkStatus() == LinkOFF) {
    Serial.println("Ethernet cable is not connected.");
  }

  // start the server
  // ethServer.begin();
  // Serial.print("server is at");
  // Serial.println(Ethernet.localIP());

  // start the Modbus TCP server
  if (!modbus_server.begin()) {
    Serial.println("Failed to start Modbus TCP Server!");
    while (1);
  }

  pinMode(2, OUTPUT);  // furnace
  pinMode(32, OUTPUT);  // wideFov
  pinMode(33, OUTPUT);  // narrowFov

  // configure eight coils at address 0x00, repeat for others
  modbus_server.configureCoils(0, 8);

  modbus_server.configureDiscreteInputs(10001, 8);
  uint8_t inputs[8] = {0, 0, 1, 1, 0, 1, 0, 1};
  modbus_server.writeDiscreteInputs(10001, inputs, 8);

  modbus_server.configureInputRegisters(30001, 16);
  modbus_server.configureHoldingRegisters(40001, 16);

  Serial.print("Setup running on core ");
  Serial.println(xPortGetCoreID());

  xTaskCreatePinnedToCore(
      Task1Code,     /* Task function */
      "Task1",      /* Name of task  */
      10000,       /* Stack size    */
      NULL,       /* Parameter     */
      1,         /* Priority      */
      &Task1,   /* Handle        */
      0        /* Pin to core 0 */
  );
  delay(500);

  // Configure timers
  furnaceTimer = timerBegin(0, 80, true);
  timerAttachInterrupt(furnaceTimer, &furnaceOnTimer, true);
  timerAlarmWrite(furnaceTimer, (1000000/FREQUENCY_FURNACE), true);

  wideFovTimer = timerBegin(1, 80, true);
  timerAttachInterrupt(wideFovTimer, &wideFovOnTimer, true);
  timerAlarmWrite(wideFovTimer, (1000000/FREQUENCY_WIDEFOV), true);

  narrowFovTimer = timerBegin(2, 80, true);
  timerAttachInterrupt(narrowFovTimer, &narrowFovOnTimer, true);
  timerAlarmWrite(narrowFovTimer, (1000000/FREQUENCY_NARROWFOV), true);
}

void loop()
{
  // Listen for incoming clients
  WiFiClient client = server.available();

  if (client) {
    Serial.println("new client");
    modbus_server.accept(client);
    while (client.connected()){
      int ret = modbus_server.poll();
      if (ret) {
        Serial.print(".");
      }
    }
    Serial.println("Client disconnected");
  }
  delay(100);

}
