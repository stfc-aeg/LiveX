#ifndef __EXPANDED_GPIO_H__
#define __EXPANDED_GPIO_H__

#include <Arduino.h>
#include <stdint.h>

#include "pins_is.h"

class ExpandedGpio {
public:
    ExpandedGpio() { };
    void init(void);
    void pinMode(uint32_t pin, uint8_t mode);
    void digitalWrite(uint32_t pin, uint8_t value);
    int digitalRead(uint32_t pin);
    void analogWrite(uint32_t pin, uint16_t value);
    uint16_t analogRead(uint32_t pin);
};

// #ifdef __cplusplus
// extern "C" {
// #endif

// void initExpandedGpio();

// //void analogWrite(uint32_t pin, uint16_t value);

// #ifdef __cplusplus
// }
// #endif

#endif
