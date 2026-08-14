#pragma once

#include "mcp_action_reconnect_policy.h"

#include <web_socket.h>
#include <esp_timer.h>

#include <atomic>
#include <memory>
#include <string>

namespace ar_aipet {

// A second, action-only MCP transport. The official Xiaozhi connection keeps
// ownership of wake word, microphone, TTS and conversation state; this class
// only carries JSON-RPC tools for the AR-AIPet gateway.
class McpActionClient {
public:
    McpActionClient();
    ~McpActionClient();

    bool start();
    bool isConnected() const { return connected_.load(); }

private:
    enum class TimerPurpose : int { None, Reconnect, HandshakeTimeout };

    std::shared_ptr<std::atomic<bool>> alive_ =
        std::make_shared<std::atomic<bool>>(true);
    std::unique_ptr<WebSocket> websocket_;
    std::shared_ptr<std::atomic<bool>> notify_disconnect_;
    std::atomic<bool> connected_{false};
    std::atomic<bool> timer_armed_{false};
    std::atomic<TimerPurpose> timer_purpose_{TimerPurpose::None};
    esp_timer_handle_t timer_ = nullptr;
    McpActionReconnectPolicy reconnect_policy_;
    std::string session_id_;

    bool connectOnce();
    std::string helloMessage() const;
    void handleText(const char* data, size_t len);
    void sendMcpReply(const std::string& payload);
    void scheduleReconnect();
    void scheduleHandshakeTimeout();
    bool armTimer(TimerPurpose purpose, uint32_t delayMs);
    void stopTimer();
    void resetSocket();
    void shutdown();
};

}  // namespace ar_aipet
