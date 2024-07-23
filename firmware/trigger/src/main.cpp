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
#include <modbusServerController.h>

static bool eth_connected = false;

TaskHandle_t Task1;

// byte mac[] = { 0x00, 0x80, 0xe1, 0x3b, 0x00, 0x1d };
byte ip[] = { 192, 168, 0, 160 };
byte gateway[] = { 192, 168, 0, 1 };
byte subnet[] = { 255, 255, 255, 0 };

WiFiServer server(502);

// EthernetServer ethServer(502);
ModbusServerController modbus_server;

// WANT TO REPLACE THIS WITH MODBUSSERVERCONTROLLER
// SO I CAN WRITE HOLDING REGISTERS
// AND SEND HIGHER TIMER INTERVALS VIA THE ADAPTER
// SHOULD WORK PERFECTLY AFTER THAT

hw_timer_t *furnaceTimer = NULL;
hw_timer_t *wideFovTimer = NULL;
hw_timer_t *narrowFovTimer = NULL;

// Is furnace running
bool furnaceEnabled = false;
bool widefovEnabled = false;
bool narrowfovEnabled = false;

// For frame counting - to request a specific number or run until shut down
volatile int furnaceFrameCount = 0;
volatile int wideFovFrameCount = 0;
volatile int narrowFovFrameCount = 0;

int furnaceFrameTarget = 0;
int wideFovFrameTarget = 0;
int narrowFovFrameTarget = 0;

// Is the signal 'rising' or 'falling'?
// Want to alternate every call for 50% duty cycle
volatile bool risingFurnace = true;
volatile bool risingWide = true;
volatile bool risingNarrow = true;

// These flags are set only when the frame target is reached.
// Would be preferable to write false to the relevant enable coil, but that is not ISR-safe.
volatile bool furnaceShutdown = false;
volatile bool widefovShutdown = false;
volatile bool narrowfovShutdown = false;

void IRAM_ATTR furnaceOnTimer()
{
  // Non-zero target has been met or exceeded, return early
  if (furnaceFrameTarget != 0 && furnaceFrameCount >= furnaceFrameTarget)
  {
    furnaceShutdown = true;
    return;
  }
  digitalWrite(PIN_FURNACE, risingFurnace);
  if (risingFurnace)
  {
    furnaceFrameCount++;
  }
  risingFurnace = !risingFurnace;
}
void IRAM_ATTR wideFovOnTimer()
{
  if (wideFovFrameTarget != 0 && wideFovFrameCount >= wideFovFrameTarget)
  {
    widefovShutdown = true;
    return;
  }
  digitalWrite(PIN_WIDEFOV, risingWide);
  if (risingWide)
  {
    wideFovFrameCount++;
  }
  risingWide = !risingWide;
}
void IRAM_ATTR narrowFovOnTimer()
{
  if (narrowFovFrameTarget != 0 && narrowFovFrameCount >= narrowFovFrameTarget)
  {
    narrowfovShutdown = true;
    return;
  }
  digitalWrite(PIN_NARROWFOV, risingNarrow);
  if (risingNarrow)
  {
    narrowFovFrameCount++;
  }
  risingNarrow = !risingNarrow;
}

