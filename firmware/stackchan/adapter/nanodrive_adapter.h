#pragma once

#include <stdbool.h>
#include <stdint.h>

#include "driver/uart.h"

#ifdef __cplusplus
extern "C" {
#endif

// CoreS3 Port C: GPIO17 TX (yellow), GPIO18 RX (green).
#define NANODRIVE_UART_PORT UART_NUM_2
#define NANODRIVE_TX_PIN 17
#define NANODRIVE_RX_PIN 18
#define NANODRIVE_BAUD 115200

// No level shifter is currently available. Only StackChan TX -> NanoDrive RX
// is connected, so commands are accepted after a successful local UART write.
#define NANODRIVE_TX_ONLY 1

bool nanodrive_init(void);
bool nanodrive_is_initialized(void);
bool nanodrive_send_raw(const char* command);

bool nanodrive_enable(bool enabled);
bool nanodrive_forward(uint8_t speed);
bool nanodrive_backward(uint8_t speed);
bool nanodrive_turn_left(uint8_t speed);
bool nanodrive_turn_right(uint8_t speed);
bool nanodrive_set_wheels(int16_t left, int16_t right);
bool nanodrive_stop(void);
bool nanodrive_set_timeout(uint16_t timeout_ms);

#ifdef __cplusplus
}
#endif
