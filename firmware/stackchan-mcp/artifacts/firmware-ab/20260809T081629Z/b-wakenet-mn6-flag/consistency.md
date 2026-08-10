# StackChan 构建一致性报告

生成时间：`2026-08-09T08:19:40.742365+00:00`

## 结论

- 技术上可进入烧录评审：`True`
- 用户已授权烧录：`False`
- Git：`23792aa3ec00d23a3a86146aafe60f949bb2c4d3`，dirty=`True`
- 固件 SHA256：`d7a5745803e84b4b91539657e64029978824c906a4733d05c6aa46b9ff2b718b`

## 配置

| 配置项 | 构建有效值 | 本地默认值 |
|---|---:|---:|
| `CONFIG_BOARD_TYPE_STACKCHAN` | `1` | `y` |
| `CONFIG_STACKCHAN_VOICE_MODE_XIAOZHI_CONVERSATIONAL` | `1` | `y` |
| `CONFIG_STACKCHAN_VOICE_MODE_MCP_SINGLE_SHOT` | `None` | `None` |
| `CONFIG_STACKCHAN_TOUCH_PTT` | `1` | `y` |
| `CONFIG_USE_AFE_WAKE_WORD` | `1` | `y` |
| `CONFIG_USE_CUSTOM_WAKE_WORD` | `None` | `None` |
| `CONFIG_SR_WN_WN9_NIHAOXIAOZHI_TTS` | `1` | `y` |
| `CONFIG_SR_MN_CN_NONE` | `None` | `None` |
| `CONFIG_SR_MN_CN_MULTINET6_QUANT` | `1` | `y` |
| `CONFIG_USE_AUDIO_PROCESSOR` | `1` | `y` |
| `CONFIG_USE_DEVICE_AEC` | `None` | `None` |
| `CONFIG_USE_SERVER_AEC` | `None` | `None` |
| `CONFIG_LANGUAGE_ZH_CN` | `1` | `None` |
| `CONFIG_DEFAULT_WEBSOCKET_URL` | `"ws://192.168.50.133:8765"` | `"ws://192.168.50.133:8765"` |
| `CONFIG_DEFAULT_WEBSOCKET_FALLBACK_URL` | `""` | `None` |
| `CONFIG_DEFAULT_WEBSOCKET_TOKEN` | `<MASKED>` | `<MASKED>` |
| `CONFIG_FORCE_DEFAULT_WEBSOCKET_URL` | `1` | `y` |
| `CONFIG_DISABLE_OTA_WEBSOCKET_CONFIG` | `1` | `None` |

## 模型

```json
{
  "build_log": {
    "wakenet": [
      "wn9_nihaoxiaozhi_tts"
    ],
    "multinet": [],
    "skipped_multinet": [
      "mn6_cn"
    ]
  }
}
```

## 串口证据

```json
null
```

## 发现

- **warning / dirty_worktree**：The firmware binary cannot represent the current dirty source tree exactly.
- **observation / mn6_flag_without_packaged_model**：MN6 is selected while Custom Wake Word is disabled; no packaged Multinet model was found in the build log. Preserve this as an A/B observation profile.
