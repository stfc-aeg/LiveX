#include "initialise.h"

// Initialise timers for pid, for secondary devices, and setting camera to low (enabled by pid)
void initialiseInterrupts(hw_timer_t** pidFlagTimer)
{
  if (USE_EXTERNAL_INTERRUPT)
  {
    // Configure interrupt for PID
    pinMode(PIN_TRIGGER_INTERRUPT, INPUT);
    attachInterrupt(digitalPinToInterrupt(PIN_TRIGGER_INTERRUPT), pidInterrupt, CHANGE);
  }
  else
  {
    // Timer for pid mechanisms if no external interrupt
    *pidFlagTimer = timerBegin(0, 80, true);
    timerAttachInterrupt(*pidFlagTimer, &pidFlagOnTimer, true);
    timerAlarmWrite(*pidFlagTimer, TIMER_PID, true);
    timerAlarmEnable(*pidFlagTimer);
  }
}

// Run the MCP9600 default setup code. Find devices and set defaults
void initialiseThermocouples(Adafruit_MCP9600* mcp, int num_mcp, const uint8_t* mcp_addr)
{
  // Initialise MCP9600(s)
  Serial.println("mcp9600 startup");

  for (int idx = 0; idx < num_mcp; idx++)
  {
    Serial.println("\nNow considering new device.");

    // Find sensor
    if (!mcp[idx].begin(mcp_addr[idx])) 
    {
      Serial.print("Sensor not found at address 0x");
      Serial.print(mcp_addr[idx], 16);
      Serial.println("Check wiring!");
      delay(1000);
      while(1);
    }
    Serial.print("Found MCP9600 at address 0x");
    Serial.println(mcp_addr[idx], 16);

    // Set ADC resolution
    mcp[idx].setADCresolution(MCP9600_ADCRESOLUTION_18);
    Serial.print("ADC resolution set to ");
    switch(mcp[idx].getADCresolution())
    {
      case MCP9600_ADCRESOLUTION_18:   Serial.print("18"); break;
      case MCP9600_ADCRESOLUTION_16:   Serial.print("16"); break;
      case MCP9600_ADCRESOLUTION_14:   Serial.print("14"); break;
      case MCP9600_ADCRESOLUTION_12:   Serial.print("12"); break;
    }
    Serial.println(" bits");

    // Set thermocouple type (K: -200 to 1372 degrees C)
    mcp[idx].setThermocoupleType(MCP9600_TYPE_K);
    Serial.print("Thermocouple type set to ");
    switch (mcp[idx].getThermocoupleType())
    {
      case MCP9600_TYPE_K:  Serial.print("K"); break;
      case MCP9600_TYPE_J:  Serial.print("J"); break;
      case MCP9600_TYPE_T:  Serial.print("T"); break;
      case MCP9600_TYPE_N:  Serial.print("N"); break;
      case MCP9600_TYPE_S:  Serial.print("S"); break;
      case MCP9600_TYPE_E:  Serial.print("E"); break;
      case MCP9600_TYPE_B:  Serial.print("B"); break;
      case MCP9600_TYPE_R:  Serial.print("R"); break;
    }
    Serial.println(" type");

    mcp[idx].setFilterCoefficient(3);  // Filter coefficient averages readings... speed things up by doing just one? It includes 0...
    Serial.print("Filter coefficient value set to: ");
    Serial.println(mcp[idx].getFilterCoefficient());

    mcp[idx].setAlertTemperature(1, 30);
    Serial.print("Alert #1 temperature set to ");
    Serial.println(mcp[idx].getAlertTemperature(1));
    mcp[idx].configureAlert(1, true, true);  // alert 1 enabled, rising temp

    mcp[idx].enable(true);
    Serial.println("Enabled");
  }
}

  // This function initialises Ethernet/ethServer and checks for hardware
void initialiseEthernet(EthernetServer ethServer, byte* mac, byte* ip, int ethPin)
{
  // IS ESP32 module has Ethernet SPI CS on pin 15
  Ethernet.init(ethPin);
  // Start the Ethernet connection and the server
  Ethernet.begin(mac, ip);
  ethServer.begin();

  // Check if Ethernet hardware present
  if (Ethernet.hardwareStatus() == EthernetNoHardware) 
  {
    Serial.println("Ethernet shield was not found.  Sorry, can't run without hardware. :(");
    while (true) 
    {
      Serial.print(".");
      delay(1000); // Do nothing, no point running without Ethernet hardware
    }
  }
  if (Ethernet.linkStatus() == LinkOFF) 
  {
    Serial.println("Ethernet cable is not connected.");
  }
}

void writePIDDefaults(ModbusServerController& modbus_server, PIDController PID)
{
      // Write variables to modbus
    // PID requires doubles, modbus works best with floats, so cast
    float pidDefaults_[4] =
    {
        static_cast<float>(PID.setPoint),
        static_cast<float>(PID.Kp),
        static_cast<float>(PID.Ki),
        static_cast<float>(PID.Kd)
    }; 
    int tempAddress = PID.addr_.modSetPointHold;

    // Separate values as only one holding register can be written to at a time
    for (float term : pidDefaults_)
    {
        modbus_server.floatToHoldingRegisters(tempAddress, term);
        tempAddress += 2;
    }

    // Also includes initial frequency, as ASPC depends on it
    modbus_server.floatToHoldingRegisters(MOD_FURNACE_FREQ_HOLD, DEFAULT_INTERRUPT_FREQUENCY);
}
