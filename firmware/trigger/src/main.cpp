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
void updateTimer(int index);

void IRAM_ATTR onTimer0();
void IRAM_ATTR onTimer1();
void IRAM_ATTR onTimer2();
void IRAM_ATTR onTimer3();
void IRAM_ATTR handleInterrupt(int index);

// Global variables
ModbusTCPServer modbusTCPServer;
TaskHandle_t fastLoopTaskHandle;
TaskHandle_t modbusTaskHandle;

SemaphoreHandle_t pwmMutex;

// PWM parameters
float frequency[4] = {0, 0, 0, 0};
uint32_t pulseCount[4] = {0, 0, 0, 0}; // Target # of instances
volatile uint32_t activePulseCount[4] = {0, 0, 0, 0}; // For use in interrupts, enables restart logic
volatile bool enablePWM[4] = {false, false, false, false};
bool timersRunning[4] = {false, false, false, false};
volatile bool timerComplete[4] = {false, false, false, false};

static bool eth_connected = false;
bool startAll = false;
bool stopAll = false;

// GPIO and timer variables
const int pwmPins[4] = {PIN_TRIGGER_0, PIN_TRIGGER_1, PIN_TRIGGER_2, PIN_TRIGGER_3};
volatile bool pinStates[4] = {false, false, false, false};
hw_timer_t *timers[4] = {nullptr, nullptr, nullptr, nullptr};

// For more readable address referencing
int addrEnable[4] = {TRIG_0_ENABLE_COIL, TRIG_1_ENABLE_COIL, TRIG_2_ENABLE_COIL, TRIG_3_ENABLE_COIL};
int addrDisable[4] = {TRIG_0_DISABLE_COIL, TRIG_1_DISABLE_COIL, TRIG_2_DISABLE_COIL, TRIG_3_DISABLE_COIL};
int addrRunning[4] = {TRIG_0_RUNNING_COIL, TRIG_1_RUNNING_COIL, TRIG_2_RUNNING_COIL, TRIG_3_RUNNING_COIL};
int addrIntvl[4] = {TRIG_0_INTVL_HOLD, TRIG_1_INTVL_HOLD, TRIG_2_INTVL_HOLD, TRIG_3_INTVL_HOLD};
int addrTarget[4] = {TRIG_0_TARGET_HOLD, TRIG_1_TARGET_HOLD, TRIG_2_TARGET_HOLD, TRIG_3_TARGET_HOLD};

volatile int counter = 0;

// Debug logging macro
#ifdef DEBUG_MODE
#define DEBUG_PRINT(x) Serial.println(x)
#define DEBUG_PRINTF(...) Serial.printf(__VA_ARGS__)
#else
#define DEBUG_PRINT(x)
#define DEBUG_PRINTF(...)
#endif


void IRAM_ATTR handleInterrupt(int i)
{
  if (i<0 || i>=NUM_TRIGGERS) { return; }  // Sanity check
  if (!enablePWM[i]) { return; }  // Only run any code if the timer is enabled

  counter++;
  pinStates[i] = !pinStates[i];
  digitalWrite(pwmPins[i], pinStates[i]);

  // Count down on falling edge provided the target is higher than 0 (target 0 is freerun)
  if (!pinStates[i] && activePulseCount[i] > 0)
  {
    activePulseCount[i]--;
    // at 0, disable PWM
    if (activePulseCount[i] <= 0)
    {
      enablePWM[i] = false;
      pinStates[i] = false;  // Reset pin
      digitalWrite(pwmPins[i], pinStates[i]);
      timerAlarmDisable(timers[i]);
      timerComplete[i] = true;  // Flag to handle timer stop in main loop
    }
  }
}

void IRAM_ATTR onTimer0() { handleInterrupt(0); }
void IRAM_ATTR onTimer1() { handleInterrupt(1); }
void IRAM_ATTR onTimer2() { handleInterrupt(2); }
void IRAM_ATTR onTimer3() { handleInterrupt(3); }

// Establish connection details
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

// Setup function, begin ethernet, gpio pins, modbus, and timers
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
  for (int i=0; i<NUM_TRIGGERS; i++)
  {
    timers[i] = timerBegin(i, 80, true); // Timer number, prescaler (80MHz), count up
    if (timers[i]){ DEBUG_PRINTF("Timer %d started successfully.", i); }
    switch (i)
    {
    case 0:
      timerAttachInterrupt(timers[0], &onTimer0, true);
      break;
    case 1:
      timerAttachInterrupt(timers[1], &onTimer1, true);
      break;
    case 2:
      timerAttachInterrupt(timers[2], &onTimer2, true);
      break;
    case 3:
      timerAttachInterrupt(timers[3], &onTimer3, true);
    default:
      break;
    }
  }

  // Create tasks on separate cores
  // xTaskCreatePinnedToCore(fastLoopTask, "Fast Loop Task", 4096, NULL, 5, &fastLoopTaskHandle, 0);
  xTaskCreatePinnedToCore(modbusTask, "Modbus Task", 4096, NULL, 5, &modbusTaskHandle, 1);
}

