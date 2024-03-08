#include <Ethernet.h>
#include <SPI.h>
#include <WiFi.h>
#include <ArduinoRS485.h>
#include <ArduinoModbus.h>
#include <cmath>
#include <esp32-hal-timer.h>
#include <driver/timer.h>

#include <ExpandedGpio.h>
#include "pins_is.h"
#include "initialise.h"
#include "config.h"
#include "pidController.h"
#include "modbusServerController.h"
#include "buffer.h"

#include <Adafruit_I2CDevice.h>
#include <Adafruit_I2CRegister.h>
#include "Adafruit_MCP9600.h"
#include <PID_v1.h>

static bool eth_connected = false;

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

byte mac[] = { 0x10, 0x97, 0xbd, 0xca, 0xea, 0x14 };
byte ip[] = { 192, 168, 0, 159 };
byte gateway[] = { 192, 168, 0, 1 };
byte subnet[] = { 255, 255, 255, 0 };

EthernetClient modbusClient;
EthernetClient streamClient;

// Timers setup
float counter = 1;
long int tDequeue = millis(); // Timer for buffer dequeue
long int tPID = millis(); // Timer for PID
long int tModifiers = millis(); // Timer for gradient update
long int tMotor = millis(); // Auto set point control
long int connectionTimer;
bool acquiringFlag = false;

// MCP9600 setup
Adafruit_MCP9600 mcp[] = {Adafruit_MCP9600(), Adafruit_MCP9600()};
const unsigned int num_mcp = sizeof(mcp) / sizeof(mcp[0]);
const uint8_t mcp_addr[] = {0x60, 0x67};

long int tRead = millis(); // Timer for thermocouple reading
float thermoReadings[2] = { 1, 1 };
int num_thermoReadings = sizeof(thermoReadings) / sizeof(thermoReadings[0]);

// Functions for reference later
void Core0PIDTask(void * pvParameters);

hw_timer_t *pidFlagTimer = NULL;
hw_timer_t *secondaryFlagTimer = NULL;
hw_timer_t *camPinToggleTimer = NULL;

volatile bool pidFlag = false;
volatile bool secondaryFlag = false;
volatile bool camToggleFlag = false;
volatile bool camPinToggle = false;

void IRAM_ATTR pidFlagOnTimer()
{
  pidFlag = true;
}

void IRAM_ATTR secondaryFlagOnTimer()
{
  secondaryFlag = true;
}

void IRAM_ATTR camPinToggleOnTimer()
{
  camToggleFlag = true;
}

