#ifndef CONFIG_H
#define CONFIG_H

#define DEBUG false

// Invert output pid analogwrite signal (does not alter output in UI)
#define INVERT_OUTPUT_SIGNAL false

// true: use external interrupt instead of internal timer
#define USE_EXTERNAL_INTERRUPT true
// true: output total of external interrupts at given range (e.g.: every 100 interrupts. 100, 200, etc.)
#define LOG_INTERRUPTS false
#define LOG_INTERRUPTS_INTERVAL 100

// Intervals
// Speed at which specified function runs in ms
#define INTERVAL_PID 20  // PID iteration
#define INTERVAL_MODIFIERS 500  // Gradient and auto set point control interval
#define INTERVAL_THERMOCOUPLES 1000  // Read extra thermcouples
#define INTERVAL_MOTOR 500
#define INTERVAL_TIMEOUT 30000

#define TIMER_PID 20000
#define TIMER_CAM_PIN 10000
#define TIMER_SECONDARY 200000 // motor and modifiers

// Default terms for PID controllers
#define PID_SETPOINT_DEFAULT 25.5
#define PID_KP_DEFAULT       25.5
#define PID_KI_DEFAULT       5.0
#define PID_KD_DEFAULT       0.1
#define PID_OUTPUT_LIMIT     4095

// Modbus setup/addresses

// Number of each register type
#define MOD_NUM_HOLD 32
#define MOD_NUM_INP 32
#define MOD_NUM_COIL 12

// Register addresses
// coils start at 00001-09999
#define MOD_PID_ENABLE_A_COIL 1
#define MOD_PID_ENABLE_B_COIL 2
#define MOD_GRADIENT_ENABLE_COIL 3
#define MOD_AUTOSP_ENABLE_COIL 4
#define MOD_AUTOSP_HEATING_COIL 5
#define MOD_MOTOR_ENABLE_COIL 6
#define MOD_MOTOR_DIRECTION_COIL 7
#define MOD_GRADIENT_HIGH_COIL 8
#define MOD_ACQUISITION_COIL 9

// input registers start at 30001-39999
#define MOD_COUNTER_INP 30001
#define MOD_PID_OUTPUT_A_INP 30003
#define MOD_PID_OUTPUT_B_INP 30005

#define MOD_THERMOCOUPLE_A_INP 30007
#define MOD_THERMOCOUPLE_B_INP 30009
#define MOD_THERMOCOUPLE_C_INP 30011
#define MOD_THERMOCOUPLE_D_INP 30013

#define MOD_GRADIENT_ACTUAL_INP 30015
#define MOD_GRADIENT_THEORY_INP 30017
#define MOD_GRADIENT_SETPOINT_A_INP 30019
#define MOD_GRADIENT_SETPOINT_B_INP 30021
#define MOD_AUTOSP_MIDPT_INP 30023

#define MOD_MOTOR_LVDT_INP 30027

// holding registers start at 40001-49999
#define MOD_SETPOINT_A_HOLD 40001
#define MOD_KP_A_HOLD 40003
#define MOD_KI_A_HOLD 40005
#define MOD_KD_A_HOLD 40007

#define MOD_SETPOINT_B_HOLD 40009
#define MOD_KP_B_HOLD 40011
#define MOD_KI_B_HOLD 40013
#define MOD_KD_B_HOLD 40015

#define MOD_GRADIENT_WANTED_HOLD 40017
#define MOD_GRADIENT_DISTANCE_HOLD 40019

#define MOD_AUTOSP_RATE_HOLD 40021
#define MOD_AUTOSP_IMGDEGREE_HOLD 40023

#define MOD_MOTOR_SPEED_HOLD 40025

#define PIN_PWM_A A0_5
#define PIN_PWM_B A0_6

#define PIN_TRIGGER_INTERRUPT I0_6

#define PIN_MOTOR_DIRECTION Q1_6
#define PIN_MOTOR_PWM Q1_7
#define PIN_MOTOR_LVDT_IN I0_7

#endif