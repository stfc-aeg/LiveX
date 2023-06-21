#include "ExpandedGpio.h"

#include "esp32-hal-i2c.h"
#include "esp32-hal-log.h"
#include "pins_arduino.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"

static const uint8_t i2cNum = 0;
static const uint8_t i2cGeneralCallAddress = 0x00;
static const uint8_t i2cSoftReset = 0b00000110;

// extern void __pinMode(uint8_t pin, uint8_t mode);
// extern void __digitalWrite(uint8_t pin, uint8_t value);
// extern int __digitalRead(uint8_t pin);
// extern uint16_t __analogRead(uint8_t pin);

#define isExpandedPin(pin) (pin > 0xff)
#define expandedPinToDeviceAddress(p) ((p >> 8) & 0xff)
#define expandedPinToDeviceIndex(p) (p & 0xff)

// PCA9685
#ifdef HAVE_PCA9685
#include "peripheral-pca9685.h"
#endif

// MCP23008
#ifdef HAVE_MCP23008
#include "peripheral-mcp23008.h"
#endif

// ADS1015
#ifdef HAVE_ADS1015
#include "peripheral-ads1015.h"
#endif

static bool isAddressIntoArray(uint8_t addr, const uint8_t* arr, uint8_t len) {
	while (len--) {
		if (*arr++ == addr) {
			return true;
		}
	}
	return false;
}

void ExpandedGpio::init(void)
{
	if (!i2cIsInit(i2cNum)) {
		if (i2cInit(i2cNum, SDA, SCL, 0) != ESP_OK) {
			return;
		}
	}

	// Reset devices
	uint8_t resetFunction = i2cSoftReset;
	if (i2cWrite(i2cNum, i2cGeneralCallAddress, &resetFunction, sizeof(resetFunction), 50) != ESP_OK) {
		return;
	}
	delay(10);

#ifdef HAVE_PCA9685
	for (int i = 0; i < NUM_PCA9685_DEVICES; ++i) {
		pca9685_init(i2cNum, pca9685Addresses[i]);
	}
#endif

#ifdef HAVE_MCP23008
	for (int i = 0; i < NUM_MCP23008_DEVICES; ++i) {
		mcp23008_init(i2cNum, mcp23008Addresses[i]);
	}
#endif

#ifdef HAVE_ADS1015
	for (int i = 0; i < NUM_ADS1015_DEVICES; ++i) {
		ads1015_init(i2cNum, ads1015Addresses[i]);
	}
#endif

	delay(5);
}

void ExpandedGpio::pinMode(uint32_t pin, uint8_t mode)
{
	if (!isExpandedPin(pin)) {
		pinMode((uint8_t)(pin & 0xFF), mode);
		return;
	}

	uint8_t addr = expandedPinToDeviceAddress(pin);
	uint8_t index = expandedPinToDeviceIndex(pin);

#ifdef HAVE_MCP23008
	if (isAddressIntoArray(addr, mcp23008Addresses, NUM_MCP23008_DEVICES)) {
		mcp23008_set_pin_mode(i2cNum, addr, index, mode);
	}
#endif
}

void ExpandedGpio::digitalWrite(uint32_t pin, uint8_t value) {
	if (!isExpandedPin(pin)) {
		digitalWrite((uint8_t)(pin & 0xFF), value);
		return;
	}

	uint8_t addr = expandedPinToDeviceAddress(pin);
	uint8_t index = expandedPinToDeviceIndex(pin);

#ifdef HAVE_PCA9685
	if (isAddressIntoArray(addr, pca9685Addresses, NUM_PCA9685_DEVICES)) {
		if (value == LOW) {
			pca9685_set_out_off(i2cNum, addr, index);
		} else {
			pca9685_set_out_on(i2cNum, addr, index);
		}
	}
#endif
#ifdef HAVE_MCP23008
	if (isAddressIntoArray(addr, mcp23008Addresses, NUM_MCP23008_DEVICES)) {
		mcp23008_set_output(i2cNum, addr, index, value);
	}
#endif
}

int ExpandedGpio::digitalRead(uint32_t pin)
{
	if (!isExpandedPin(pin)) {
		return digitalRead((uint8_t)(pin & 0xFF));
	}

	uint8_t addr = expandedPinToDeviceAddress(pin);
	uint8_t index = expandedPinToDeviceIndex(pin);

#ifdef HAVE_MCP23008
	if (isAddressIntoArray(addr, mcp23008Addresses, NUM_MCP23008_DEVICES)) {
		return mcp23008_get_input(i2cNum, addr, index);
	}
#endif

#ifdef HAVE_ADS1015
	if (isAddressIntoArray(addr, ads1015Addresses, NUM_ADS1015_DEVICES)) {
		return ads1015_get_input(i2cNum, addr, index) > 1023 ? HIGH : LOW;
	}
#endif

	return LOW;
}

void ExpandedGpio::analogWrite(uint32_t pin, uint16_t value) {
	if (!isExpandedPin(pin)) {
		return;
	}

	uint8_t addr = expandedPinToDeviceAddress(pin);
	uint8_t index = expandedPinToDeviceIndex(pin);

#ifdef HAVE_PCA9685
	if (isAddressIntoArray(addr, pca9685Addresses, NUM_PCA9685_DEVICES)) {
		pca9685_set_out_pwm(i2cNum, addr, index, value);
	}
#endif
}

uint16_t ExpandedGpio::analogRead(uint32_t pin) {
	if (!isExpandedPin(pin)) {
		return analogRead((uint8_t)(pin & 0xFF));
	}

	uint8_t addr = expandedPinToDeviceAddress(pin);
	uint8_t index = expandedPinToDeviceIndex(pin);

#ifdef HAVE_ADS1015
	if (isAddressIntoArray(addr, ads1015Addresses, NUM_ADS1015_DEVICES)) {
		return ads1015_get_input(i2cNum, addr, index);
	}
#endif

	return 0;
}
