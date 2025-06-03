#ifndef CONFIG_H
#define CONFIG_H

// #define DEBUG_MODE true

#define MODBUS_TCP_PORT 502

#define NUM_TRIGGERS 3

#define PIN_TRIGGER_0 33
#define PIN_TRIGGER_1 32
#define PIN_TRIGGER_2 16
#define PIN_TRIGGER_3 15

// Modbus config options
#define TRIG_NUM_COIL 16
#define TRIG_NUM_HOLD 16

// Modbus addresses
// For enabling and disabling all coils
#define TRIG_ENABLE_COIL 0
#define TRIG_DISABLE_COIL 1
// Single-fire 'turn this on' coil
#define TRIG_0_ENABLE_COIL 2
#define TRIG_1_ENABLE_COIL 3
#define TRIG_2_ENABLE_COIL 4
#define TRIG_3_ENABLE_COIL 5
// Single-fire 'turn this off' coil
#define TRIG_0_DISABLE_COIL 6
#define TRIG_1_DISABLE_COIL 7
#define TRIG_2_DISABLE_COIL 8
#define TRIG_3_DISABLE_COIL 9
// 'Is this running?' coil
#define TRIG_0_RUNNING_COIL 10
#define TRIG_1_RUNNING_COIL 11
#define TRIG_2_RUNNING_COIL 12
#define TRIG_3_RUNNING_COIL 13
// Frequency holding registers
#define TRIG_0_INTVL_HOLD 40001
#define TRIG_1_INTVL_HOLD 40003
#define TRIG_2_INTVL_HOLD 40005
#define TRIG_3_INTVL_HOLD 40007
// Frame target holding registers
#define TRIG_0_TARGET_HOLD 40009
#define TRIG_1_TARGET_HOLD 40011
#define TRIG_2_TARGET_HOLD 40013
#define TRIG_3_TARGET_HOLD 40015

#endif