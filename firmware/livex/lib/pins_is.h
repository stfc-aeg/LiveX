#ifndef __pins_is_H__
#define __pins_is_H__

#if defined(ESP32PLC_21) || defined(ESP32PLC_42) || defined(ESP32PLC_58) || defined(ESP32PLC_38AR) || defined(ESP32PLC_53ARR) || defined(ESP32PLC_57AAR) || defined(ESP32PLC_54ARA)
#define PIN_I0_0		(0x2106)
#define PIN_I0_1		(0x2104)
#define PIN_I0_2		(0x2105)
#define PIN_I0_3		(0x2103)
#define PIN_I0_4		(0x2102)
#define PIN_I0_5		(27)
#define PIN_I0_6		(26)
#define PIN_I0_7		(0x4902)
#define PIN_I0_8		(0x4903)
#define PIN_I0_9		(0x4803)
#define PIN_I0_10		(0x4802)
#define PIN_I0_11		(0x4801)
#define PIN_I0_12		(0x4800)

static const uint32_t I0_0 = PIN_I0_0;
static const uint32_t I0_1 = PIN_I0_1;
static const uint32_t I0_2 = PIN_I0_2;
static const uint32_t I0_3 = PIN_I0_3;
static const uint32_t I0_4 = PIN_I0_4;
static const uint32_t I0_5 = PIN_I0_5;
static const uint32_t I0_6 = PIN_I0_6;
static const uint32_t I0_7 = PIN_I0_7;
static const uint32_t I0_8 = PIN_I0_8;
static const uint32_t I0_9 = PIN_I0_9;
static const uint32_t I0_10 = PIN_I0_10;
static const uint32_t I0_11 = PIN_I0_11;
static const uint32_t I0_12 = PIN_I0_12;

#define PIN_Q0_0		(0x400b)
#define PIN_Q0_1		(0x400a)
#define PIN_Q0_2		(0x4009)
#define PIN_Q0_3		(0x4008)
#define PIN_Q0_4		(0x400c)
#define PIN_Q0_5		(0x400d)
#define PIN_Q0_6		(0x4006)
#define PIN_Q0_7		(0x4007)

static const uint32_t Q0_0 = PIN_Q0_0;
static const uint32_t Q0_1 = PIN_Q0_1;
static const uint32_t Q0_2 = PIN_Q0_2;
static const uint32_t Q0_3 = PIN_Q0_3;
static const uint32_t Q0_4 = PIN_Q0_4;
static const uint32_t Q0_5 = PIN_Q0_5;
static const uint32_t Q0_6 = PIN_Q0_6;
static const uint32_t Q0_7 = PIN_Q0_7;

static const uint32_t A0_5 = PIN_Q0_5;
static const uint32_t A0_6 = PIN_Q0_6;
static const uint32_t A0_7 = PIN_Q0_7;

#elif defined(ESP32PLC_19R) || defined(ESP32PLC_38R) || defined(ESP32PLC_57R) || defined(ESP32PLC_50RRA)
#define PIN_I0_0		(27)
#define PIN_I0_1		(26)
#define PIN_I0_2		(0x4902)
#define PIN_I0_3		(0x4903)
#define PIN_I0_4		(0x4803)
#define PIN_I0_5		(0x4802)

static const uint32_t I0_0 = PIN_I0_0;
static const uint32_t I0_1 = PIN_I0_1;
static const uint32_t I0_2 = PIN_I0_2;
static const uint32_t I0_3 = PIN_I0_3;
static const uint32_t I0_4 = PIN_I0_4;
static const uint32_t I0_5 = PIN_I0_5;

#define PIN_R0_1		(0x2104)
#define PIN_R0_2		(0x2106)
#define PIN_R0_3		(0x2103)
#define PIN_R0_4		(0x2105)
#define PIN_R0_5		(0x400C)
#define PIN_R0_6		(0x4008)
#define PIN_R0_7		(0x4009)
#define PIN_R0_8		(0x400A)

static const uint32_t R0_1 = PIN_R0_1;
static const uint32_t R0_2 = PIN_R0_2;
static const uint32_t R0_3 = PIN_R0_3;
static const uint32_t R0_4 = PIN_R0_4;
static const uint32_t R0_5 = PIN_R0_5;
static const uint32_t R0_6 = PIN_R0_6;
static const uint32_t R0_7 = PIN_R0_7;
static const uint32_t R0_8 = PIN_R0_8;

