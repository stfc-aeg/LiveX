#ifndef __PERIPHERAL_MCP23008_H__
#define __PERIPHERAL_MCP23008_H__

#include "Arduino.h"
#include "esp32-hal-i2c.h"

#ifdef __cplusplus
extern "C" {
#endif

bool mcp23008_init(uint8_t i2cNum, uint8_t addr);
uint8_t mcp23008_set_pin_mode(uint8_t i2cNum, uint8_t addr, uint8_t index, uint8_t mode);
uint8_t mcp23008_get_input(uint8_t i2cNum, uint8_t addr, uint8_t index);
uint8_t mcp23008_set_output(uint8_t i2cNum, uint8_t addr, uint8_t index, uint8_t value);

#ifdef __cplusplus
}
#endif


#endif
