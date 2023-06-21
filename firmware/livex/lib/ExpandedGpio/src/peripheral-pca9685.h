#ifndef __PERIPHERAL_PCA9685_H__
#define __PERIPHERAL_PCA9685_H__

#include "Arduino.h"
#include "esp32-hal-i2c.h"

#ifdef __cplusplus
extern "C" {
#endif

bool pca9685_init(uint8_t i2cNum, uint8_t addr);
bool pca9685_set_out_on(uint8_t i2cNum, uint8_t addr, uint8_t index);
bool pca9685_set_out_off(uint8_t i2cNum, uint8_t addr, uint8_t index);
bool pca9685_set_out_pwm(uint8_t i2cNum, uint8_t addr, uint8_t index, uint16_t value);

#ifdef __cplusplus
}
#endif


#endif
