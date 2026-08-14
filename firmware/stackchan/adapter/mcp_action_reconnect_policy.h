#pragma once

#include <algorithm>
#include <cstdint>

namespace ar_aipet {

// The action channel is optional. Backoff keeps a missing local server from
// blocking the voice application or flooding the Wi-Fi task.
class McpActionReconnectPolicy {
public:
    static constexpr uint32_t kInitialDelayMs = 5000;
    static constexpr uint32_t kMaximumDelayMs = 60000;

    uint32_t consumeDelayMs()
    {
        const auto delay = next_delay_ms_;
        next_delay_ms_ = std::min(next_delay_ms_ * 2, kMaximumDelayMs);
        return delay;
    }

    void reset() { next_delay_ms_ = kInitialDelayMs; }

private:
    uint32_t next_delay_ms_ = kInitialDelayMs;
};

}  // namespace ar_aipet
