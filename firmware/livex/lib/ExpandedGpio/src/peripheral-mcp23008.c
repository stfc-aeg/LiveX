#include "peripheral-mcp23008.h"
#include "esp32-hal-log.h"

// Registers
#define IODIR_REGISTER		0x00
#define IPOL_REGISTER		0x01
#define GPINTEN_REGISTER	0x02
#define DEFVAL_REGISTER		0x03
#define INTCON_REGISTER		0x04
#define IOCON_REGISTER		0x05
#define GPPU_REGISTER		0x06
#define INTF_REGISTER		0x07
#define INTCAP_REGISTER		0x08
#define GPIO_REGISTER		0x09
#define OLAT_REGISTER		0x0a

// Registers values and masks
#define IOCON_INTPOL		0x02
#define IOCON_ODR			0x04
#define IOCON_DISSLW		0x10
#define IOCON_SEQOP			0x20

static const uint16_t i2cTimeout = 50;

bool mcp23008_init(uint8_t i2cNum, uint8_t addr) {
	uint8_t buffer[2];

	buffer[0] = IODIR_REGISTER;
	buffer[1] = 0xff; // Inputs
	if (i2cWrite(i2cNum, addr, buffer, 2, i2cTimeout) != ESP_OK) {
		return false;
	}

	buffer[0] = IOCON_REGISTER;
	buffer[1] = IOCON_SEQOP | IOCON_ODR;
	if (i2cWrite(i2cNum, addr, buffer, 2, i2cTimeout) != ESP_OK) {
		return false;
	}

	buffer[0] = GPPU_REGISTER;
	buffer[1] = 0x00; // No pull-ups
	if (i2cWrite(i2cNum, addr, buffer, 2, i2cTimeout) != ESP_OK) {
		return false;
	}

	return true;
}

uint8_t mcp23008_set_pin_mode(uint8_t i2cNum, uint8_t addr, uint8_t index, uint8_t mode) {
	uint8_t reg = IODIR_REGISTER;
	uint8_t iodir_reg;
	size_t len = 0;
	if (i2cWriteReadNonStop(i2cNum, addr, &reg, 1, &iodir_reg, 1, i2cTimeout, &len) != ESP_OK) {
		return 0;
	}

    if (mode == INPUT) {
        iodir_reg |= (1 << index);
    } else {
        iodir_reg &= ~(1 << index);
    }

	uint8_t buffer[2];
	buffer[0] = IODIR_REGISTER;
	buffer[1] = iodir_reg;

	if (i2cWrite(i2cNum, addr, buffer, 2, i2cTimeout) != ESP_OK) {
		return 0;
	}

    return 1;
}

uint8_t mcp23008_get_input(uint8_t i2cNum, uint8_t addr, uint8_t index) {
	uint8_t reg = GPIO_REGISTER;
	uint8_t ioval_reg;
	size_t len = 0;
	if (i2cWriteReadNonStop(i2cNum, addr, &reg, 1, &ioval_reg, 1, i2cTimeout, &len) != ESP_OK) {
		return 0;
	}

	return (ioval_reg >> index) & 0x01 ? HIGH : LOW;
}

uint8_t mcp23008_set_output(uint8_t i2cNum, uint8_t addr, uint8_t index, uint8_t value) {
	uint8_t reg = GPIO_REGISTER;
	uint8_t ioval_reg;
	size_t len = 0;
	if (i2cWriteReadNonStop(i2cNum, addr, &reg, 1, &ioval_reg, 1, i2cTimeout, &len) != ESP_OK) {
		return 0;
	}

	if (value == LOW) {
		ioval_reg &= ~(1 << index);
	} else {
		ioval_reg |= (1 << index);
	}

	uint8_t buffer[2];
	buffer[0] = GPIO_REGISTER;
	buffer[1] = ioval_reg;

	if (i2cWrite(i2cNum, addr, buffer, 2, i2cTimeout) != ESP_OK) {
		return 0;
	}

	return 1;
}
