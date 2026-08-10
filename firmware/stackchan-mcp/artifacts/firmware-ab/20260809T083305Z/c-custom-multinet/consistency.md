# StackChan 构建一致性报告

生成时间：`2026-08-09T08:35:36.379611+00:00`

## 结论

- 技术上可进入烧录评审：`True`
- 用户已授权烧录：`False`
- Git：`23792aa3ec00d23a3a86146aafe60f949bb2c4d3`，dirty=`True`
- 固件 SHA256：`79b859aaf9f756a9f80e5a53f2f2b8cb260942e60b0b45d08777f3bc4587f69d`

## 配置

| 配置项 | 构建有效值 | 本地默认值 |
|---|---:|---:|
| `CONFIG_BOARD_TYPE_STACKCHAN` | `1` | `y` |
| `CONFIG_STACKCHAN_VOICE_MODE_XIAOZHI_CONVERSATIONAL` | `1` | `y` |
| `CONFIG_STACKCHAN_VOICE_MODE_MCP_SINGLE_SHOT` | `None` | `None` |
| `CONFIG_STACKCHAN_TOUCH_PTT` | `1` | `y` |
| `CONFIG_USE_AFE_WAKE_WORD` | `None` | `None` |
| `CONFIG_USE_CUSTOM_WAKE_WORD` | `1` | `y` |
| `CONFIG_SR_WN_WN9_NIHAOXIAOZHI_TTS` | `None` | `None` |
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
    "wakenet": [],
    "multinet": [
      "mn6_cn"
    ],
    "skipped_multinet": []
  },
  "build_log_evidence": [
    "multinet models: mn6_cn, fst (will be packaged)",
    "custom wake word: ni hao xiao zhi (С)",
    "Copied directory: D:/projects/stackchan-b-evaluation/stackchan-mcp/firmware/managed_components/espressif__esp-sr/model\\multinet_model\\mn6_cn -> D:/projects/stackchan-b-evaluation/stackchan-mcp/firmware/build\\temp_build\\srmodels\\mn6_cn",
    "Added multinet model: mn6_cn",
    "Copied directory: D:/projects/stackchan-b-evaluation/stackchan-mcp/firmware/managed_components/espressif__esp-sr/model\\multinet_model\\fst -> D:/projects/stackchan-b-evaluation/stackchan-mcp/firmware/build\\temp_build\\srmodels\\fst",
    "Added multinet model: fst"
  ]
}
```

## 串口证据

```json
null
```

## 发现

- **warning / dirty_worktree**：The firmware binary cannot represent the current dirty source tree exactly.
