# StackChan / Kimito / Xiaozhi controlled-device readiness review

> **SUPERSEDED:** Do not flash this run. The current reviewed matrix is
> `20260809T104116Z`, rebuilt after action-channel reconnect hardening.

This is the current candidate matrix. It was rebuilt with native ESP-IDF
v5.5.4 PowerShell after adding a device-originated App ELF identity. No serial
port, reset, security query, backup, or flash operation was performed.

## Product ownership boundary

For A through E, the primary firmware protocol remains the external
AI.AGENT/Xiaozhi voice and session owner. OTA/NVS activation selects that
endpoint. The second local WebSocket is action-only: `McpActionClient` accepts
MCP requests, rejects TTS/listen ownership, and exposes StackChan actions to
Kimito, Unity, Beam Pro, AR, and other MCP clients through the local gateway.

F deliberately tests the alternative local-MCP single-shot model. It is a
behavior/PTT control and must not be mixed into Xiaozhi ASR/AEC scoring.

## Current verification evidence

- Firmware configuration/orchestration/device-safety Python tests: 36/36.
- Firmware C++ state-machine tests: 15/15.
- StackChan gateway: five consecutive full runs, each 719 passed and 6
  optional-dependency skips; ruff passed.
- A Windows asyncio early-wake condition was found and fixed in both buffered
  and streaming TTS pacing. Frames now re-check the monotonic deadline before
  every send instead of trusting a single sleep.
- Kimito brain gateway: 126/126; TypeScript typecheck passed.
- Current WLAN address is still `192.168.50.133`, matching the A-E action
  socket. Gateway preflight passed; a temporary live smoke test proved TCP
  8765 plus authenticated MCP initialize on 8767 (`200`, session header and
  initialize response present). The temporary process was stopped and all
  three listeners were released afterward.
- Six clean firmware builds: 8/8 required files per variant, App and full-image
  hashes recomputed successfully, zero consistency errors.
- Every App contains the full device-side `App identity ... ELF SHA256=...`
  log. Host file SHA authorizes the write; device ELF SHA proves what booted.
- The guarded loader now parses and checks the mmap asset `index.json`. A and
  B have the same assets SHA and both route to WakeNet with no MultiNet runtime
  object; C has a different assets SHA and a Chinese MultiNet command route
  (`ni hao xiao zhi` -> `你好小智` -> `wake`). The decoded text was also
  checked as Unicode U+4F60/U+597D/U+5C0F/U+667A. This proves C is wired to
  `CustomWakeWord`, not merely carrying unused model bytes.
- A/B App images are both 3,092,192 bytes. Only 68 bytes differ, all inside
  ESP-IDF build time, embedded ELF identity, and final image checksum/hash
  regions. Their assets SHA is identically
  `96f804117e749d3bacd938a5039b4aab47629ebe5cd6010792497b0bfe8c9d98`.
  `A-B-RUNTIME-EQUIVALENCE.json` records the exact ranges. Therefore A/B has
  equal executable behavior and model payload; B is a blinded negative
  control, not a causal Chinese-recognition variant.
- `matrix.json` records ESP-IDF v5.5.4 and `flash_invoked=false`.

## Historical checkbox finding

The official StackChan checkout embeds an independent Xiaozhi repository at
`firmware/xiaozhi-esp32`, remote `78/xiaozhi-esp32`, currently detached at
v2.2.4 commit `e77dedb`. Its local asset-script change is only explicit UTF-8
file decoding; the model-selection policy comes from upstream history.

- `d2e99ba` (2025-09-16) packaged every selected MultiNet model into
  `srmodels.bin`, even if `USE_CUSTOM_WAKE_WORD` was off.
- In that version, `AudioService` still instantiated AFE/WakeNet or
  `CustomWakeWord` from compile-time Kconfig. With the default AFE path active,
  a packaged MN6 model was not run as the detector. It could change image size
  and memory pressure, but there was no explicit Chinese-ASR enhancement path.
- `d3e7fee` (2025-09-22) converted wake implementation into an exclusive
  `WAKE_WORD_TYPE` choice and changed asset packaging to skip MN6 unless
  `USE_CUSTOM_WAKE_WORD=y`. The current project inherits this behavior.

This history explains why an older checkbox-only build could be binary-
different, while the current A/B pair is behavior-identical. It does not prove
that the old checkbox improved recognition; a blinded negative control is
needed to measure procedure/backend/room variance before attributing causality.

## Candidate matrix

