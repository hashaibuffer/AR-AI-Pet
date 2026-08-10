# StackChan 构建一致性报告

生成时间：`2026-08-09T13:36:41.831435+00:00`

## 结论

- 技术上可进入烧录评审：`True`
- 用户已授权烧录：`False`
- Git：`23792aa3ec00d23a3a86146aafe60f949bb2c4d3`，dirty=`True`
- 固件 SHA256：`ac22644043bd09d0724f813bedcdb3c3cbcbe349df1424e76680866277611984`

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
| `CONFIG_SR_MN_CN_NONE` | `1` | `y` |
| `CONFIG_SR_MN_CN_MULTINET6_QUANT` | `None` | `None` |
| `CONFIG_USE_AUDIO_PROCESSOR` | `1` | `y` |
| `CONFIG_USE_DEVICE_AEC` | `None` | `None` |
| `CONFIG_USE_SERVER_AEC` | `None` | `None` |
| `CONFIG_LANGUAGE_ZH_CN` | `1` | `y` |
| `CONFIG_DEFAULT_WEBSOCKET_URL` | `""` | `""` |
| `CONFIG_DEFAULT_WEBSOCKET_FALLBACK_URL` | `""` | `""` |
| `CONFIG_DEFAULT_WEBSOCKET_TOKEN` | `<MASKED>` | `<MASKED>` |
| `CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_URL` | `"ws://192.168.50.133:8765"` | `"ws://192.168.50.133:8765"` |
| `CONFIG_STACKCHAN_MCP_ACTION_GATEWAY_TOKEN` | `<MASKED>` | `<MASKED>` |
| `CONFIG_FORCE_DEFAULT_WEBSOCKET_URL` | `None` | `None` |
| `CONFIG_DISABLE_OTA_WEBSOCKET_CONFIG` | `None` | `None` |

## 模型

```json
{
  "build_log": {
    "wakenet": [
      "wn9_nihaoxiaozhi_tts"
    ],
    "multinet": [],
    "skipped_multinet": []
  },
  "build_log_evidence": [
    "wakenet models: wn9_nihaoxiaozhi_tts (will be packaged)",
    "Copied directory: D:/projects/stackchan-b-evaluation/stackchan-mcp/firmware/managed_components/espressif__esp-sr/model\\wakenet_model\\wn9_nihaoxiaozhi_tts -> D:/projects/stackchan-b-evaluation/stackchan-mcp/firmware/build\\temp_build\\srmodels\\wn9_nihaoxiaozhi_tts",
    "Added wakenet model: wn9_nihaoxiaozhi_tts"
  ]
}
```

## 串口证据

```json
{
  "urls": [
    "ws://192.168.50.133:8765",
    "wss://api.tenclass.net/xiaozhi/v1/"
  ],
  "session_id_present": true,
  "models": {
    "wakenet": [
      "wn9_nihaoxiaozhi_tts"
    ],
    "multinet": [],
    "skipped_multinet": []
  },
  "afe_pipeline": "I (11005) AFE: AFE Pipeline: [input] -> |AEC(SR_HIGH_PERF)| ->  -> |VAD(WebRTC)| -> |WakeNet(wn9_nihaoxiaozhi_tts,)| -> [output]",
  "contains_firmware_sha256": false,
  "device_elf_sha256": []
}
```

## 发现

- **warning / dirty_worktree**：The firmware binary cannot represent the current dirty source tree exactly.
- **error / serial_not_bound_to_binary**：The serial log contains no device-originated App ELF SHA256, so a host-injected file hash cannot prove which binary ran.
