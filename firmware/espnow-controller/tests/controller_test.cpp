#include <cassert>
#include <cstring>
#include <iostream>

extern "C" {
#include "controller_protocol.h"
#include "controller_state.h"
}

static void packet_round_trip() {
    ar_controller_state_t controller;
    ar_controller_state_init(&controller);
    ar_controller_packet_t input{};
    ar_controller_build_input(&controller, 630, 310, 0, &input);

    assert(input.mode == AR_MODE_HEAD);
    assert(input.head_yaw == 1280);
    assert(input.head_pitch == 0);
    assert(input.joystick_x == -1000);
    assert(input.joystick_y == 1000);

    uint8_t wire[AR_CONTROLLER_PACKET_SIZE]{};
    assert(ar_controller_encode(&input, wire));
    ar_controller_packet_t decoded{};
    assert(ar_controller_decode(wire, sizeof(wire), &decoded));
    assert(std::memcmp(&input, &decoded, sizeof(input)) == 0);
    wire[10] ^= 1;
    assert(!ar_controller_decode(wire, sizeof(wire), &decoded));
}

static void mode_flow_and_safe_stop() {
    ar_controller_state_t controller;
    ar_controller_state_init(&controller);
    assert(controller.mode == AR_MODE_HEAD);

    ar_controller_toggle_physical_mode(&controller);
    assert(controller.mode == AR_MODE_BASE);
    ar_controller_packet_t packet{};
    ar_controller_build_input(&controller, 2180, 310, 0, &packet);
    assert(!(packet.flags & AR_FLAG_STOP));

    ar_controller_apply_agent_command(&controller, AR_AGENT_COMMAND_FARM);
    assert(controller.mode == AR_MODE_GAME_FARM);
    ar_controller_build_input(&controller, 2180, 310, 0, &packet);
    assert(packet.flags & AR_FLAG_STOP);

    ar_controller_toggle_physical_mode(&controller);
    assert(controller.mode == AR_MODE_GAME_FARM);
    ar_controller_apply_agent_command(&controller, AR_AGENT_COMMAND_GAME_END);
    assert(controller.mode == AR_MODE_BASE);

    ar_controller_toggle_physical_mode(&controller);
    assert(controller.mode == AR_MODE_HEAD);
    ar_controller_build_input(&controller, 2180, 310, 0, &packet);
    assert(packet.flags & AR_FLAG_STOP);
}

static void agent_command_round_trip() {
    ar_controller_packet_t command{};
    command.kind = AR_PACKET_MODE_COMMAND;
    command.mode = AR_MODE_GAME_YAHTZEE;
    command.sequence = 9;
    command.command = AR_AGENT_COMMAND_YAHTZEE;
    uint8_t wire[AR_CONTROLLER_PACKET_SIZE]{};
    assert(ar_controller_encode(&command, wire));

    ar_controller_packet_t decoded{};
    assert(ar_controller_decode(wire, sizeof(wire), &decoded));
    ar_controller_state_t controller;
    ar_controller_state_init(&controller);
    assert(ar_controller_apply_agent_command(&controller, decoded.command));
    assert(controller.mode == AR_MODE_GAME_YAHTZEE);
}

static void button_is_one_shot() {
    ar_controller_state_t controller;
    ar_controller_state_init(&controller);
    ar_controller_apply_agent_command(&controller, AR_AGENT_COMMAND_YAHTZEE);
    ar_controller_packet_t packet{};

    ar_controller_build_input(&controller, 2180, 1960, AR_BUTTON_ACTION, &packet);
    assert(packet.button_events == AR_BUTTON_ACTION);
    ar_controller_build_input(&controller, 2180, 1960, AR_BUTTON_ACTION, &packet);
    assert(packet.button_events == 0);
    ar_controller_build_input(&controller, 2180, 1960, 0, &packet);
    assert(packet.button_events == 0);
    ar_controller_build_input(&controller, 2180, 1960, AR_BUTTON_ACTION, &packet);
    assert(packet.button_events == AR_BUTTON_ACTION);
}

static void receiver_never_moves_outside_base_and_times_out() {
    ar_controller_state_t controller;
    ar_controller_state_init(&controller);
    ar_receiver_state_t receiver;
    ar_receiver_state_init(&receiver);
    ar_controller_packet_t packet{};

    ar_controller_build_input(&controller, 2180, 310, 0, &packet);
    assert(ar_receiver_accept_input(&receiver, &packet, 10));
    assert(receiver.stopped);

    ar_controller_toggle_physical_mode(&controller);
    ar_controller_build_input(&controller, 2180, 310, 0, &packet);
    assert(ar_receiver_accept_input(&receiver, &packet, 20));
    assert(!receiver.stopped);
    assert(receiver.base_left == 1000 && receiver.base_right == 1000);

    ar_receiver_tick(&receiver, 321);
    assert(receiver.stopped);
    assert(receiver.base_left == 0 && receiver.base_right == 0);
}

static void offline_status() {
    ar_controller_state_t controller;
    ar_controller_state_init(&controller);
    ar_controller_packet_t status{};
    status.kind = AR_PACKET_STATUS;
    status.mode = AR_MODE_HEAD;
    ar_controller_accept_status(&controller, &status, 100);
    assert(controller.online);
    ar_controller_tick(&controller, 1100);
    assert(controller.online);
    ar_controller_tick(&controller, 1101);
    assert(!controller.online);
}

int main() {
    packet_round_trip();
    mode_flow_and_safe_stop();
    agent_command_round_trip();
    button_is_one_shot();
    receiver_never_moves_outside_base_and_times_out();
    offline_status();
    std::cout << "ESPNOW_CONTROLLER_TEST_OK\n";
    return 0;
}
