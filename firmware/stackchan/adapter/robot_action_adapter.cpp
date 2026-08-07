/*
 * AR-AIPet project actions for StackChan.
 *
 * Communication is handled by StackChan's official McpServer and WebSocket
 * control server. This file only maps a small, fixed action vocabulary to the
 * existing StackChan motion system.
 */
#include "robot_action_adapter.h"

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