#define PIN_A0_0		(0x400D)
#define PIN_A0_1		(0x4006)
#define PIN_A0_2		(0x4007)

static const uint32_t Q0_0 = PIN_A0_0;
static const uint32_t Q0_1 = PIN_A0_1;
static const uint32_t Q0_2 = PIN_A0_2;

static const uint32_t A0_0 = PIN_A0_0;
static const uint32_t A0_1 = PIN_A0_1;
static const uint32_t A0_2 = PIN_A0_2;
#endif

#if defined(ESP32PLC_42) || defined(ESP32PLC_58) ||  defined(ESP32PLC_57AAR)
#define PIN_I1_0		(0x2101)
#define PIN_I1_1		(0x2100)
#define PIN_I1_2		(0x2007)
#define PIN_I1_3		(0x2006)
#define PIN_I1_4		(0x2005)
#define PIN_I1_5		(35)
#define PIN_I1_6		(25)
#define PIN_I1_7		(0x4900)
#define PIN_I1_8		(0x4901)
#define PIN_I1_9		(0x4A03)
#define PIN_I1_10		(0x4A02)
#define PIN_I1_11		(0x4A00)
#define PIN_I1_12		(0x4A01)

static const uint32_t I1_0  = PIN_I1_0;
static const uint32_t I1_1  = PIN_I1_1;
static const uint32_t I1_2  = PIN_I1_2;
static const uint32_t I1_3  = PIN_I1_3;
static const uint32_t I1_4  = PIN_I1_4;
static const uint32_t I1_5  = PIN_I1_5;
static const uint32_t I1_6  = PIN_I1_6;
static const uint32_t I1_7  = PIN_I1_7;
static const uint32_t I1_8  = PIN_I1_8;
static const uint32_t I1_9  = PIN_I1_9;
static const uint32_t I1_10 = PIN_I1_10;
static const uint32_t I1_11 = PIN_I1_11;
static const uint32_t I1_12 = PIN_I1_12;

#define PIN_Q1_0		(0x400F)
#define PIN_Q1_1		(0x400E)
#define PIN_Q1_2		(0x4000)
#define PIN_Q1_3		(0x4001)
#define PIN_Q1_4		(0x4002)
#define PIN_Q1_5		(0x4003)
#define PIN_Q1_6		(0x4108)
#define PIN_Q1_7		(0x4109)

static const uint32_t Q1_0 = PIN_Q1_0;
static const uint32_t Q1_1 = PIN_Q1_1;
static const uint32_t Q1_2 = PIN_Q1_2;
static const uint32_t Q1_3 = PIN_Q1_3;
static const uint32_t Q1_4 = PIN_Q1_4;
static const uint32_t Q1_5 = PIN_Q1_5;
static const uint32_t Q1_6 = PIN_Q1_6;
static const uint32_t Q1_7 = PIN_Q1_7;

static const uint32_t A1_5 = PIN_Q1_5;
static const uint32_t A1_6 = PIN_Q1_6;
static const uint32_t A1_7 = PIN_Q1_7;

#elif defined(ESP32PLC_38R) || defined(ESP32PLC_57R) || defined(ESP32PLC_38AR) || defined(ESP32PLC_53ARR) || defined(ESP32PLC_54ARA) || defined(ESP32PLC_50RRA)
#define PIN_I1_0		(35)
#define PIN_I1_1		(25)
#define PIN_I1_2		(0x4900)
#define PIN_I1_3		(0x4901)
#define PIN_I1_4		(0x4A03)
#define PIN_I1_5		(0x4A02)

static const uint32_t I1_0 = PIN_I1_0;
static const uint32_t I1_1 = PIN_I1_1;
static const uint32_t I1_2 = PIN_I1_2;
static const uint32_t I1_3 = PIN_I1_3;
static const uint32_t I1_4 = PIN_I1_4;
static const uint32_t I1_5 = PIN_I1_5;

#define PIN_R1_1		(0x2100)
#define PIN_R1_2		(0x2101)
#define PIN_R1_3		(0x2006)
#define PIN_R1_4		(0x2007)
#define PIN_R1_5		(0x4002)
#define PIN_R1_6		(0x4001)
#define PIN_R1_7		(0x4000)
#define PIN_R1_8		(0x400E)

