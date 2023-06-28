#include "devices.h"

void initialiseThermocouples(Adafruit_MCP9600* mcp, int num_mcp, const uint8_t* mcp_addr)
{
  // Run the MCP9600 default setup code. Find devices and set defaults

  // Initialise MCP9600(s)
  Serial.println("nano_mcp9600 startup");

  for (int idx = 0; idx < num_mcp; idx++)
  {
    Serial.println("\nNow considering new device.");

    // Find sensor
    if (!mcp[idx].begin(mcp_addr[idx])) {
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

    mcp[idx].setFilterCoefficient(3);
    Serial.print("Filter coefficient value set to: ");
    Serial.println(mcp[idx].getFilterCoefficient());

    mcp[idx].setAlertTemperature(1, 30);
    Serial.print("Alert #1 temperature set to ");
    Serial.println(mcp[idx].getAlertTemperature(1));
    mcp[idx].configureAlert(1, true, true);  // alert 1 enabled, rising temp

    mcp[idx].enable(true);
    Serial.print("enabled");
  }
}
