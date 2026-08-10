# Current-UI StackChan backend A-F review

## Fixed product boundary

- Device/UI source: current `stackchan-mcp` product firmware.
- StackChan official source: backend implementation reference only.
- Kimito: behavior and companionship layer.
- AI.AGENT/Xiaozhi: voice, ASR, reply policy, and conversation owner.
- Official StackChan Launcher/App UI/assets are not included.

The new A executable differs from the previously running A only in ESP build
metadata (69 bytes); the assets image is byte-identical. Therefore the current
product UI payload is preserved.

## Fixed comparison controls

- Firmware language: `zh-cn`.
- Required bound AI Agent language: `zh`.
- Touch PTT: enabled in all six candidates.
- Device partition layout and safe OTA workflow: unchanged.
- No device flash was invoked by this build matrix.

The Agent requirement is recorded in `xiaozhi-agent.local.json` and every
candidate consistency report. It still must be applied to the actually bound
Xiaozhi Agent before the next device scoring session.

## Candidates

| Variant | Purpose | App SHA256 | Packaged speech route |
|---|---|---|---|
| A `a-wakenet` | Normal WakeNet | `4190e9cbca68421d8c813068c856abb86bd80900fa26869fd71c15124dc28e5c` | `wn9_nihaoxiaozhi_tts` |
| B `b-wakenet-mn6-flag` | Chinese MultiNet checkbox-only negative control | `203bacd649ebe358bd24139d215e87bcf5ac9d036bf939aac07a8742f5d08ba5` | WakeNet; no MultiNet payload |
| C `c-custom-multinet` | Actual Chinese Custom MultiNet | `b7b4c3f05afcfa0bcc34dac1a8fe536521c0f3cf0af0373ecb71a9cc4b1de977` | `mn6_cn` |
| D `d-wakenet-device-aec` | Device AEC | `ff862ab620eaf10f121a259ecc07aecde322b73aff79af38e654190dcf729003` | WakeNet + device AEC |
| E `e-wakenet-server-aec` | Server AEC | `e91225929b5156d02866a7a68a06db60d1911e38982af10eaaec5ba9848ebb40` | WakeNet + server AEC |
| F `f-mcp-single-shot` | MCP single-shot voice mode | `d06d340e0ac3ba12a07a9fd2b3d76e519da27ab7dbe86014d831d38b21b63b7e` | WakeNet + local MCP |

All six pre-flash consistency gates pass and all six manifests retain
`flash_authorized_by_user=false`.

## A/B hidden-link evidence

A and B have equal executable behavior and equal assets. Their 68 differing
bytes are only build-time labels, embedded ELF identity, and image checksum.
This does not cancel the required physical test: B remains the blinded
checkbox-only negative control for the user's observed hidden effect.

## Host verification

- Firmware C++ behavior tests: 17/17 passed.
- Firmware configuration/build guard tests: 49/49 passed.
- StackChan MCP gateway: 720 passed, 6 skipped.
- Kimito companion: 4/4 passed.
- Kimito gateway: 126/126 passed; TypeScript typecheck passed.

## Device status and next gate

The earlier official full-UI candidate was rejected by the serial identity
gate. Its shared assets and OTA metadata were restored, and read-back proves A
in `ota_1` is active. That official App remains only in inactive `ota_0`.

Do not flash this matrix yet. First read or update the actually bound Xiaozhi
Agent so its service-owned language is `zh`; this is a cloud configuration
change and requires separate user authorization. After that, start physical
scoring from A, then blinded B, followed by C/D/E and F.
