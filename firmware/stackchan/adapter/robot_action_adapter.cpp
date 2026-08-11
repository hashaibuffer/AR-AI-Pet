/*
 * AR-AIPet project actions for StackChan.
 *
 * Communication is handled by StackChan's official McpServer and WebSocket
 * control server. This file only maps a small, fixed action vocabulary to the
 * existing StackChan motion system.
 */
#include "robot_action_adapter.h"
#include "nanodrive_adapter.h"

#include <mcp_server.h>
#include <mooncake_log.h>
#include <smooth_lvgl.hpp>
#include <stackchan/modifiers/dance.h>
#include <stackchan/stackchan.h>

#include <memory>
#include <string>
#include <vector>

namespace ar_aipet {

namespace {

constexpr char kTag[] = "AR-AIPet-Action";

int g_dance_modifier_id = -1;
stackchan::Modifier* g_dance_modifier = nullptr;

const stackchan::animation::KeyframeSequence* findMotion(std::string_view name)
{
    if (name == "happy") {
        return &stackchan::DanceModifier::Happy;
    }
    if (name == "robot") {
        return &stackchan::DanceModifier::Robot;
    }
    if (name == "panic") {
        return &stackchan::DanceModifier::Panic;
    }
    if (name == "look_around") {
        return &stackchan::DanceModifier::LookAround;
    }
    return nullptr;
}

}  // namespace

RobotActionAdapter& GetRobotActionAdapter()
{
    static RobotActionAdapter adapter;
    return adapter;
}

void RobotActionAdapter::registerMcpTools(McpServer& server)
{
    const bool baseReady = nanodrive_init();
    mclog::tagInfo(kTag, "NanoDrive UART initialized={}", baseReady);

    server.AddTool(
        "self.robot.play_motion",
        "Play one fixed StackChan motion. Allowed names: happy, robot, panic, look_around.",
        PropertyList({Property("name", kPropertyTypeString, std::string("happy"))}),
        [this](const PropertyList& properties) -> ReturnValue {
            const auto name = properties["name"].value<std::string>();
            LvglLockGuard lock;
            const bool accepted = playMotion(name);
            mclog::tagInfo(kTag, "play_motion name={} accepted={}", name, accepted);
            return accepted;
        });

    server.AddTool(
        "self.robot.stop_motion",
        "Stop the current project motion.",
        std::vector<Property>{},
        [this](const PropertyList&) -> ReturnValue {
            LvglLockGuard lock;
            const bool accepted = stopMotion();
            mclog::tagInfo(kTag, "stop_motion accepted={}", accepted);
            return accepted;
        });

    server.AddTool(
        "self.robot.base_move",
        "Move the physical base. Direction: forward, backward, left, right. "
        "The NanoDrive watchdog stops motion after two seconds unless another command arrives.",
        PropertyList({Property("direction", kPropertyTypeString, std::string("forward")),
                      Property("speed", kPropertyTypeInteger, 100, 0, 180)}),
        [](const PropertyList& properties) -> ReturnValue {
            const auto direction = properties["direction"].value<std::string>();
            const auto speed = static_cast<uint8_t>(properties["speed"].value<int>());

            if (!nanodrive_is_initialized() || !nanodrive_enable(true)) {
                return false;
            }

            bool accepted = false;
            if (direction == "forward") {
                accepted = nanodrive_forward(speed);
            } else if (direction == "backward") {
                accepted = nanodrive_backward(speed);
            } else if (direction == "left") {
                accepted = nanodrive_turn_left(speed);
            } else if (direction == "right") {
                accepted = nanodrive_turn_right(speed);
            }
            mclog::tagInfo(kTag, "base_move direction={} speed={} accepted={}",
                           direction, speed, accepted);
            return accepted;
        });

    server.AddTool(
        "self.robot.base_drive",
        "Set physical base wheel speeds. Each value is -180 to 180. Use zero for a stopped wheel.",
        PropertyList({Property("left", kPropertyTypeInteger, 0, -180, 180),
                      Property("right", kPropertyTypeInteger, 0, -180, 180)}),
        [](const PropertyList& properties) -> ReturnValue {
            const int left = properties["left"].value<int>();
            const int right = properties["right"].value<int>();
            const bool accepted = nanodrive_is_initialized() &&
                                  nanodrive_enable(true) &&
                                  nanodrive_set_wheels(left, right);
            mclog::tagInfo(kTag, "base_drive left={} right={} accepted={}",
                           left, right, accepted);
            return accepted;
        });

    server.AddTool(
        "self.robot.base_stop",
        "Immediately stop the physical NanoDrive base.",
        std::vector<Property>{},
        [](const PropertyList&) -> ReturnValue {
            const bool accepted = nanodrive_is_initialized() && nanodrive_stop();
            mclog::tagInfo(kTag, "base_stop accepted={}", accepted);
            return accepted;
        });
}

bool RobotActionAdapter::playMotion(std::string_view name)
{
    const auto* sequence = findMotion(name);
    if (sequence == nullptr) {
        return false;
    }

    stopMotion();
    g_dance_modifier_id = GetStackChan().addModifier(
        std::make_unique<stackchan::DanceModifier>(*sequence));
    g_dance_modifier = GetStackChan().getModifier(g_dance_modifier_id);
    return g_dance_modifier_id >= 0 && g_dance_modifier != nullptr;
}

bool RobotActionAdapter::stopMotion()
{
    if (g_dance_modifier_id >= 0 && g_dance_modifier != nullptr &&
        GetStackChan().getModifier(g_dance_modifier_id) == g_dance_modifier) {
        GetStackChan().removeModifier(g_dance_modifier_id);
    }

    g_dance_modifier_id = -1;
    g_dance_modifier = nullptr;
    GetStackChan().motion().stop();
    return true;
}

}  // namespace ar_aipet
