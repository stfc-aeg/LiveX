#include "peripheral-pca9685.h"
#include "esp32-hal-log.h"

// Registers
#define MODE1_REGISTER		0x00
#define MODE2_REGISTER		0x01
#define SUBADR1_REGISTER	0x02
#define SUBADR2_REGISTER	0x03
#define SUBADR3_REGISTER	0x04
#define ALLCALLADR_REGISTER	0x05

#define LED_REGISTERS(i)	(0x06 + (i * 4))
#define LED_ON_L(i)			(LED_REGISTERS(i))
#define LED_ON_H(i)			(LED_REGISTERS(i) + 1)
#define LED_OFF_L(i)		(LED_REGISTERS(i) + 2)
#define LED_OFF_H(i)		(LED_REGISTERS(i) + 3)

#define PRE_SCALE_REGISTER	0xfe

// Registers values and masks
#define MODE1_ALLCALL		0x01
#define MODE1_SUB3			0x02
#define MODE1_SUB2			0x04
#define MODE1_SUB1			0x08
#define MODE1_SLEEP			0x10
#define MODE1_AI			0x20
#define MODE1_EXTCLK		0x40
#define MODE1_RESTART		0x80

#define MODE2_OUTNE_1		0x01
#define MODE2_OUTNE_Z		0x02
#define MODE2_OUTDRV		0x04
#define MODE2_OCH			0x08
#define MODE2_INVRT			0x10

static uint16_t i2cTimeout = 50;

static bool set_led(uint8_t i2cNum, uint8_t addr, uint8_t index,
		uint8_t on_l, uint8_t on_h, uint8_t off_l, uint8_t off_h) {
	uint8_t buffer[5];

	buffer[0] = LED_REGISTERS(index);
	buffer[1] = on_l;
	buffer[2] = on_h;
	buffer[3] = off_l;
	buffer[4] = off_h;

	return i2cWrite(i2cNum, addr, buffer, 5, i2cTimeout) == ESP_OK;
}

bool pca9685_init(uint8_t i2cNum, uint8_t addr) {
	uint8_t buffer[2];

	buffer[0] = MODE1_REGISTER;
	buffer[1] = MODE1_SLEEP | MODE1_AI;
	if (i2cWrite(i2cNum, addr, buffer, 2, i2cTimeout) != ESP_OK) {
		return false;
	}

	buffer[0] = PRE_SCALE_REGISTER;
	buffer[1] = 11; // PWM frequency 500Hz
	if (i2cWrite(i2cNum, addr, buffer, 2, i2cTimeout) != ESP_OK) {
		return false;
	}

	buffer[0] = MODE1_REGISTER;
	buffer[1] = MODE1_AI;
	if (i2cWrite(i2cNum, addr, buffer, 2, i2cTimeout) != ESP_OK) {
		return false;
	}

	return true;
}

bool pca9685_set_out_on(uint8_t i2cNum, uint8_t addr, uint8_t index) {
	return set_led(i2cNum, addr, index, 0x00, 0x10, 0x00, 0x00);
}

bool pca9685_set_out_off(uint8_t i2cNum, uint8_t addr, uint8_t index) {
	return set_led(i2cNum, addr, index, 0x00, 0x00, 0x00, 0x10);
}

bool pca9685_set_out_pwm(uint8_t i2cNum, uint8_t addr, uint8_t index, uint16_t value) {
	return set_led(i2cNum, addr, index, 0x00, 0x00, value & 0xff, (value >> 8) & 0x0f);
}
