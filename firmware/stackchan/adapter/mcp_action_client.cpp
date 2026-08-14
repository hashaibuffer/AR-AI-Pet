#include "mcp_action_client.h"

#include <cJSON.h>
#include <esp_log.h>

#include "application.h"
#include "board.h"
#include "mcp_server.h"
#include "system_info.h"

#define TAG "AR-AIPET-MCP"

namespace ar_aipet {

namespace {
constexpr uint32_t kHandshakeTimeoutMs = 10000;
}

McpActionClient::McpActionClient()
{
    esp_timer_create_args_t args = {
        .callback = [](void* arg) {
            auto* client = static_cast<McpActionClient*>(arg);
            auto alive = client->alive_;
            Application::GetInstance().Schedule([client, alive]() {
                if (!alive->load()) {
                    return;
                }
                client->timer_armed_.store(false);
                const auto purpose = client->timer_purpose_.exchange(TimerPurpose::None);
                if (purpose == TimerPurpose::Reconnect) {
                    client->connectOnce();
                } else if (purpose == TimerPurpose::HandshakeTimeout &&
                           !client->connected_.load()) {
                    ESP_LOGW(TAG, "action gateway hello timed out");
                    client->resetSocket();
                    client->scheduleReconnect();
                }
            });
        },
        .arg = this,
        .dispatch_method = ESP_TIMER_TASK,
        .name = "ar_aipet_mcp_retry",
        .skip_unhandled_events = true,
    };
    if (esp_timer_create(&args, &timer_) != ESP_OK) {
        ESP_LOGE(TAG, "failed to create reconnect timer");
        timer_ = nullptr;
    }
}

McpActionClient::~McpActionClient()
{
    shutdown();
}

bool McpActionClient::start()
{
#ifdef CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL
    if (CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL[0] == '\0') {
        ESP_LOGI(TAG, "action gateway disabled (empty URL)");
        return false;
    }
    return connectOnce();
#else
    ESP_LOGI(TAG, "action gateway disabled (no URL configured)");
    return false;
#endif
}

bool McpActionClient::connectOnce()
{
#ifdef CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL
    if (!alive_->load() || CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL[0] == '\0') {
        return false;
    }

    auto network = Board::GetInstance().GetNetwork();
    if (network == nullptr) {
        scheduleReconnect();
        return false;
    }

    stopTimer();
    resetSocket();
    websocket_ = network->CreateWebSocket(2);
    if (websocket_ == nullptr) {
        ESP_LOGW(TAG, "failed to create action websocket");
        scheduleReconnect();
        return false;
    }

#ifdef CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_TOKEN
    if (CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_TOKEN[0] != '\0') {
        std::string token = "Bearer ";
        token += CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_TOKEN;
        websocket_->SetHeader("Authorization", token.c_str());
    }
#endif
    websocket_->SetHeader("Protocol-Version", "1");
    websocket_->SetHeader("Device-Id", SystemInfo::GetMacAddress().c_str());
    websocket_->SetHeader("Client-Id", Board::GetInstance().GetUuid().c_str());
    websocket_->OnData([this](const char* data, size_t len, bool binary) {
        if (!binary) {
            handleText(data, len);
        }
    });
    auto notify = std::make_shared<std::atomic<bool>>(false);
    notify_disconnect_ = notify;
    websocket_->OnDisconnected([this, notify]() {
        connected_.store(false);
        if (!alive_->load() || !notify->exchange(false)) {
            return;
        }
        auto alive = alive_;
        Application::GetInstance().Schedule([this, alive]() {
            if (alive->load()) {
                resetSocket();
                scheduleReconnect();
            }
        });
    });

    ESP_LOGI(TAG, "connecting action gateway: %s", CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL);
    if (!websocket_->Connect(CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL) ||
        !websocket_->Send(helloMessage())) {
        resetSocket();
        scheduleReconnect();
        return false;
    }
    notify->store(true);
    scheduleHandshakeTimeout();
    return true;
#else
    return false;
#endif
}

std::string McpActionClient::helloMessage() const
{
    cJSON* root = cJSON_CreateObject();
    cJSON_AddStringToObject(root, "type", "hello");
    cJSON_AddNumberToObject(root, "version", 1);
    cJSON* features = cJSON_CreateObject();
    cJSON_AddBoolToObject(features, "mcp", true);
    cJSON_AddItemToObject(root, "features", features);
    cJSON_AddStringToObject(root, "transport", "websocket");
    char* text = cJSON_PrintUnformatted(root);
    std::string result = text == nullptr ? "" : text;
    if (text != nullptr) {
        cJSON_free(text);
    }
    cJSON_Delete(root);
    return result;
}

void McpActionClient::handleText(const char* data, size_t len)
{
    cJSON* root = cJSON_ParseWithLength(data, len);
    if (root == nullptr) {
        ESP_LOGW(TAG, "invalid action gateway JSON");
        return;
    }
    auto type = cJSON_GetObjectItem(root, "type");
    if (cJSON_IsString(type) && strcmp(type->valuestring, "hello") == 0) {
        auto session = cJSON_GetObjectItem(root, "session_id");
        if (cJSON_IsString(session) && session->valuestring[0] != '\0') {
            session_id_ = session->valuestring;
            connected_.store(true);
            stopTimer();
            reconnect_policy_.reset();
            ESP_LOGI(TAG, "action gateway connected, session=%s", session_id_.c_str());
        }
    } else if (cJSON_IsString(type) && strcmp(type->valuestring, "mcp") == 0) {
        auto payload = cJSON_GetObjectItem(root, "payload");
        if (cJSON_IsObject(payload)) {
            McpServer::GetInstance().ParseMessage(
                payload, [this](const std::string& reply) { sendMcpReply(reply); });
        }
    } else if (cJSON_IsString(type) &&
               (strcmp(type->valuestring, "tts") == 0 ||
                strcmp(type->valuestring, "listen") == 0)) {
        ESP_LOGW(TAG, "ignoring audio event on action channel");
    }
    cJSON_Delete(root);
}

void McpActionClient::sendMcpReply(const std::string& payload)
{
    auto alive = alive_;
    Application::GetInstance().Schedule([this, alive, payload]() {
        if (!alive->load() || !connected_.load() || websocket_ == nullptr) {
            return;
        }
        cJSON* root = cJSON_CreateObject();
        cJSON_AddStringToObject(root, "type", "mcp");
        cJSON_AddStringToObject(root, "session_id", session_id_.c_str());
        cJSON* jsonPayload = cJSON_Parse(payload.c_str());
        if (jsonPayload == nullptr) {
            cJSON_Delete(root);
            return;
        }
        cJSON_AddItemToObject(root, "payload", jsonPayload);
        char* text = cJSON_PrintUnformatted(root);
        if (text != nullptr) {
            websocket_->Send(std::string(text));
            cJSON_free(text);
        }
        cJSON_Delete(root);
    });
}

void McpActionClient::scheduleReconnect()
{
    if (!alive_->load() || timer_ == nullptr || timer_armed_.exchange(true)) {
        return;
    }
    timer_purpose_.store(TimerPurpose::Reconnect);
    const auto delay = reconnect_policy_.consumeDelayMs();
    if (esp_timer_start_once(timer_, delay * 1000ULL) != ESP_OK) {
        timer_armed_.store(false);
        timer_purpose_.store(TimerPurpose::None);
    }
}

void McpActionClient::scheduleHandshakeTimeout()
{
    armTimer(TimerPurpose::HandshakeTimeout, kHandshakeTimeoutMs);
}

bool McpActionClient::armTimer(TimerPurpose purpose, uint32_t delayMs)
{
    if (!alive_->load() || timer_ == nullptr) {
        return false;
    }
    stopTimer();
    timer_purpose_.store(purpose);
    timer_armed_.store(true);
    if (esp_timer_start_once(timer_, delayMs * 1000ULL) != ESP_OK) {
        timer_armed_.store(false);
        timer_purpose_.store(TimerPurpose::None);
        return false;
    }
    return true;
}

void McpActionClient::stopTimer()
{
    timer_armed_.store(false);
    timer_purpose_.store(TimerPurpose::None);
    if (timer_ != nullptr) {
        esp_timer_stop(timer_);
    }
}

void McpActionClient::resetSocket()
{
    stopTimer();
    connected_.store(false);
    session_id_.clear();
    if (notify_disconnect_) {
        notify_disconnect_->store(false);
        notify_disconnect_.reset();
    }
    if (websocket_ != nullptr) {
        websocket_->Close();
        websocket_.reset();
    }
}

void McpActionClient::shutdown()
{
    alive_->store(false);
    resetSocket();
    if (timer_ != nullptr) {
        esp_timer_delete(timer_);
        timer_ = nullptr;
    }
}

}  // namespace ar_aipet