// Main loop, tasks are delegated to core 1 for this application
void loop()
{
  // Tasks handle everything
  DEBUG_PRINTF("%d, ", counter);
  for (int i=0; i<NUM_TRIGGERS; i++)
  {
    if (timerComplete[i])
    {
      timerComplete[i] = false;  // Reset the flag
      stopTimer(i);
      DEBUG_PRINTF("Timer %d completed.\n", i);
    }
  }
  vTaskDelay(1000);
}

// Set GPIO pins
void setupGPIO()
{
  for (int i=0; i<NUM_TRIGGERS; i++)
  {
    pinMode(pwmPins[i], OUTPUT);
    digitalWrite(pwmPins[i], LOW);
  }
}

// Start server and configure registers
void setupModbus()
{
  modbusTCPServer.begin();
  modbusTCPServer.configureHoldingRegisters(TRIG_0_INTVL_HOLD, TRIG_NUM_HOLD);
  modbusTCPServer.configureCoils(TRIG_ENABLE_COIL, TRIG_NUM_COIL);
}

// Calculate and write timer period, update pulseCount for running timer
void updateTimer(int index)
{
  uint32_t period = (uint32_t)(1000000.0f / (frequency[index]*2)); // Period in us. 1/f * 1/2
  activePulseCount[index] = pulseCount[index];
  // Timer alarm toggling pin at period interval gives frequency equal to register value (50%)
  timerAlarmWrite(timers[index], period, true);

  Serial.printf("Timer %d set to frequency/period %d/%d with target %u.\n", index, frequency[index], period, activePulseCount[index]);
}

// Begin specified timer, ensuring it is updated
void startTimer(int index)
{
  // Check valid timer
  if (index >= 0 && index <NUM_TRIGGERS && frequency[index] >0 )
  {
    enablePWM[index] = true;
    timerAlarmEnable(timers[index]);

    // Acknowledge that timer is running now
    timersRunning[index] = true;
    modbusTCPServer.coilWrite(addrRunning[index], timersRunning[index]);

    DEBUG_PRINTF("Started timer %d with frequency %d and target %d\n", index, frequency[index], activePulseCount[index]);
  }
}

// Call startTimer for each of 3 timers
void startAllTimers()
{
  DEBUG_PRINT("Starting all timers.");
  // Not calling startTimer for each to optimise synchronisation
  for (int i=0; i<NUM_TRIGGERS; i++)
  {
    enablePWM[i] = true;
    timerAlarmEnable(timers[i]);
  }
  // Write to all coils afterwards for maximum synchronicity
  for (int i=0; i<NUM_TRIGGERS; i++)
  {
    timersRunning[i] = true;
    modbusTCPServer.coilWrite(addrRunning[i], timersRunning[i]);
  }
}

// Stop a single timer. enable flag is false, disable, write low, and target becomes 0
void stopTimer(int index)
{
  DEBUG_PRINTF("Stopping timer %d\n", index);
  enablePWM[index] = false;
  timerAlarmDisable(timers[index]);
  digitalWrite(pwmPins[index], LOW);
  pulseCount[index] = 0;
  // Acknowledge that timer is no longer running
  timersRunning[index] = false;
  modbusTCPServer.coilWrite(addrRunning[index], timersRunning[index]);
  pinStates[index] = false; // Reset pin state for future runs
}

// Call stopTimer for all of 3 timers
void stopAllTimers()
{
  DEBUG_PRINT("Stopping all timers.");
  for (int i=0; i<NUM_TRIGGERS; i++)
  {
    // Not as concerned about synchronising the stopping of triggers, this is fine
    stopTimer(i);
  }
}

// Establish modbus client connection, check registers for updates to values or start/stop flags
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
          for (int i=0; i<NUM_TRIGGERS; i++)
          {
            bool isRunning = timersRunning[i];
            float newFreq = combineHoldingRegisters(&modbusTCPServer, addrIntvl[i]);
            if (newFreq > 0 && newFreq != frequency[i]) // Avoiding division by 0 errors when calculating period
            {
              // Avoid unexpected results by stopping timer before updating parameters
              if (isRunning) { stopTimer(i); }
              frequency[i] = newFreq;
              updateTimer(i);
              if (isRunning) { startTimer(i); }
            }

            uint32_t newPulse = combineHoldingRegisters(&modbusTCPServer, addrTarget[i]);
            if (newPulse != pulseCount[i])
            {
              if (isRunning) { stopTimer(i); }
              pulseCount[i] = newPulse;
              updateTimer(i);
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
          for (int i=0; i<NUM_TRIGGERS; i++)
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