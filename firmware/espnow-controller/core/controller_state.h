#pragma once

#include "controller_protocol.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    ar_controller_mode_t mode;
    ar_controller_mode_t return_mode;
    uint32_t next_sequence;
    uint32_t last_ack_ms;
    uint16_t previous_buttons;
    bool ack_seen;
    bool online;
    bool stop_pending;
} ar_controller_state_t;

typedef struct {
    uint32_t last_input_ms;
    uint32_t last_sequence;
    int16_t base_left;
    int16_t base_right;
    int16_t head_yaw;
    int16_t head_pitch;
    uint16_t button_events;
    ar_controller_mode_t mode;
    bool input_seen;
    bool stopped;
} ar_receiver_state_t;

void ar_controller_state_init(ar_controller_state_t* state);
void ar_controller_toggle_physical_mode(ar_controller_state_t* state);
bool ar_controller_apply_agent_command(ar_controller_state_t* state,
                                       ar_agent_command_t command);
void ar_controller_accept_status(ar_controller_state_t* state,
                                 const ar_controller_packet_t* status,
                                 uint32_t now_ms);
void ar_controller_tick(ar_controller_state_t* state, uint32_t now_ms);
void ar_controller_build_input(ar_controller_state_t* state,
                               uint16_t raw_x, uint16_t raw_y,
                               uint16_t buttons, ar_controller_packet_t* packet);

void ar_receiver_state_init(ar_receiver_state_t* state);
bool ar_receiver_accept_input(ar_receiver_state_t* state,
                              const ar_controller_packet_t* packet,
                              uint32_t now_ms);
void ar_receiver_tick(ar_receiver_state_t* state, uint32_t now_ms);

#ifdef __cplusplus
}
#endif
