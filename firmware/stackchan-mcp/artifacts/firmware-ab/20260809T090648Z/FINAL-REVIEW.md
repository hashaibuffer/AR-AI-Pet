# SUPERSEDED - DO NOT FLASH: fixed-offset OTA write could overwrite the current slot

This matrix remains valid build evidence, but its original device procedure
fixed the application write at `0x20000`. The current device may boot either
`ota_0` or `ota_1`, so that procedure did not prove that the installed firmware
would be preserved. Use matrix `20260809T094038Z` and its guarded inactive-slot
workflow instead.

# StackChan / Kimito / Xiaozhi historical pre-flash review

This is the current candidate matrix. It was built with native ESP-IDF v5.5.4
PowerShell. No serial port, backup, reset, or flash operation was performed.

## Product ownership proved by effective firmware configuration

For variants A through E:

- `protocol_` is the primary AI.AGENT/Xiaozhi voice and session owner.
- The primary build-time URL/token are empty and are not forced.
- OTA WebSocket configuration is enabled, so the official activation/NVS
  Xiaozhi endpoint remains authoritative.
- `McpActionClient` uses the local `ws://192.168.50.133:8765` gateway only for
  MCP actions. It rejects TTS/listen events and cannot mutate voice state.
- Kimito, Unity, Beam Pro, AR, and other MCP clients reach the device through
  the gateway's `http://127.0.0.1:8767/mcp` surface.

Variant F deliberately proves the alternative ownership model: local MCP is
the forced primary single-shot session, and the second action socket is off.

## Verification gates

- Firmware Python configuration/report/device-session tests: 23/23 passed.
- Firmware C++ host state-machine tests: 15/15 passed.
- StackChan gateway: 719 passed, 6 optional-dependency skips; ruff passed.
- Kimito brain gateway: 126/126 passed; TypeScript typecheck passed.
- Kimito offline full-contract dry run passed: voice-turn, silent/quiet/auto,
  persistent scene switch, auth, presence, TTS shim, morning, and observation.
- Six complete firmware bundles: application and merged-image hashes match;
  eight required bundle files are present in every variant.
- Matrix records `flash_invoked=false`; host managed config was restored.

## Final candidate matrix

| Variant | Audio difference | Transport | App SHA256 | Full-image SHA256 |
|---|---|---|---|---|
| `a-wakenet` | WN9 baseline, no AEC | Xiaozhi + action | `a560cb5430ed91833078a6f44dda5460b5c613da318013e77259499bd7693c1d` | `e2b87fc98fc2304f3496987915c70f23b2733f26cccf432fc21bd12744a6f311` |
| `b-wakenet-mn6-flag` | WN9; MN6 selected but asset skipped | Xiaozhi + action | `cfd5ab811431b11eeeda29de490a27989f316bcfb76fd5b85caa37c95a591f8c` | `70c90aa125e36577a58276ee8cb69d5ea8db793831e7373d37244f813fba24f8` |
| `c-custom-multinet` | `mn6_cn + fst` packaged | Xiaozhi + action | `26c9a9f692d97fbf4fdc264473c976035c1b281a7800d268bf375dbc5f54261b` | `ef3039df130cc4914013e5bcb72743e1f4ebfa168a87751079878295a7f1ecb3` |
| `d-wakenet-device-aec` | WN9 + device AEC | Xiaozhi + action | `cc32bf1b7329e41c57c5b2f97d9d659ab39bfab1468194f02be2f1cccb0bb3b6` | `e0f8b6b309d5b7854e46cd319ddce73a212b15908be46b25dccae1b2f79e5c1e` |
| `e-wakenet-server-aec` | WN9 + server AEC | Xiaozhi + action | `8c9c0d237148728fa8be1e226671c44db4926e1e1fd7d8393f56471c9d294704` | `6139f9a4978cb33cb4e8ddf1f56e6985cd3b84a7e540af6aa15f28c9698dbf1b` |
| `f-mcp-single-shot` | WN9 behavior control | Local MCP primary | `53d1b60f8d0e94bb58fe1030527b2ce4b249d109f1fe42767fd5c30c69b383df` | `f558fa35d510a352a75f2c88d68926022259dfc9d855541dc67d4d169d76075a` |

## Guarded real-device procedure after explicit user authorization

Use `firmware/scripts/device_ab_session.py`. Its default is plan-only.

1. Read and hash the current COM7 full 16 MiB image before any write.
2. Require the selected candidate's exact application SHA as the authorization
   argument.
3. Routine A/B writes only `xiaozhi.bin` at `0x20000` and
   `generated_assets.bin` at `0x800000`. This preserves NVS, Wi-Fi, activation,
   partition table, and the existing rollback path.
4. `merged-binary.bin` is never used for routine A/B; it is recovery evidence.
5. Capture serial without DTR/RTS toggles. The log header binds variant, app
   SHA, assets SHA, and pre-flash backup SHA.

Recommended order: A -> B for the hidden MN6 flag claim; then A -> D -> E for
AEC. C is a local wake-word false-accept/false-reject test, not a cloud Chinese
ASR test. F only compares local MCP turn semantics and touch PTT.

## Remaining evidence and known limitation

- COM7 is visible, but no new candidate has been flashed or booted.
- `McpActionClient` currently connects once at boot. Start the local gateway
  before reboot for this acceptance session; reconnect/backoff is a later UX
  hardening item.
- `AR-AIPet/services/agent-service` is currently a data/state service, not an
  AI voice runtime. In A-E the external Xiaozhi service is the voice brain.
  Kimito's local brain is separately proven by stub contracts and is used by
  the F/local-MCP architecture, not allowed to compete for A-E audio ownership.
- The full product claim still needs real boot logs, Xiaozhi reply loop,
  action-channel tool proof, touch PTT observation, and controlled A/B scores.

No statement in this report authorizes a device write.
