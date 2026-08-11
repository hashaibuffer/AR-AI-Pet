#include "nanodrive_adapter.h"

#include <stdio.h>
#include <string.h>

#include "esp_log.h"

namespace {

constexpr char kTag[] = "NanoDrive";
bool initialized = false;

int clampSpeed(int value) {
    if (value > 255) return 255;
    if (value < -255) return -255;
    return value;
}

bool writeCommand(const char* command) {
    if (!initialized || command == nullptr || command[0] == '\0') {
        return false;
    }

    const int commandLength = static_cast<int>(strlen(command));
    const int sent = uart_write_bytes(NANODRIVE_UART_PORT, command, commandLength);
    const int newlineSent = uart_write_bytes(NANODRIVE_UART_PORT, "\n", 1);
    if (sent != commandLength || newlineSent != 1) {
        ESP_LOGE(kTag, "UART write failed: %s", command);
        return false;
    }

    uart_wait_tx_done(NANODRIVE_UART_PORT, pdMS_TO_TICKS(100));
    ESP_LOGI(kTag, "TX: %s", command);
    return true;
}

bool writeSpeedCommand(const char* operation, int speed) {
    char command[20];
    snprintf(command, sizeof(command), "%s:%d", operation, clampSpeed(speed));
    return writeCommand(command);
}

}  // namespace

bool nanodrive_init(void) {
    if (initialized) return true;

    const uart_config_t config = {
        .baud_rate = NANODRIVE_BAUD,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .rx_flow_ctrl_thresh = 0,
        .source_clk = UART_SCLK_DEFAULT,
        .flags = {},
    };

    esp_err_t result = uart_driver_install(NANODRIVE_UART_PORT, 256, 256, 0, nullptr, 0);
    if (result != ESP_OK && result != ESP_ERR_INVALID_STATE) {
        ESP_LOGE(kTag, "uart_driver_install failed: %s", esp_err_to_name(result));
        return false;
    }
    if ((result = uart_param_config(NANODRIVE_UART_PORT, &config)) != ESP_OK) {
        ESP_LOGE(kTag, "uart_param_config failed: %s", esp_err_to_name(result));
        return false;
    }
    if ((result = uart_set_pin(NANODRIVE_UART_PORT, NANODRIVE_TX_PIN,
                               NANODRIVE_RX_PIN, UART_PIN_NO_CHANGE,
                               UART_PIN_NO_CHANGE)) != ESP_OK) {
        ESP_LOGE(kTag, "uart_set_pin failed: %s", esp_err_to_name(result));
        return false;
    }

    initialized = true;
    ESP_LOGI(kTag, "ready: UART%d TX=%d RX=%d baud=%d tx_only=%d",
             NANODRIVE_UART_PORT, NANODRIVE_TX_PIN, NANODRIVE_RX_PIN,
             NANODRIVE_BAUD, NANODRIVE_TX_ONLY);
    return true;
}

bool nanodrive_is_initialized(void) {
    return initialized;
}

bool nanodrive_send_raw(const char* command) {
    return writeCommand(command);
}

bool nanodrive_enable(bool enabled) {
    return writeCommand(enabled ? "EN:1" : "EN:0");
}

bool nanodrive_forward(uint8_t speed) {
    return writeSpeedCommand("FW", speed);
}

bool nanodrive_backward(uint8_t speed) {
    return writeSpeedCommand("BW", speed);
}

bool nanodrive_turn_left(uint8_t speed) {
    return writeSpeedCommand("TL", speed);
}

bool nanodrive_turn_right(uint8_t speed) {
    return writeSpeedCommand("TR", speed);
}

bool nanodrive_set_wheels(int16_t left, int16_t right) {
    char command[24];
    snprintf(command, sizeof(command), "VL:%d,%d", clampSpeed(left), clampSpeed(right));
    return writeCommand(command);
}

bool nanodrive_stop(void) {
    return writeCommand("ST");
}

bool nanodrive_set_timeout(uint16_t timeoutMs) {
    char command[20];
    snprintf(command, sizeof(command), "TO:%u", static_cast<unsigned>(timeoutMs));
    return writeCommand(command);
}
