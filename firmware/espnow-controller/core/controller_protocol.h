#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define AR_CONTROLLER_PACKET_SIZE 24u
#define AR_CONTROLLER_PROTOCOL_VERSION 1u
#define AR_CONTROLLER_ACK_TIMEOUT_MS 1000u
#define AR_CONTROLLER_INPUT_TIMEOUT_MS 300u

typedef enum {
    AR_MODE_HEAD = 0,
    AR_MODE_BASE = 1,
    AR_MODE_GAME_YAHTZEE = 2,
    AR_MODE_GAME_FARM = 3,
} ar_controller_mode_t;

typedef enum {
    AR_PACKET_INPUT = 1,
    AR_PACKET_STATUS = 2,
    AR_PACKET_MODE_COMMAND = 3,
} ar_packet_kind_t;

typedef enum {
    AR_AGENT_COMMAND_NONE = 0,
    AR_AGENT_COMMAND_YAHTZEE = 1,
    AR_AGENT_COMMAND_FARM = 2,
    AR_AGENT_COMMAND_GAME_END = 3,
} ar_agent_command_t;

enum {
    AR_BUTTON_ACTION = 1u << 0,
};

enum {
    AR_FLAG_STOP = 1u << 0,
    AR_FLAG_ONLINE = 1u << 1,
};

typedef struct {
    ar_packet_kind_t kind;
    ar_controller_mode_t mode;
    uint8_t flags;
    uint32_t sequence;
    int16_t joystick_x;
    int16_t joystick_y;
    int16_t head_yaw;
    int16_t head_pitch;
    uint16_t buttons_held;
    uint16_t button_events;
    ar_agent_command_t command;
} ar_controller_packet_t;

bool ar_controller_encode(const ar_controller_packet_t* packet,
                          uint8_t output[AR_CONTROLLER_PACKET_SIZE]);
bool ar_controller_decode(const uint8_t* data, size_t length,
                          ar_controller_packet_t* packet);
const char* ar_controller_mode_name(ar_controller_mode_t mode);

#ifdef __cplusplus
}
#endif
