#ifndef CONFIG_H
#define CONFIG_H

// #define DEBUG_MODE false

#define MODBUS_TCP_PORT 502

#define PIN_TRIGGER_1 33
#define PIN_TRIGGER_2 32
#define PIN_TRIGGER_3 16
#define PIN_TRIGGER_4 15

// Modbus config options
#define TRIG_NUM_COIL 12
#define TRIG_NUM_HOLD 16

// Modbus addresses
// For enabling and disabling all coils
#define TRIG_ENABLE_COIL 0
#define TRIG_DISABLE_COIL 1
// Single-fire 'turn this on' coil
#define TRIG_FURNACE_ENABLE_COIL 2
#define TRIG_WIDEFOV_ENABLE_COIL 3
#define TRIG_NARROWFOV_ENABLE_COIL 4
// Single-fire 'turn this off' coil
#define TRIG_FURNACE_DISABLE_COIL 5
#define TRIG_WIDEFOV_DISABLE_COIL 6
#define TRIG_NARROWFOV_DISABLE_COIL 7
// 'Is this running?' coil
#define TRIG_FURNACE_RUNNING_COIL 8
#define TRIG_WIDEFOV_RUNNING_COIL 9
#define TRIG_NARROWFOV_RUNNING_COIL 10

#define TRIG_FURNACE_INTVL_HOLD 40001
#define TRIG_WIDEFOV_INTVL_HOLD 40003
#define TRIG_NARROWFOV_INTVL_HOLD 40005

#define TRIG_FURNACE_TARGET_HOLD 40007
#define TRIG_WIDEFOV_TARGET_HOLD 40009
#define TRIG_NARROWFOV_TARGET_HOLD 40011

#endif