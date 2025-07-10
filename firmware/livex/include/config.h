#ifndef CONFIG_H
#define CONFIG_H

// DEBUG outputs some internal values to ensure correct sending/calculation
#define DEBUG false
// PID_DEBUG changes the TCP object sent to be PID calculated values
// Ensure that the adapter also has this set, otherwise reading TCP values may throw errors.
#define PID_DEBUG true

// Invert output pid analogwrite signal (does not alter output in UI)
#define INVERT_OUTPUT_SIGNAL false

// true: use external interrupt instead of internal timer
#define USE_EXTERNAL_INTERRUPT true
// true: output total of external interrupts at given range (e.g.: every 100 interrupts. 100, 200, etc.)
#define LOG_INTERRUPTS true
#define LOG_INTERRUPTS_INTERVAL 50

// Timeout (no modbus connection) in ms
#define INTERVAL_TIMEOUT 10000

// For the internal timer. Set to 50Hz here, other rates should be managed via external trigger.
#define TIMER_PID 20000
#define DEFAULT_INTERRUPT_FREQUENCY 10

// Default terms for PID controllers
#define PID_SETPOINT_DEFAULT 25.5
#define PID_KP_DEFAULT       0.3  // From testing, these values seem coherent/safe
#define PID_KI_DEFAULT       0.02
#define PID_KD_DEFAULT       0.0

// MAX # of bits written to relevant power output channel. Min is 0.
#define POWER_OUTPUT_BITS 4095
// Scale the output value (0->1*POWER_OUTPUT_BITS) by a 0.1 value. e.g. 0.8 for 80% output
#define POWER_OUTPUT_SCALE 1
// PID Output is the higher end of the range for this. temporarily moved up here for convenience
#define PID_OUTPUT_LIMIT 100

// Modbus setup/addresses

// Number of each register type
#define MOD_NUM_HOLD 64
#define MOD_NUM_INP 48
#define MOD_NUM_COIL 24

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
#define MOD_GRADIENT_UPDATE_COIL 10
#define MOD_FREQ_ASPC_UPDATE_COIL 11
#define MOD_SETPOINT_UPDATE_COIL 12
// A thermocouple type has been changed
#define MOD_TC_TYPE_UPDATE_COIL 13

// input registers start at 30001-39999
#define MOD_COUNTER_INP 30001
#define MOD_PID_OUTPUT_A_INP 30003
#define MOD_PID_OUTPUT_B_INP 30005
#define MOD_PID_OUTPUTSUM_A_INP 30007
#define MOD_PID_OUTPUTSUM_B_INP 30009

// Thermocouple registers must stay defined sequentially
#define MOD_HEATERTC_A_INP 30011
#define MOD_HEATERTC_B_INP 30013
#define MOD_EXTRATC_A_INP 30015
#define MOD_EXTRATC_B_INP 30017
#define MOD_EXTRATC_C_INP 30019
#define MOD_EXTRATC_D_INP 30021
#define MOD_NUM_MCP_INP 30023

#define MOD_GRADIENT_ACTUAL_INP 30025
#define MOD_GRADIENT_THEORY_INP 30027
#define MOD_AUTOSP_MIDPT_INP 30029

// holding registers start at 40001-49999
#define MOD_SETPOINT_A_HOLD 40001
#define MOD_KP_A_HOLD 40003
#define MOD_KI_A_HOLD 40005
#define MOD_KD_A_HOLD 40007

#define MOD_SETPOINT_B_HOLD 40009
#define MOD_KP_B_HOLD 40011
#define MOD_KI_B_HOLD 40013
#define MOD_KD_B_HOLD 40015

#define MOD_FURNACE_FREQ_HOLD 40017

#define MOD_GRADIENT_WANTED_HOLD 40019
#define MOD_GRADIENT_DISTANCE_HOLD 40021

#define MOD_AUTOSP_RATE_HOLD 40023
#define MOD_AUTOSP_IMGDEGREE_HOLD 40025

// Which thermocouples do the heaters use - thermocouple map to heater
#define MOD_HEATERTC_A_IDX_HOLD 40027
#define MOD_HEATERTC_B_IDX_HOLD 40029
#define MOD_EXTRATC_A_IDX_HOLD 40031
#define MOD_EXTRATC_B_IDX_HOLD 40033
#define MOD_EXTRATC_C_IDX_HOLD 40035
#define MOD_EXTRATC_D_IDX_HOLD 40037
// Thermocouple index type
#define MOD_TCIDX_0_TYPE_HOLD 40039
#define MOD_TCIDX_1_TYPE_HOLD 40041
#define MOD_TCIDX_2_TYPE_HOLD 40043
#define MOD_TCIDX_3_TYPE_HOLD 40045
#define MOD_TCIDX_4_TYPE_HOLD 40047
#define MOD_TCIDX_5_TYPE_HOLD 40049

#define PIN_PWM_A A0_5
#define PIN_PWM_B A0_6

#define PIN_TRIGGER_INTERRUPT I0_6

#define PIN_MOTOR_DIRECTION Q1_6
#define PIN_MOTOR_PWM Q1_7
#define PIN_MOTOR_LVDT_IN I0_7

#endif