static const uint32_t R1_1 = PIN_R1_1;
static const uint32_t R1_2 = PIN_R1_2;
static const uint32_t R1_3 = PIN_R1_3;
static const uint32_t R1_4 = PIN_R1_4;
static const uint32_t R1_5 = PIN_R1_5;
static const uint32_t R1_6 = PIN_R1_6;
static const uint32_t R1_7 = PIN_R1_7;
static const uint32_t R1_8 = PIN_R1_8;

#define PIN_A1_0		(0x4003)
#define PIN_A1_1		(0x4108)
#define PIN_A1_2		(0x4109)

static const uint32_t A1_0 = PIN_A1_0;
static const uint32_t A1_1 = PIN_A1_1;
static const uint32_t A1_2 = PIN_A1_2;

static const uint32_t Q1_0 = PIN_A1_0;
static const uint32_t Q1_1 = PIN_A1_1;
static const uint32_t Q1_2 = PIN_A1_2;
#endif

#if defined(ESP32PLC_58) || defined(ESP32PLC_54ARA) || defined(ESP32PLC_50RRA)
#define PIN_I2_0		(0x2004)
#define PIN_I2_1		(0x2003)
#define PIN_I2_2		(0x2002)
#define PIN_I2_3		(0x2001)
#define PIN_I2_4		(0x2000)
#define PIN_I2_5		(34)
#define PIN_I2_6		(5)
#define PIN_I2_7		(0x4B03)
#define PIN_I2_8		(0x4B02)
#define PIN_I2_9		(0x4B00)
#define PIN_I2_10		(0x4B01)

static const uint32_t I2_0  = PIN_I2_0;
static const uint32_t I2_1  = PIN_I2_1;
static const uint32_t I2_2  = PIN_I2_2;
static const uint32_t I2_3  = PIN_I2_3;
static const uint32_t I2_4  = PIN_I2_4;
static const uint32_t I2_5  = PIN_I2_5;
static const uint32_t I2_6  = PIN_I2_6;
static const uint32_t I2_7  = PIN_I2_7;
static const uint32_t I2_8  = PIN_I2_8;
static const uint32_t I2_9  = PIN_I2_9;
static const uint32_t I2_10 = PIN_I2_10;

#define PIN_Q2_0		(0x410F)
#define PIN_Q2_1		(0x410E)
#define PIN_Q2_2		(0x410D)
#define PIN_Q2_3		(0x410C)
#define PIN_Q2_4		(0x410B)
#define PIN_Q2_5		(0x410A)
#define PIN_Q2_6		(0x4106)
#define PIN_Q2_7		(0x4107)

static const uint32_t Q2_0 = PIN_Q2_0;
static const uint32_t Q2_1 = PIN_Q2_1;
static const uint32_t Q2_2 = PIN_Q2_2;
static const uint32_t Q2_3 = PIN_Q2_3;
static const uint32_t Q2_4 = PIN_Q2_4;
static const uint32_t Q2_5 = PIN_Q2_5;
static const uint32_t Q2_6 = PIN_Q2_6;
static const uint32_t Q2_7 = PIN_Q2_7;

static const uint32_t A2_5 = PIN_Q2_5;
static const uint32_t A2_6 = PIN_Q2_6;
static const uint32_t A2_7 = PIN_Q2_7;

#elif defined(ESP32PLC_57R) || defined(ESP32PLC_53ARR) || defined(ESP32PLC_57AAR)
#define PIN_I2_0		(34)
#define PIN_I2_1		(5)
#define PIN_I2_2		(0x4B03)
#define PIN_I2_3		(0x4B02)
#define PIN_I2_4		(0x4B00)
#define PIN_I2_5		(0x4B01)

static const uint32_t I2_0 = PIN_I2_0;
static const uint32_t I2_1 = PIN_I2_1;
static const uint32_t I2_2 = PIN_I2_2;
static const uint32_t I2_3 = PIN_I2_3;
static const uint32_t I2_4 = PIN_I2_4;
static const uint32_t I2_5 = PIN_I2_5;

#define PIN_R2_1		(0x2003)
#define PIN_R2_2		(0x2004)
#define PIN_R2_3		(0x2001)
#define PIN_R2_4		(0x2002)
#define PIN_R2_5		(0x410B)
#define PIN_R2_6		(0x410C)
#define PIN_R2_7		(0x410D)
#define PIN_R2_8		(0x410E)

