#include <Arduino.h>
#include <ETH.h>
#include <ArduinoModbus.h>
#include "esp_eth.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "config.h"
#include "modbusUtils.h"

#include <cmath>
#include <esp32-hal-timer.h>
#include <driver/timer.h>

// Debug mode: uncomment to enable extra logging
// #define DEBUG_MODE

// Static IP configuration
IPAddress ip(192, 168, 0, 160);
IPAddress gateway(192, 168, 0, 1);
IPAddress subnet(255, 255, 255, 0);

// Function prototypes
void setupGPIO();
void setupModbus();
void fastLoopTask(void *pvParameters);
void modbusTask(void *pvParameters);
void WiFiEvent(WiFiEvent_t event);
void startTimer(int index);
void stopTimer(int index);
void startAllTimers();
void stopAllTimers();
int updateTimer(int index);

void IRAM_ATTR onTimer0();
void IRAM_ATTR onTimer1();
void IRAM_ATTR onTimer2();
void IRAM_ATTR handleInterrupt(int index);

// Global variables
ModbusTCPServer modbusTCPServer;
TaskHandle_t fastLoopTaskHandle;
TaskHandle_t modbusTaskHandle;

SemaphoreHandle_t pwmMutex;

// PWM parameters
uint32_t frequency[3] = {0, 0, 0};
uint32_t pulseCount[3] = {0, 0, 0}; // Target # of instances
volatile uint32_t activePulseCount[3] = {0, 0, 0}; // For use in interrupts, enables restart logic
volatile bool enablePWM[3] = {false, false, false};
bool timersRunning[3] = {false, false, false};

static bool eth_connected = false;
bool startAll = false;
bool stopAll = false;

// GPIO and timer variables
const int pwmPins[3] = {PIN_TRIGGER_1, PIN_TRIGGER_2, PIN_TRIGGER_3};
volatile bool pinStates[3] = {false, false, false};
hw_timer_t *timers[3] = {nullptr, nullptr, nullptr};

// For readable address referencing
int addrEnable[3] = {TRIG_FURNACE_ENABLE_COIL, TRIG_WIDEFOV_ENABLE_COIL, TRIG_NARROWFOV_ENABLE_COIL};
int addrDisable[3] = {TRIG_FURNACE_DISABLE_COIL, TRIG_WIDEFOV_DISABLE_COIL, TRIG_NARROWFOV_DISABLE_COIL};
int addrRunning[3] = {TRIG_FURNACE_RUNNING_COIL, TRIG_WIDEFOV_RUNNING_COIL, TRIG_NARROWFOV_RUNNING_COIL};
int addrIntvl[3] = {TRIG_FURNACE_INTVL_HOLD, TRIG_WIDEFOV_INTVL_HOLD, TRIG_NARROWFOV_INTVL_HOLD};
int addrTarget[3] = {TRIG_FURNACE_TARGET_HOLD, TRIG_WIDEFOV_TARGET_HOLD, TRIG_NARROWFOV_TARGET_HOLD};

volatile int counter = 0;

// Debug logging macro
#ifdef DEBUG_MODE
#define DEBUG_PRINT(x) Serial.println(x)
#else
#define DEBUG_PRINT(x)
#endif

// Timer interrupt handlers
void IRAM_ATTR onTimer0()
{
  counter++;
  pinStates[0] = !pinStates[0];
  digitalWrite(pwmPins[0], pinStates[0]);

  // Count down on falling edge provided the target is higher than 0
  if (!pinStates[0] && activePulseCount[0] > 0)
  {
    activePulseCount[0]--;
    // at 0, disable PWM
    if (activePulseCount[0] == 0)
    {
      enablePWM[0] = false;
      digitalWrite(pwmPins[0], LOW);
      timerAlarmDisable(timers[0]);
    }
  }
}

// Written with less whitespace for space
void IRAM_ATTR onTimer1(){
  counter++;
  pinStates[1] = !pinStates[1];
  digitalWrite(pwmPins[1], pinStates[1]);
  if (!pinStates[1] && activePulseCount[1] > 0){
    activePulseCount[1]--;
    if (activePulseCount[1] == 0){
      enablePWM[1] = false;
      digitalWrite(pwmPins[1], LOW);
      timerAlarmDisable(timers[1]);
  }}
}

