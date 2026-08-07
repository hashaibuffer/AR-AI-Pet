#pragma once

#include <string_view>

class McpServer;

namespace ar_aipet {

// Project-level actions exposed through the official StackChan MCP server.
class RobotActionAdapter {
public:
    void registerMcpTools(McpServer& server);

private:
    bool playMotion(std::string_view name);
    bool stopMotion();
};

RobotActionAdapter& GetRobotActionAdapter();

}  // namespace ar_aipet
