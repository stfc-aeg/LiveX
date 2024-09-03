#include <Arduino.h>
#include <ETH.h>
#include <ArduinoModbus.h>
#include "esp_eth.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "config.h"
#include "modbusUtils.h"

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
void startTimer(int timerIndex);
void stopAllTimers();

// Global variables
ModbusTCPServer modbusTCPServer;
TaskHandle_t fastLoopTaskHandle;
TaskHandle_t modbusTaskHandle;

SemaphoreHandle_t pwmMutex;

// PWM parameters
uint32_t frequency[3] = {0, 0, 0};
uint32_t pulseCount[3] = {0, 0, 0};
uint32_t timerPulseCount[3] = {0, 0, 0};
bool enablePWM[3] = {false, false, false};

static bool eth_connected = false;
bool startAll = false;
bool stopAll = false;

// New variables for fast loop implementation
const int pwmPins[3] = {PIN_TRIGGER_1, PIN_TRIGGER_2, PIN_TRIGGER_3};
uint32_t cycleCounters[3] = {0, 0, 0};
uint32_t halfPeriods[3] = {0, 0, 0};
bool pinStates[3] = {false, false, false};

// Debug logging macro
#ifdef DEBUG_MODE
#define DEBUG_PRINT(x) Serial.println(x)
#else
#define DEBUG_PRINT(x)
#endif


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
  Serial.begin(115200);

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

  // Create tasks on separate cores
  xTaskCreatePinnedToCore(fastLoopTask, "Fast Loop Task", 4096, NULL, 5, &fastLoopTaskHandle, 0);
  xTaskCreatePinnedToCore(modbusTask, "Modbus Task", 4096, NULL, 5, &modbusTaskHandle, 1);
}

void loop()
{
  // The main loop is empty as we're using FreeRTOS tasks
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

// Start timers and set relevant global attributes
void startTimer(int timerIndex)
{
  if (timerIndex >= 0 && timerIndex < 3)
  {
    enablePWM[timerIndex] = true; // Array of enables
    timerPulseCount[timerIndex] = pulseCount[timerIndex]; // Array of pulse counts
    cycleCounters[timerIndex] = 0; // Array of cycles required from loop to trigger pwm
    pinStates[timerIndex] = true; // Array of pin output states - setting that index to true
    digitalWrite(pwmPins[timerIndex], HIGH); // Write pins to HIGH for synchronisation
    DEBUG_PRINT("Timer " + String(timerIndex + 1) + " started");
  }
}

// Stop all timers and write LOW
void stopAllTimers()
{
  for (int i = 0; i < 3; i++)
  {
    enablePWM[i] = false;
    digitalWrite(pwmPins[i], LOW);
    timerPulseCount[i] = 0; // Reset pulse count
  }
  DEBUG_PRINT("All timers stopped");
}

// Task that repeatedly checks timers and writes pin values accordingly
void fastLoopTask(void *pvParameters)
{
  TickType_t xLastWakeTime; // Time function is awoken
  const TickType_t xPeriod = pdMS_TO_TICKS(1); // 1000Hz = 1ms period
  xLastWakeTime = xTaskGetTickCount();

  while (1)
  {
    // Exclusive register access
    xSemaphoreTake(pwmMutex, portMAX_DELAY);

    // Start all if requested
    if (startAll)
    {
      DEBUG_PRINT("Starting all PWM channels simultaneously");
      for (int i = 0; i < 3; i++) {
        if (frequency[i] > 0) {
          startTimer(i);
        }
      }
      startAll = false;
    }

    // Stop all if requested
    if (stopAll)
    {
      stopAllTimers();
      stopAll = false;
    }

    // Always: increase cycles, if cycle meets half period (for rise+fall), toggle pin
    // then increase count on falling edge. At target pulse count, disable pin.
    for (int i = 0; i < 3; i++)
    {
      if (enablePWM[i]) // Check if given trigger is enabled
      {
        cycleCounters[i]++;

        // Toggle pin at twice the frequency
        if (cycleCounters[i] >= halfPeriods[i])
        { // Toggle state, write that state, reset cycle counter
          pinStates[i] = !pinStates[i];
          digitalWrite(pwmPins[i], pinStates[i]);
          cycleCounters[i] = 0;

          if (timerPulseCount[i] > 0)
          {
            if (!pinStates[i])
            { // Count (down) on falling edge
              timerPulseCount[i]--;
              if (timerPulseCount[i] == 0)
              {
                enablePWM[i] = false;
                digitalWrite(pwmPins[i], LOW);
                DEBUG_PRINT("PWM " + String(i) + " stopped (pulse count reached zero)");
              }
            }
          }
        }
      } else // If it's not enabled, write LOW
      {
        digitalWrite(pwmPins[i], LOW);
      }
    }
    // Return access and delay task by period
    xSemaphoreGive(pwmMutex);
    vTaskDelayUntil(&xLastWakeTime, xPeriod);
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

          if (ret) {

          }
          // Ensure registers are not accessed while being written to
          xSemaphoreTake(pwmMutex, portMAX_DELAY);

          // Update frequency registers
          for (int i = 0; i < 3; i++)
          {
            uint32_t newFreq = combineHoldingRegisters(&modbusTCPServer, TRIG_FURNACE_INTVL_HOLD+ (i * 2));
            if (newFreq > 0)
            {
              frequency[i] = newFreq;
              halfPeriods[i] = 500 / frequency[i];
            }
          }

          // Update pulse count registers
          for (int i = 0; i < 3; i++)
          {
            pulseCount[i] = combineHoldingRegisters(&modbusTCPServer, TRIG_FURNACE_TARGET_HOLD + (i * 2))
            DEBUG_PRINT("Pulse count " + String(i) + " updated to " + String(pulseCount[i]));
          }

          // Check coils and reset after reading them
          startAll = modbusTCPServer.coilRead(TRIG_ENABLE_COIL);
          modbusTCPServer.coilWrite(TRIG_ENABLE_COIL, false);

          stopAll = modbusTCPServer.coilRead(TRIG_DISABLE_COIL);
          modbusTCPServer.coilWrite(TRIG_DISABLE_COIL, false);

          // Enable for individual timers
          for (int i = 0; i < 3; i++)
          {
            if (modbusTCPServer.coilRead(TRIG_FURNACE_ENABLE_COIL + i))
            {
              startTimer(i);
              modbusTCPServer.coilWrite(TRIG_FURNACE_ENABLE_COIL + i, false);
            }
          }
          // Return access for fast loop
          xSemaphoreGive(pwmMutex);

          vTaskDelay(1);
        }
        DEBUG_PRINT("Client disconnected");
      }
    }
    vTaskDelay(10);
  }
}