void IRAM_ATTR onTimer2(){
  counter++;
  pinStates[2] = !pinStates[2];
  digitalWrite(pwmPins[2], pinStates[2]);
  if (!pinStates[2] && activePulseCount[2] > 0){
    activePulseCount[2]--;
    if (activePulseCount[2] == 0){
      enablePWM[2] = false;
      digitalWrite(pwmPins[2], LOW);
      timerAlarmDisable(timers[2]);
  }}
}

void IRAM_ATTR handleInterrupt(int index)
{

  // Always toggle state and count down
  pinStates[index] = !pinStates[index]; // toggle state
  digitalWrite(pwmPins[index], pinStates[index]); // write state to pin

  // Count down on falling edge provided the target is higher than 0
  if (!pinStates[index] && pulseCount[index] > 0)
  {
    pulseCount[index]--;
    // at 0, disable PWM
    if (pulseCount[index] == 0)
    {
      enablePWM[index] = false;
      digitalWrite(pwmPins[index], LOW);
      timerAlarmDisable(timers[index]);
    }
  }
}

void WiFiEvent(WiFiEvent_t event)
{
  switch (event)
  {
    case ARDUINO_EVENT_ETH_START:
      DEBUG_PRINT("ETH Started");
      ETH.setHostname("esp32-ethernet");
      break;
    case ARDUINO_EVENT_ETH_CONNECTED:
      DEBUG_PRINT("ETH Connected");
      break;
    case ARDUINO_EVENT_ETH_GOT_IP:
      Serial.print("ETH MAC: ");
      Serial.print(ETH.macAddress());
      Serial.print(", IPv4: ");
      Serial.print(ETH.localIP());
      if (ETH.fullDuplex())
      {
        Serial.print(", FULL_DUPLEX");
      }
      Serial.print(", ");
      Serial.print(ETH.linkSpeed());
      Serial.println("Mbps");
      eth_connected = true;
      break;
    case ARDUINO_EVENT_ETH_DISCONNECTED:
      DEBUG_PRINT("ETH Disconnected");
      eth_connected = false;
      break;
    case ARDUINO_EVENT_ETH_STOP:
      DEBUG_PRINT("ETH Stopped");
      eth_connected = false;
      break;
    default:
      break;
  }
}

void setup()
{
  Serial.begin(9600);

  // Initialize Ethernet
  WiFi.onEvent(WiFiEvent);
  ETH.begin();
  ETH.config(ip, gateway, subnet);

  // Wait for Ethernet connection
  while (!eth_connected)
  {
    delay(1000);
    Serial.println("Waiting for Ethernet connection...");
  }

  // Create mutex for thread-safe access to shared variables
  pwmMutex = xSemaphoreCreateMutex();

  setupGPIO();
  setupModbus();

  // Timer initialisation
  for (int i=0; i<3; i++)
  {
    timers[i] = timerBegin(i, 80, true); // Timer number, prescaler (80MHz), count up
    if (timers[i]){ Serial.printf("Timer %d started successfully.", timers[i]); }
  }

  timerAttachInterrupt(timers[0], &onTimer0, true);
  timerAttachInterrupt(timers[1], &onTimer1, true);
  timerAttachInterrupt(timers[2], &onTimer2, true);

  // Create tasks on separate cores
  // xTaskCreatePinnedToCore(fastLoopTask, "Fast Loop Task", 4096, NULL, 5, &fastLoopTaskHandle, 0);
  xTaskCreatePinnedToCore(modbusTask, "Modbus Task", 4096, NULL, 5, &modbusTaskHandle, 1);
}

void loop()
{
  // Tasks handle everything
  // Serial.printf("%d, ", counter);
  vTaskDelay(1000);
}

void setupGPIO()
{
  for (int i = 0; i < 3; i++)
  {
    pinMode(pwmPins[i], OUTPUT);
    digitalWrite(pwmPins[i], LOW);
  }
}

// Start server and configure registers
void setupModbus()
{
  modbusTCPServer.begin();
  modbusTCPServer.configureHoldingRegisters(TRIG_FURNACE_INTVL_HOLD, TRIG_NUM_HOLD);
  modbusTCPServer.configureCoils(TRIG_ENABLE_COIL, TRIG_NUM_COIL);
}