// Initialise wires, devices, and Modbus/gpio
void setup()
{
  pidFlagTimer = timerBegin(0, 80, true); // timer number (0-3),prescaler (80MHz), count up (true/false)
  timerAttachInterrupt(pidFlagTimer, &pidFlagOnTimer, true); // timer, ISR (interrupting function), edge (?)
  timerAlarmWrite(pidFlagTimer, TIMER_PID, true); // timer, time in μs, reload (true) for periodic
  timerAlarmEnable(pidFlagTimer); // guess

  secondaryFlagTimer = timerBegin(1, 80, true);
  timerAttachInterrupt(secondaryFlagTimer, &secondaryFlagOnTimer, true);
  timerAlarmWrite(secondaryFlagTimer, TIMER_SECONDARY, true);
  timerAlarmEnable(secondaryFlagTimer);

  camPinToggleTimer = timerBegin(3, 80, true);
  timerAttachInterrupt(camPinToggleTimer, &camPinToggleOnTimer, true);
  timerAlarmWrite(camPinToggleTimer, TIMER_CAM_PIN, false);

  Serial.begin(9600);
  delay(2000); // Serial requires a moment to be ready

  // I2C initialisation to ensure it is established before I2C calls made
  Wire.begin();

  // initialise.cpp
  initialiseEthernet(modbusEthServer, mac, ip, PIN_SPI_SS_ETHERNET_LIB);
  tcpEthServer.begin();
  initialiseThermocouples(mcp, num_mcp, mcp_addr);
  modbus_server.initialiseModbus();
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

// Read two MCP9600 thermocouples
void readThermoCouples()
{
  // Read hot junction from each mcp
  for (int idx = 0; idx < num_mcp; idx++)
  {
    thermoReadings[idx] = mcp[idx].readThermocouple();

    if (DEBUG)
    {
      Serial.print((String)"Thermocouple reading (" + idx + "): ");
      Serial.println(thermoReadings[idx]);
    }
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
  // Serial.println(counter);
}

// Thermal gradient is based off of midpoint of heater setpoints and overrides them
void thermalGradient()
{
  // Get temperature (K) per mm
  float wanted = modbus_server.combineHoldingRegisters(MOD_GRADIENT_WANTED_HOLD);
  // Get distance (mm)
  float distance = modbus_server.combineHoldingRegisters(MOD_GRADIENT_DISTANCE_HOLD);
  // Theoretical temperature gradient (k/mm * mm = k)
  float theoretical = wanted * distance;
  float gradientModifier = theoretical/2;

  // Calculate midpoint and 
  float setPointA = modbus_server.combineHoldingRegisters(MOD_SETPOINT_A_HOLD);
  float setPointB = modbus_server.combineHoldingRegisters(MOD_SETPOINT_B_HOLD);
  float midpoint = (setPointA + setPointB) / 2.0;

  float signA, signB;

  // High heater is A (0) or B (1)?
  bool high = modbus_server.coilRead(MOD_GRADIENT_HIGH_COIL);

  if (!high)  // 0 = A = false
  {
    signA = 1.0;
    signB = -1.0;
  }
  else if (high)  // 1 = B = true
  {
    signA = -1.0;
    signB = 1.0;
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

  if (DEBUG)
  {
    Serial.print("gradient midpoint: ");
    Serial.println(midpoint);
    Serial.print("gradient modifier: ");
    Serial.println(gradientModifier);
  }
}

// Increment setPoint by an average rate per second
void autoSetPointControl()
{
  // Get rate
  float rate = modbus_server.combineHoldingRegisters(MOD_AUTOSP_RATE_HOLD);

  // Heating (1) or cooling (0)?
  bool heating = modbus_server.coilRead(MOD_AUTOSP_HEATING_COIL);

  if (!heating)
  { 
    // Rate should be a positive value with 'direction' determined by heating option
    rate = -rate;
  }

  // Rate is average K/s, but value depends on PID interval
  rate = rate * (static_cast<float>(INTERVAL_PID)/1000); // e.g.: 0.5 * 20/1000 = 0.01 = 50 times per second
  PID_A.autospRate = rate;
  PID_B.autospRate = rate;

  // Get img per degree
  float imgPerDegree = modbus_server.combineHoldingRegisters(MOD_AUTOSP_IMGDEGREE_HOLD);

  // Calculate midpoint. Fabs in case B is higher temp
  float midpoint = fabs((PID_A.input + PID_B.input) / 2);
  modbus_server.floatToInputRegisters(MOD_AUTOSP_MIDPT_INP, midpoint);

  if (DEBUG)
  {
    Serial.print("Autosp rate: ");
    Serial.print(rate);
    Serial.print(" | interval: ");
    Serial.print(INTERVAL_PID/1000);
  }
}

// Run a specified PID (A or B) then apply gradient, ASPC, new PID terms, etc.
void runPID(String pid)
{
  PIDController* PID = nullptr;
  PIDAddresses addr;
  // Identify which PID
  if (pid == "A")
  {
    PID = &PID_A;
    addr = pidA_addr;
  } else if (pid == "B")
  {
    PID = &PID_B;
    addr = pidB_addr;
  } else
  {
    Serial.println("Improper PID run call, no PID specified.");
    return;
  }

  if (PID != nullptr)
  {
    // Check PID enabled
    if (modbus_server.readBool(addr.modPidEnableCoil)){
      // Check PID tunings
      double newKp = double(modbus_server.combineHoldingRegisters(addr.modKpHold));
      double newKi = double(modbus_server.combineHoldingRegisters(addr.modKiHold));
      double newKd = double(modbus_server.combineHoldingRegisters(addr.modKdHold));
      PID->check_PID_tunings(newKp, newKi, newKd);

      // Check thermal gradient enable status and use setpoint accordingly
      if (modbus_server.readBool(MOD_GRADIENT_ENABLE_COIL))
      {
        PID->setPoint = PID->gradientSetPoint;
      }
      else
      {
        PID->setPoint = modbus_server.combineHoldingRegisters(addr.modSetPointHold);
      }

      // Calculate PID output
      PID->run();

      // Write PID output
      modbus_server.floatToInputRegisters(addr.modPidOutputInp, PID->output);

      if (INVERT_OUTPUT_SIGNAL)
      {
        float inv_output = PID_OUTPUT_LIMIT - PID->output;
        gpio.analogWrite(addr.outputPin, inv_output);
      }
      else
      {
        gpio.analogWrite(addr.outputPin, PID->output);
      }

      // Check autosp enable status. If enabled, add rate to setpoint via holding register
      if (modbus_server.readBool(MOD_AUTOSP_ENABLE_COIL))
      {
        modbus_server.floatToHoldingRegisters(addr.modSetPointHold, (PID->setPoint + PID->autospRate));
      }
    }
  }
  else
  {
    gpio.analogWrite(addr.outputPin, 0);
  }
}

void loop()
{
  if(modbusClient.connected()) // check for existing connection...
  {
    modbus_server.poll();
    connectionTimer = millis();
  }
  else // ...check for new ones if not.
  {
    modbusClient = modbusEthServer.available();
    if (modbusClient){
      modbus_server.accept(modbusClient);
    }
  }

  if(streamClient.connected()) // check first, then poll
  {
    char c = streamClient.read();
    // Serial.print(".");

    // Dequeue object, if its not a nullptr, write its data out
    BufferObject* dequeued = buffer.dequeue();
    if (dequeued != nullptr)
    {
      tcpEthServer.write((uint8_t*)dequeued, sizeof(BufferObject));
    }
  }
  else
  {
    streamClient = tcpEthServer.available();
  }

  // Disable heaters if no connection for 30 seconds. Checked only if no current connection.
  long int elapsedTime = millis() - connectionTimer;
  if (elapsedTime > INTERVAL_TIMEOUT)
  {
    Serial.println("Timeout: no connection. Disabling PID behaviour (write 0).");
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
    if (pidFlag)
    {
      // Write pin to high and start timer to write it low
      gpio.digitalWrite(Q1_0, HIGH);
      if (!timerAlarmEnabled(camPinToggleTimer))
      {
        // Restart resets counter, otherwise timer fires immediately on 2nd+ enables
        timerRestart(camPinToggleTimer);
        timerAlarmEnable(camPinToggleTimer);
      }

      // Get thermocouple readings for input
      PID_A.input = mcp[0].readThermocouple(); // First thermocouple for A
      PID_B.input = mcp[1].readThermocouple(); // Second thermocouple for B

      // Write thermocouple output to modbus registers
      modbus_server.floatToInputRegisters(MOD_THERMOCOUPLE_A_INP, PID_A.input);
      modbus_server.floatToInputRegisters(MOD_THERMOCOUPLE_B_INP, PID_B.input);
      modbus_server.floatToInputRegisters(MOD_COUNTER_INP, counter);
      counter = counter +1;

      // Create a buffer object, add selected attributes, add it to the buffer if not full
      if (modbus_server.coilRead(MOD_ACQUISITION_COIL))
      {
        // Reset counter if we haven't already done so
        if (!acquiringFlag)
        {
          counter = 1;
          acquiringFlag = true;
        }
        // Construct object
        BufferObject obj;
        obj.counter = counter;
        obj.temperatureA = PID_A.input;
        obj.temperatureB = PID_B.input;

        // Queue only if there is room in the buffer
        if (buffer.isFull())
        {
          // Serial.print(".");
        }
        else
        {
          buffer.enqueue(&obj);
        }
      }
      else
      {
        // Counter will be set to 1 when starting acquisition
        acquiringFlag = false;
      }

      runPID("A");
      runPID("B");

      // Set flag back to false for timer
      pidFlag=false;
    }

    if (secondaryFlag)
    {
      // Thermal modifiers
      thermalGradient();
      autoSetPointControl();

      // Motor control (if enabled)
      if (modbus_server.readBool(MOD_MOTOR_ENABLE_COIL))
      {
        bool direction = modbus_server.readBool(MOD_MOTOR_DIRECTION_COIL);
        direction *= 4095; // Either 4095 (max out) or 0 (no out)

        float speed = modbus_server.combineHoldingRegisters(MOD_MOTOR_SPEED_HOLD); // exactly how this is calculated is TBC

        // analogWrite does PWM
        gpio.digitalWrite(PIN_MOTOR_DIRECTION, direction);
        gpio.analogWrite(PIN_MOTOR_PWM, speed);
      }
      else
      {
        // Write 0 (no motor) if motor control disabled
        gpio.analogWrite(PIN_MOTOR_PWM, 0);
      }

      // Always read LVDT regardless of motor enable
      float lvdt = gpio.analogRead(I0_7);

      // No obvious conversion formula, but readings of values at positions are known.
      // Max height is at ~1700, minimum at ~200, total range of 9.5mm.
      // This covers a range of 7.28V by current positioning of LVDT.
      float position = (1700 -(lvdt)) * (9.5 / 1500); // mm/mV

      modbus_server.floatToInputRegisters(MOD_MOTOR_LVDT_INP, position);

      secondaryFlag = false;
    }
  
    if (camToggleFlag)
    {
      gpio.digitalWrite(Q1_0, LOW);
      camToggleFlag = false;
    }
  }
}