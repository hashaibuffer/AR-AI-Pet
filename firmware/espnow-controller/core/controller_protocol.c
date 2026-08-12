#include "controller_protocol.h"

#define MAGIC_0 0xA7u
#define MAGIC_1 0x50u

static void write_u16(uint8_t* out, uint16_t value) {
    out[0] = (uint8_t)value;
    out[1] = (uint8_t)(value >> 8);
}

static void write_u32(uint8_t* out, uint32_t value) {
    out[0] = (uint8_t)value;
    out[1] = (uint8_t)(value >> 8);
    out[2] = (uint8_t)(value >> 16);
    out[3] = (uint8_t)(value >> 24);
}

static uint16_t read_u16(const uint8_t* in) {
    return (uint16_t)(in[0] | ((uint16_t)in[1] << 8));
}

static uint32_t read_u32(const uint8_t* in) {
    return (uint32_t)in[0] | ((uint32_t)in[1] << 8) |
           ((uint32_t)in[2] << 16) | ((uint32_t)in[3] << 24);
}

static uint8_t crc8(const uint8_t* data, size_t length) {
    uint8_t crc = 0;
    for (size_t i = 0; i < length; ++i) {
        crc ^= data[i];
        for (uint8_t bit = 0; bit < 8; ++bit) {
            crc = (crc & 0x80u) ? (uint8_t)((crc << 1) ^ 0x07u)
                                : (uint8_t)(crc << 1);
        }
    }
    return crc;
}

static bool valid_mode(ar_controller_mode_t mode) {
    return mode >= AR_MODE_HEAD && mode <= AR_MODE_GAME_FARM;
}

bool ar_controller_encode(const ar_controller_packet_t* packet,
                          uint8_t output[AR_CONTROLLER_PACKET_SIZE]) {
    if (packet == NULL || output == NULL || !valid_mode(packet->mode) ||
        packet->kind < AR_PACKET_INPUT || packet->kind > AR_PACKET_MODE_COMMAND) {
        return false;
    }
    output[0] = MAGIC_0;
    output[1] = MAGIC_1;
    output[2] = AR_CONTROLLER_PROTOCOL_VERSION;
    output[3] = (uint8_t)packet->kind;
    output[4] = (uint8_t)packet->mode;
    output[5] = packet->flags;
    write_u32(&output[6], packet->sequence);
    write_u16(&output[10], (uint16_t)packet->joystick_x);
    write_u16(&output[12], (uint16_t)packet->joystick_y);
    write_u16(&output[14], (uint16_t)packet->head_yaw);
    write_u16(&output[16], (uint16_t)packet->head_pitch);
    write_u16(&output[18], packet->buttons_held);
    write_u16(&output[20], packet->button_events);
    output[22] = (uint8_t)packet->command;
    output[23] = crc8(output, 23);
    return true;
}

bool ar_controller_decode(const uint8_t* data, size_t length,
                          ar_controller_packet_t* packet) {
    if (data == NULL || packet == NULL || length != AR_CONTROLLER_PACKET_SIZE ||
        data[0] != MAGIC_0 || data[1] != MAGIC_1 ||
        data[2] != AR_CONTROLLER_PROTOCOL_VERSION || data[23] != crc8(data, 23)) {
        return false;
    }
    packet->kind = (ar_packet_kind_t)data[3];
    packet->mode = (ar_controller_mode_t)data[4];
    if (packet->kind < AR_PACKET_INPUT || packet->kind > AR_PACKET_MODE_COMMAND ||
        !valid_mode(packet->mode)) {
        return false;
    }
    packet->flags = data[5];
    packet->sequence = read_u32(&data[6]);
    packet->joystick_x = (int16_t)read_u16(&data[10]);
    packet->joystick_y = (int16_t)read_u16(&data[12]);
    packet->head_yaw = (int16_t)read_u16(&data[14]);
    packet->head_pitch = (int16_t)read_u16(&data[16]);
    packet->buttons_held = read_u16(&data[18]);
    packet->button_events = read_u16(&data[20]);
    packet->command = (ar_agent_command_t)data[22];
    return true;
}

const char* ar_controller_mode_name(ar_controller_mode_t mode) {
    switch (mode) {
        case AR_MODE_HEAD: return "HEAD";
        case AR_MODE_BASE: return "BASE";
        case AR_MODE_GAME_YAHTZEE: return "GAME YAHTZEE";
        case AR_MODE_GAME_FARM: return "GAME FARM";
        default: return "UNKNOWN";
    }
}