| Variant | Isolated purpose | App SHA256 | Device ELF SHA256 |
|---|---|---|---|
| `a-wakenet` | Xiaozhi + WN9 baseline, no AEC | `1e38a7a4b86458939b2d74a2c0bbce0c5bf5eb1681148afb42a8b8b80e6278c3` | `e61554887c4ae8b7332641acfd3d2789a4b9e0a7091965d97a4aa12e2c962014` |
| `b-wakenet-mn6-flag` | Blinded negative control: MN6 flag selected, but behavior/models equal to A | `39252049e4cee5823b98d19aab67365014cfa20b58e527796c428b76712c4a89` | `c5bd058d769bf21e86187d5d23177115f8f1f0194c415e84df74530ce6a678aa` |
| `c-custom-multinet` | Packaged `mn6_cn + fst` wake-command model | `18e8e973d316a53b3a3c23eca88a80cd4002773cf9b47046fa7dabc092dcd73d` | `e64d595ecbf27e9c600e4454128450ecf1625c10b1317dd958a6bd2b0758de61` |
| `d-wakenet-device-aec` | WN9 + device-side AEC | `bdd315b22fe1b1866442bceac8969b8304393290117e9d8665ba1f16487d76a3` | `a816cb6864424035c7d181c86820a2b3892f3e6fe1e36ebd34adafdde71af00e` |
| `e-wakenet-server-aec` | WN9 + server-side AEC | `b21c10c5df28fb07abe1a9e9a99c03b0e1ab0c616a94bec1be6fc682a2769b6f` | `56e884d5d49f469bfc291e1b3a1c5ca81f1e97667ad43737a483d9c2e65e3b07` |
| `f-mcp-single-shot` | Local MCP single-shot + touch PTT control | `9215c741bf9794e51a2c0abb8d2aee23c16d416dd61962216c66b150104b4807` | `267c8ae58cfffc0143606fee66a526c7ffad51bda037fa93f5cfd1efaea073a6` |

## Two-phase device workflow

Use `firmware/scripts/device_ab_session.py` only from the configured ESP-IDF
5.5 PowerShell. Plan mode has been verified and does not open COM7.

Phase 1 is read-only evidence collection and requires separate user approval:

1. Query Secure Boot and Flash Encryption. Abort the unsigned workflow if
   either is enabled.
2. Read the complete 16 MiB flash and verify its SHA256.
3. Require the device partition table to exactly match the candidate table.
4. Parse both OTA selection copies using ESP-IDF bootloader CRC/state rules.
5. Record the current OTA slot and extract original assets plus OTA metadata as
   focused rollback files.

Phase 2 is a write and requires a second explicit user approval containing both
the verified backup SHA256 and exact candidate App SHA256:

1. Write the candidate App to the non-active OTA slot. The current App slot is
   never written.
2. Write candidate assets with no reset, then write generated OTA selection
   metadata and reset. The OTA switch happens only after App/assets succeed.
3. Capture serial and require a device-originated ELF SHA prefix/full hash that
   matches the archived candidate. A host-injected log header is not accepted
   as boot proof.
4. If any write or boot gate fails, restore original assets and original OTA
   metadata from the verified backup; the preserved original App slot becomes
   active again. NVS, Wi-Fi, and Xiaozhi activation are never written.

`merged-binary.bin` is recovery evidence only and is never used by this
workflow.

## Real-device test order after authorization

1. A versus B, blinded and randomized: use the same Mandarin script, room,
   distance, backend, and scoring. Because behavior payloads are equal, this
   measures the test method's noise floor. A repeatable material difference
   means the procedure or external state is confounded and blocks causal A/C
   or AEC conclusions.
2. Roll back to the preserved baseline between candidates.
3. A versus C: compare WakeNet/AFE wake acceptance with the actual Chinese
   MultiNet command route. Score wake false accepts/rejects and latency only;
   C is not evidence of better cloud transcription after wake.
4. A versus D versus E: quiet speech, fan noise, loudspeaker idle, and device
   playback; score transcription, task success, endpoint latency, clipping,
   echo, and interruption.
5. F: local single-shot session and touch PTT only.

## Remaining unproved product evidence

- COM7 is visible, but no candidate has been booted on the physical StackChan.
- The real Xiaozhi reply loop, action-only MCP channel, touch PTT, model/AEC
  scores, and rollback path still require device evidence.
- `McpActionClient` currently makes one connection attempt at boot; start the
  local gateway before reboot. Reconnect/backoff remains a post-acceptance UX
  hardening item.
- `AR-AIPet/services/agent-service` is a data/state service, not the current
  voice runtime. A-E rely on the external Xiaozhi service for voice/session.

No statement in this report authorizes COM7 access or a device write.
