#include <taskComms.h>

// Check and poll connections. If no clients for 30 seconds, 'time out' and write 0 for PID/heating.
void manageComms()
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
