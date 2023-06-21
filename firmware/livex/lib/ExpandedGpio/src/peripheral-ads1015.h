#ifndef __PERIPHERAL_ADS1015_H__
#define __PERIPHERAL_ADS1015_H__

#include "Arduino.h"
#include "esp32-hal-i2c.h"

#ifdef __cplusplus
extern "C" {
#endif

bool ads1015_init(uint8_t i2cNum, uint8_t addr);
uint16_t ads1015_get_input(uint8_t i2cNum, uint8_t addr, uint8_t index);

#ifdef __cplusplus
}
#endif


#endif