static const uint32_t R2_1 = PIN_R2_1;
static const uint32_t R2_2 = PIN_R2_2;
static const uint32_t R2_3 = PIN_R2_3;
static const uint32_t R2_4 = PIN_R2_4;
static const uint32_t R2_5 = PIN_R2_5;
static const uint32_t R2_6 = PIN_R2_6;
static const uint32_t R2_7 = PIN_R2_7;
static const uint32_t R2_8 = PIN_R2_8;

#define PIN_A2_0		(0x410A)
#define PIN_A2_1		(0x4106)
#define PIN_A2_2		(0x4107)

static const uint32_t A2_0 = PIN_A2_0;
static const uint32_t A2_1 = PIN_A2_1;
static const uint32_t A2_2 = PIN_A2_2;

static const uint32_t Q2_0 = PIN_A2_0;
static const uint32_t Q2_1 = PIN_A2_1;
static const uint32_t Q2_2 = PIN_A2_2;
#endif

// External GPIOs
#if defined(ESP32PLC_V3)
static const uint32_t GPIO_0 = 0x2107;
#endif

static const uint32_t I_VP = 36;
static const uint32_t I_VN = 39;

// SD
#define PIN_SD_CS					(13)

// Ethernet
#define PIN_SPI_SS_ETHERNET_LIB		(15)

// RTC
#define HAVE_RTC
#define HAVE_RTC_DS3231

// RS485
#if defined(ESP32PLC_V3)
#define HAVE_RS485
#define HAVE_RS485_HARD
#define RS485_HWSERIAL				(2)
#define RS485_DE_RE					(4)
#endif

// Expansion module 1
#if defined(ESP32PLC_V3)
#define SerialExp1					(SerialSC1)
static const uint32_t EXP1_CS = 2;
static const uint32_t EXP1_PWM = 0x2300;
static const uint32_t EXP1_INT = 0x2301;
static const uint32_t EXP1_AN = 0x2302;
static const uint32_t EXP1_RST = 0x2303;
#endif

#if defined(EXPANSION_MODULE1_GPRS)
#define HAVE_GPRS

#if defined(ESP32PLC_V3)
#define GSM4_SERIAL					(SerialExp1)
#define GSM4_RESETN					(EXP1_RST)
#elif defined(ESP32PLC_V1)
#define GSM4_SERIAL					(Serial2)
#endif

#else
#if defined(ESP32PLC_V1)
#define HAVE_RS485
#define HAVE_RS485_HARD
#define RS485_HWSERIAL              (2)
#define RS485_DE_RE                 (4)
#endif
#endif

// Expansion module 2
#if defined(ESP32PLC_V3)
#define SerialExp2					(SerialSC0)
static const uint32_t EXP2_CS = 32;
static const uint32_t EXP2_PWM = 0x2304;
static const uint32_t EXP2_INT = 0x2305;
static const uint32_t EXP2_RST = 0x2306;
static const uint32_t EXP2_AN = 0x2307;
#endif

#if defined(EXPANSION_MODULE2_GPRS)
#define HAVE_GPRS

#if defined(ESP32PLC_V3)
#define GSM4_SERIAL					(SerialExp2)
#define GSM4_RESETN					(EXP2_RST)
#endif

#else
// RS-232
#if defined(ESP32PLC_V3)
#define RS232						(SerialSC0)
#elif defined(ESP32PLC_V1)
#define RS232						(Serial)
#endif
#endif

// Expansion hardware
#if defined(ESP32PLC_V3)
#define HAVE_SERIAL_SC_0
#define SERIAL_SC_0_CS				12

#define HAVE_SERIAL_SC_1
#define SERIAL_SC_1_CS				12
#endif

#define HAVE_PCA9685
static const uint8_t pca9685Addresses[] = {
	0x40,
	0x41,
};
#define NUM_PCA9685_DEVICES (sizeof(pca9685Addresses) / sizeof(uint8_t))

#define HAVE_MCP23008
static const uint8_t mcp23008Addresses[] = {
	0x20,
	0x21,

#if defined(ESP32PLC_V3)
	0x23,
#endif
};
#define NUM_MCP23008_DEVICES (sizeof(mcp23008Addresses) / sizeof(uint8_t))

#define HAVE_ADS1015
static const uint8_t ads1015Addresses[] = {
	0x48,
	0x49,
	0x4a,
	0x4b,
};
#define NUM_ADS1015_DEVICES (sizeof(ads1015Addresses) / sizeof(uint8_t))

#endif // __pins_is_H__