int updateTimer(int index)
{
  uint32_t period = 1000000 / (frequency[index] * 2); // Period in us. 1/f * 1/2
  activePulseCount[index] = pulseCount[index];
  // Timer alarm toggling pin at period interval gives frequency equal to register value (50%)
  timerAlarmWrite(timers[index], period, true);

  return period;
}

void startTimer(int index)
{
  // Check valid timer
  if (index >= 0 && index <3 && frequency[index] >0 )
  {
    int period = updateTimer(index);
    enablePWM[index] = true;
    timerAlarmEnable(timers[index]);

    // Acknowledge that timer is running now
    timersRunning[index] = true;
    modbusTCPServer.coilWrite(addrRunning[index], timersRunning[index]);

    Serial.printf("Started timer %d with frequency/period %d/%d\n", index, frequency[index], period);
  }
}

void startAllTimers()
{
  Serial.println("Starting all timers.");
  for (int i=0; i<3; i++)
  {
    Serial.printf("Starting timer %d, ", i);
    startTimer(i);
  }
}

// Stop a single timer. enable flag is false, disable, write low, and target becomes 0
void stopTimer(int index)
{
  Serial.printf("Stopping timer %d\n", index);
  enablePWM[index] = false;
  timerAlarmDisable(timers[index]);
  digitalWrite(pwmPins[index], LOW);
  pulseCount[index] = 0;
  // Acknowledge that timer is no longer running
  timersRunning[index] = false;
  modbusTCPServer.coilWrite(addrRunning[index], timersRunning[index]);
}

void stopAllTimers()
{
  Serial.println("Stopping all timers.");
  for (int i=0; i<3; i++)
  {
    stopTimer(i);
  }
}

void modbusTask(void *pvParameters)
{
  WiFiServer server(MODBUS_TCP_PORT);
  server.begin();

  while (1)
  {
    if (eth_connected)
    {
      // Identify any available clients
      WiFiClient client = server.available();

      if (client)
      {
        DEBUG_PRINT("New client connected");
        modbusTCPServer.accept(client);

        // Client connection is maintained - only one thing can be connected at a time
        while (client.connected())
        {
          int ret = modbusTCPServer.poll();

          // Ensure registers are not accessed while being written to
          xSemaphoreTake(pwmMutex, portMAX_DELAY);

          // Update frequency registers and pulse targets
          for (int i=0; i<3; i++)
          {
            bool isRunning = timersRunning[i];
            uint32_t newFreq = combineHoldingRegisters(&modbusTCPServer, addrIntvl[i]);
            if (newFreq > 0 && newFreq != frequency[i]) // Avoiding division by 0 errors when calculating period
            {
              // Avoid unexpected results by stopping timer before updating parameters
              if (isRunning) { stopTimer(i); }
              frequency[i] = newFreq;
              // Start timer calls updateTimer
              if (isRunning) { startTimer(i); }
            }

            uint32_t newPulse = combineHoldingRegisters(&modbusTCPServer, addrTarget[i]);
            if (newPulse != pulseCount[i])
            {
              if (isRunning) { stopTimer(i); }
              pulseCount[i] = newPulse;
              if (isRunning) { startTimer(i); }
            }
          }

          // Check coils and reset after reading them
          if (modbusTCPServer.coilRead(TRIG_ENABLE_COIL))
          {
            startAllTimers();
            modbusTCPServer.coilWrite(TRIG_ENABLE_COIL, false);
          }
          else if (modbusTCPServer.coilRead(TRIG_DISABLE_COIL))
          {
            stopAllTimers();
            modbusTCPServer.coilWrite(TRIG_DISABLE_COIL, false);
          }

          // Enable or disable for individual timers
          for (int i = 0; i < 3; i++)
          {
            if (modbusTCPServer.coilRead(addrEnable[i]))
            {
              startTimer(i);
              modbusTCPServer.coilWrite(addrEnable[i], false);
            }
            else if (modbusTCPServer.coilRead(addrDisable[i]))
            {
              stopTimer(i);
              modbusTCPServer.coilWrite(addrDisable[i], false);
            }
          }
          // Return access for fast loop
          xSemaphoreGive(pwmMutex);

          vTaskDelay(10);
        }
        DEBUG_PRINT("Client disconnected");
      }
    }
    vTaskDelay(10);
  }
}