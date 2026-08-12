#include "controller_state.h"

#include <string.h>

#define X_CENTER 2180
#define Y_CENTER 1960
#define DEAD_ZONE 300
#define X_MIN 630
#define X_MAX 3730
#define Y_MIN 310
#define Y_MAX 3460

static int32_t clamp_i32(int32_t value, int32_t low, int32_t high) {
    return value < low ? low : (value > high ? high : value);
}

static int16_t map_i16(int32_t value, int32_t in_min, int32_t in_max,
                       int32_t out_min, int32_t out_max) {
    value = clamp_i32(value, in_min, in_max);
    return (int16_t)((value - in_min) * (out_max - out_min) /
                         (in_max - in_min) +
                     out_min);
}

static int16_t clamp_axis(int32_t value) {
    return (int16_t)clamp_i32(value, -1000, 1000);
}

static bool is_game_mode(ar_controller_mode_t mode) {
    return mode == AR_MODE_GAME_YAHTZEE || mode == AR_MODE_GAME_FARM;
}

void ar_controller_state_init(ar_controller_state_t* state) {
    memset(state, 0, sizeof(*state));
    state->mode = AR_MODE_HEAD;
    state->return_mode = AR_MODE_HEAD;
    state->next_sequence = 1;
}

void ar_controller_toggle_physical_mode(ar_controller_state_t* state) {
    if (is_game_mode(state->mode)) return;
    if (state->mode == AR_MODE_BASE) {
        state->mode = AR_MODE_HEAD;
        state->stop_pending = true;
    } else {
        state->mode = AR_MODE_BASE;
    }
    state->return_mode = state->mode;
}

bool ar_controller_apply_agent_command(ar_controller_state_t* state,
                                       ar_agent_command_t command) {
    ar_controller_mode_t requested;
    if (command == AR_AGENT_COMMAND_GAME_END) {
        if (!is_game_mode(state->mode)) return false;
        state->mode = state->return_mode;
        return true;
    }
    if (command == AR_AGENT_COMMAND_YAHTZEE) {
        requested = AR_MODE_GAME_YAHTZEE;
    } else if (command == AR_AGENT_COMMAND_FARM) {
        requested = AR_MODE_GAME_FARM;
    } else {
        return false;
    }
    if (!is_game_mode(state->mode)) {
        state->return_mode = state->mode;
        if (state->mode == AR_MODE_BASE) state->stop_pending = true;
    }
    state->mode = requested;
    return true;
}

void ar_controller_accept_status(ar_controller_state_t* state,
                                 const ar_controller_packet_t* status,
                                 uint32_t now_ms) {
    if (status == NULL || status->kind != AR_PACKET_STATUS) return;
    state->ack_seen = true;
    state->online = true;
    state->last_ack_ms = now_ms;
}

void ar_controller_tick(ar_controller_state_t* state, uint32_t now_ms) {
    if (state->ack_seen && (uint32_t)(now_ms - state->last_ack_ms) >
                               AR_CONTROLLER_ACK_TIMEOUT_MS) {
        state->online = false;
        if (state->mode == AR_MODE_BASE) state->stop_pending = true;
    }
}

void ar_controller_build_input(ar_controller_state_t* state,
                               uint16_t raw_x, uint16_t raw_y,
                               uint16_t buttons, ar_controller_packet_t* packet) {
    memset(packet, 0, sizeof(*packet));
    int32_t x = raw_x;
    int32_t y = raw_y;
    if (x > X_CENTER - DEAD_ZONE && x < X_CENTER + DEAD_ZONE) x = X_CENTER;
    if (y > Y_CENTER - DEAD_ZONE && y < Y_CENTER + DEAD_ZONE) y = Y_CENTER;

    packet->kind = AR_PACKET_INPUT;
    packet->mode = state->mode;
    packet->sequence = state->next_sequence++;
    packet->joystick_x = map_i16(x, X_MIN, X_MAX, -1000, 1000);
    packet->joystick_y = map_i16(y, Y_MIN, Y_MAX, 1000, -1000);
    packet->head_yaw = map_i16(x, X_MIN, X_MAX, 1280, -1280);
    packet->head_pitch = map_i16(y, Y_MIN, Y_MAX, 0, 900);
    packet->buttons_held = buttons;
    packet->button_events = (uint16_t)(buttons & ~state->previous_buttons);
    packet->flags = state->stop_pending ? AR_FLAG_STOP : 0;
    if (state->online) packet->flags |= AR_FLAG_ONLINE;
    state->previous_buttons = buttons;
    state->stop_pending = false;
}

void ar_receiver_state_init(ar_receiver_state_t* state) {
    memset(state, 0, sizeof(*state));
    state->mode = AR_MODE_HEAD;
    state->stopped = true;
}

bool ar_receiver_accept_input(ar_receiver_state_t* state,
                              const ar_controller_packet_t* packet,
                              uint32_t now_ms) {
    if (packet == NULL || packet->kind != AR_PACKET_INPUT) return false;
    if (state->input_seen && (int32_t)(packet->sequence - state->last_sequence) <= 0)
        return false;

    state->input_seen = true;
    state->last_input_ms = now_ms;
    state->last_sequence = packet->sequence;
    state->mode = packet->mode;
    state->button_events = packet->button_events;
    state->head_yaw = packet->head_yaw;
    state->head_pitch = packet->head_pitch;

    if (packet->mode == AR_MODE_BASE && !(packet->flags & AR_FLAG_STOP)) {
        state->base_left = clamp_axis(packet->joystick_y + packet->joystick_x);
        state->base_right = clamp_axis(packet->joystick_y - packet->joystick_x);
        state->stopped = state->base_left == 0 && state->base_right == 0;
    } else {
        state->base_left = 0;
        state->base_right = 0;
        state->stopped = true;
    }
    return true;
}

void ar_receiver_tick(ar_receiver_state_t* state, uint32_t now_ms) {
    if (state->input_seen &&
        (uint32_t)(now_ms - state->last_input_ms) > AR_CONTROLLER_INPUT_TIMEOUT_MS) {
        state->base_left = 0;
        state->base_right = 0;
        state->stopped = true;
    }
}