void Task1Code(void * pvParameters)
{
  Serial.print("Task1 running on core ");
  Serial.println(xPortGetCoreID());

  for(;;)
  {
    bool furnaceSetting = modbus_server.coilRead(TRIG_FURNACE_ENABLE_COIL);
    bool widefovSetting = modbus_server.coilRead(TRIG_WIDEFOV_ENABLE_COIL);
    bool narrowfovSetting = modbus_server.coilRead(TRIG_NARROWFOV_ENABLE_COIL);

    // For each furnace:
    // if shutdown flag, or if enabled and wanted off, turn it off. If disabled and wanted on,
    // turn it on. Other combinations require no action.
    if (furnaceShutdown || (furnaceEnabled && !furnaceSetting)) {
      timerAlarmDisable(furnaceTimer); furnaceEnabled = false;
      risingFurnace = false; digitalWrite(PIN_FURNACE, risingFurnace);
    }
    else if (!furnaceEnabled && furnaceSetting) {
      timerAlarmEnable(furnaceTimer); // Start timer
      furnaceEnabled = true; // Flag enabled
      furnaceFrameCount = 0; // Set frame count to 0
    }
    if (widefovShutdown || (widefovEnabled && !widefovSetting)) {
      timerAlarmDisable(wideFovTimer); widefovEnabled = false;
      risingWide = false; digitalWrite(PIN_WIDEFOV, risingWide);
    }
    else if (!widefovEnabled && widefovSetting) { timerAlarmEnable(wideFovTimer); widefovEnabled = true; wideFovFrameCount = 0; }

    if (narrowfovShutdown || (narrowfovEnabled && !narrowfovSetting)) {
      timerAlarmDisable(narrowFovTimer); narrowfovEnabled = false;
      risingNarrow = false; digitalWrite(PIN_NARROWFOV, risingNarrow);
    }
    else if (!narrowfovEnabled && narrowfovSetting) { timerAlarmEnable(narrowFovTimer); narrowfovEnabled = true; narrowFovFrameCount = 0; }

    // Check if any values have been updated
    bool value_updated = modbus_server.coilRead(TRIG_VAL_UPDATED_COIL);
    if (value_updated)
    {
      // Only update a timer if it isn't already running.
      if (!furnaceEnabled)
      {
        int new_interval = modbus_server.combineHoldingRegisters(TRIG_FURNACE_INTVL_HOLD);
        timerAlarmWrite(furnaceTimer, new_interval, true);

        int new_target = modbus_server.combineHoldingRegisters(TRIG_FURNACE_TARGET_HOLD);
        furnaceFrameTarget = new_target;
      }
      if (!widefovEnabled)
      {
        int new_interval = modbus_server.combineHoldingRegisters(TRIG_WIDEFOV_INTVL_HOLD);
        timerAlarmWrite(wideFovTimer, new_interval, true);

        int new_target = modbus_server.combineHoldingRegisters(TRIG_WIDEFOV_TARGET_HOLD);
        wideFovFrameTarget = new_target;
      }
      if (!narrowfovEnabled)
      {
        int new_interval = modbus_server.combineHoldingRegisters(TRIG_NARROWFOV_INTVL_HOLD);
        timerAlarmWrite(narrowFovTimer, new_interval, true);

        int new_target = modbus_server.combineHoldingRegisters(TRIG_NARROWFOV_TARGET_HOLD);
        narrowFovFrameTarget = new_target;
      }
      modbus_server.coilWrite(TRIG_VAL_UPDATED_COIL, false);
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

  if (Ethernet.linkStatus() == LinkOFF) {
    Serial.println("Ethernet cable is not connected.");
  }

  // start the Modbus TCP server
  if (!modbus_server.begin()) {
    Serial.println("Failed to start Modbus TCP Server!");
    while (1);
  }

  // Configure pins to output
  pinMode(PIN_FURNACE, OUTPUT);  // furnace
  pinMode(PIN_WIDEFOV, OUTPUT);  // wideFov
  pinMode(PIN_NARROWFOV, OUTPUT);  // narrowFov

  // configure eight coils at address 0x00, repeat for others
  modbus_server.configureCoils(0, 8);

  modbus_server.configureDiscreteInputs(10001, 8);
  uint8_t inputs[8] = {0, 0, 1, 1, 0, 1, 0, 1};
  modbus_server.writeDiscreteInputs(10001, inputs, 8);

  modbus_server.configureInputRegisters(30001, 16);
  modbus_server.configureHoldingRegisters(40001, 16);

  // Write initial values to registers
  modbus_server.floatToHoldingRegisters(TRIG_FURNACE_INTVL_HOLD, (1000000/FREQUENCY_FURNACE)/2);
  modbus_server.floatToHoldingRegisters(TRIG_WIDEFOV_INTVL_HOLD, (1000000/FREQUENCY_WIDEFOV)/2);
  modbus_server.floatToHoldingRegisters(TRIG_NARROWFOV_INTVL_HOLD, (1000000/FREQUENCY_NARROWFOV)/2);

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
  timerAlarmWrite(furnaceTimer, (1000000/FREQUENCY_FURNACE)/2, true);

  wideFovTimer = timerBegin(1, 80, true);
  timerAttachInterrupt(wideFovTimer, &wideFovOnTimer, true);
  timerAlarmWrite(wideFovTimer, (1000000/FREQUENCY_WIDEFOV)/2, true);

  narrowFovTimer = timerBegin(2, 80, true);
  timerAttachInterrupt(narrowFovTimer, &narrowFovOnTimer, true);
  timerAlarmWrite(narrowFovTimer, (1000000/FREQUENCY_NARROWFOV)/2, true);
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
