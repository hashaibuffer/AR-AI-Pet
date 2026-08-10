# StackChan / Kimito / Xiaozhi controlled-device readiness review

This is the only current firmware candidate matrix. It was built natively from
the ESP-IDF 5.5 PowerShell environment (`ESP-IDF v5.5.4`, Python 3.11.2).
The separately authorized read-only COM7 phase queried device security and
backed up the complete 16 MiB flash. A later, explicit phase-2 authorization
wrote only A to inactive `ota_1`, the A assets image, and OTA metadata.
`matrix.json` still correctly records that the build-matrix process itself
never flashed a device.

## Product-chain ownership

- StackChan owns the physical body: microphone, speaker, display, touch,
  camera, head motion, and device-local safety.
- AI.AGENT/Xiaozhi owns voice transport, wake-triggered conversation state,
  cloud ASR/LLM/TTS, and the primary WebSocket session in A through E.
- Kimito is the behavior/companionship presentation layer. It observes
  AI.AGENT state/emotion and invokes physical MCP actions through a separate,
  action-only WebSocket. It cannot start TTS/listening or take over audio.
- Beam Pro, Unity, AR, and other MCP clients should enter through the gateway
  action surface, not open a second voice owner on the firmware.
- F deliberately selects the alternative local MCP single-shot/PTT behavior
  and must not be mixed into Xiaozhi ASR/AEC scoring.

## Current verification evidence

- Firmware configuration/build/device-safety Python tests: 44/44.
- Firmware C++ host tests: 17/17, including Xiaozhi/MCP turn transitions,
  touch PTT, and action-channel backoff reset/cap.
- StackChan gateway: 720 passed, 6 optional-dependency skips; ruff passed.
- Kimito gateway: 126/126; TypeScript typecheck passed.
- Kimito companion: 4/4 Python tests, including MCP Bearer authentication and
  Chinese-first remote-STT fallback policy; Python compilation passed.
- Six clean ESP-IDF builds: every required bundle file exists; App, embedded
  ELF, assets, and merged recovery-image hashes recompute; every consistency
  report has zero errors and `technical_ready_for_flash_review=true`.
- Device plan mode for A was run from ESP-IDF 5.5.4 and printed the guarded
  security/16 MiB backup plan. The later, separately authorized read-only phase
  produced the device evidence below and never used `merged-binary.bin` as a
  write source.

## Reliability changes included in this matrix

- `XIAOZHI_CONVERSATIONAL` returns automatic/realtime turns to listening after
  `tts.stop`; manual PTT returns to idle. `MCP_SINGLE_SHOT` always returns idle.
- LCD touch PTT starts/stops an explicit manual turn without taking ownership
  away from Xiaozhi automatic sessions.
- A wake word received while the persistent Xiaozhi socket is already open now
  enters the required Connecting hand-off before continuing; later wake words
  are no longer silently dropped.
- The Kimito action WebSocket retries when the gateway starts late or
  disconnects. Backoff is 5, 10, 20, 40, then 60 seconds capped; a valid server
  hello resets it. A 10-second hello deadline detects half-open handshakes.
  Intentional teardown disarms callbacks/timers, and temporary socket creation
  failure also retries. Audio/session frames remain rejected on this channel.
- Windows asyncio TTS pacing rechecks monotonic deadlines after early timer
  wakeups, preventing bursts after a producer pause.

## Speech-model finding

The official embedded Xiaozhi history shows the important policy boundary:

- `d2e99ba` (2025-09-16) packaged selected MultiNet models even when
  `USE_CUSTOM_WAKE_WORD` was off. The default AFE path still instantiated
  WakeNet, so the extra MN6 was not an explicit Chinese-ASR detector path.
- `d3e7fee` (2025-09-22) made wake implementation an exclusive
  `WAKE_WORD_TYPE` choice and skipped MN6 packaging unless custom wake word was
  enabled. The current project inherits this behavior.

In this final matrix A and B are both 3,095,744 bytes. They differ in only 67
bytes, all within ESP-IDF build-time, embedded ELF identity, and trailing image
checksum/hash spans. Their assets SHA is identical:
`96f804117e749d3bacd938a5039b4aab47629ebe5cd6010792497b0bfe8c9d98`.
`matrix.json.comparisons[0].behavior_payload_equal=true`; B is therefore a
blinded negative control for procedure/backend/room variance, not a causal
recognition variant.

C has distinct assets SHA
`913ef986199d61af460ccfde7a34c659d60a93fb848d1876f377ac56fd18188f`
and a validated runtime route `ni hao xiao zhi` -> `你好小智` -> `wake`, language
`cn`. C tests local wake-command acceptance only; it does not improve or replace
Xiaozhi cloud transcription after wake.

## Final candidate hashes

| Variant | Purpose | App SHA256 | Device ELF SHA256 | Full recovery image SHA256 |
|---|---|---|---|---|
| `a-wakenet` | Xiaozhi + WN9 baseline, no AEC | `38913ccf93d3a0ec815197b91e633efaa56de2a837473292bdac14aba0038884` | `87800cc56e41289b20dd205dac9ad1cf16d544172c0a395a892c77067ee2cbc9` | `899668e08f37077bf6d8eb4ce3dd5271f3c86b5620f5b08a4d492eba8f38c312` |
| `b-wakenet-mn6-flag` | Blinded negative control; behavior/models equal to A | `3df8201afbf5863ad90079bde0a5211a1e9adbc57cd4285a0923190311327b6b` | `912aff5bb9006015095e81b73e763a0f001c12316960eda027b986a3f97d414b` | `8441d11f7a6ea144d7e7f780b6ec281bb05bd1745ed5876a51a9a9f108382d26` |
| `c-custom-multinet` | Real Chinese MN6 command route | `48a9c9ddf60a3dcb1ca31b0fb7b745bc957bceaf5136c3c1151a4d770a3bedd7` | `c89aa578753700c1b3dc75cbfa4dcd1747e0648ca0c033e1a95428abee19e6f3` | `1bc35036f81cd22b2da7beb5846246c4dddae897eb4e41a46fc7f64aaaf284f6` |
| `d-wakenet-device-aec` | WN9 + device-side AEC | `c1b3f49753e4229f5a9f945056d2b3487ba95503a6e6e6719a4be145251dff0f` | `b7801369762d6e74d68039c06836f5c5ac0cae7029c39547ac726c1741949622` | `a3c69fe918fa890c1cea180e4e7ad237c7385477472255c8ee725a17eb2b0744` |
| `e-wakenet-server-aec` | WN9 + server-side AEC flag | `9ff633900f6133d1191c30dec16ca4d3f1da1b59dd00e18d7291f688f20a73e3` | `dcee79c1ff5f58e7a9876c38606fa70fcb96d034b6bb6d68a2222097b1d82aec` | `8c1f5613c4847444c3bc393635854284adc3e3c6eb6e28f087be4d5462a3b06a` |
| `f-mcp-single-shot` | Local MCP single-shot + touch PTT | `e0a3eb610d5cb2bb5211bc7ae5f97b4516501a20213ab186537889131b78cbd3` | `50394827b0644e95b9a34427112934efc88a6479830c53871da8c7ef6274173c` | `d8d55cec753da25b278017898baa6b8799bae2b9c34bab1af66d1db09596c0ad` |

## Read-only COM7 evidence

The authorized phase-1 session is archived under
`artifacts/device-ab/20260809T105938Z`:

- Device: ESP32-S3 QFN56 revision v0.2, MAC `80:45:6b:54:7d:10`.
- Secure Boot: disabled. Flash Encryption: disabled.
  `SPI_BOOT_CRYPT_CNT=0x0`.
- Full backup: exactly 16,777,216 bytes, SHA256
  `91a1baf6db14852ca39dab48d4475c05b679ba590bb235f58a7911bbde2f1b63`.
- The device partition-table bytes exactly equal the A candidate table,
  SHA256 `4811619cacae08ef2e0e71b7220c6033a346ca5da7ca179082408c963ef530b5`.
- Current boot selection is valid OTA copy 0, sequence 1, active `ota_0` at
  `0x20000`. Its complete 4,128,768-byte partition SHA256 is
  `b9f6f4dd4eced9becc0bcd07cc11b2bbb526b8720f5d3645b1a276a124ef20c3`.
- The inactive target is `ota_1` at `0x410000`, size 4,128,768 bytes. The A
  candidate App is 3,095,744 bytes, so it fits without touching `ota_0`.
- Extracted rollback assets are exactly 8,388,608 bytes, SHA256
  `04fb4df733c30f734f5eb308d757aaa09d0c46dfcaf89d6959487cda23509a5a`.
- Extracted rollback OTA metadata are exactly 8,192 bytes, SHA256
  `8ba3b110139f45443d4f268d1a3373ef99a1718b71d51664531b83ee2d4b91a3`.
- Both rollback files were independently compared byte-for-byte with their
  corresponding slices in the full backup. The generated next OTA record was
  also independently regenerated and selects copy 1, sequence 2, `ota_1`.
- The active boot image itself is a valid appended-SHA ESP image: project
  `xiaozhi`, version `2.2.6`, ESP-IDF `v5.5.2`, secure version 0, build
  `Aug 7 2026 11:16:33`, size 3,083,760 bytes, ELF SHA256
  `5805934a78ba59516feccca6fbeeeca17ce293db7f6f46497309ba543d1c9ae7`.
  Its file SHA256
  `21751d2575e94900eb7f3657ee1e37909c40aa2e4d12dcff6456c24834ed7592`
  exactly matches the archived pre-change baseline under the first A/B run.
  Non-erased bytes after the valid image are historical OTA-slot residue; they
  are outside the signed image length, and the complete original `ota_0` is
  left untouched.

This evidence permits a separate phase-2 decision; it does not authorize a
write.

## A baseline real-device result

The explicitly authorized A session is archived under
`artifacts/device-ab/20260809T111902Z`:

- Immediately before writing, live partition-table, otadata, active App and
  complete 8 MiB assets evidence matched the approved phase-1 backup.
- App SHA256
  `38913ccf93d3a0ec815197b91e633efaa56de2a837473292bdac14aba0038884`
  was written only to `ota_1 @ 0x410000`; esptool verified its data hash.
- Assets SHA256
  `96f804117e749d3bacd938a5039b4aab47629ebe5cd6010792497b0bfe8c9d98`
  and the generated 8 KiB OTA record were separately written and verified.
- The first boot reported the exact candidate ELF SHA256
  `87800cc56e41289b20dd205dac9ad1cf16d544172c0a395a892c77067ee2cbc9`.
  The configuration-model-firmware-serial consistency gates are all true.
- Runtime reported `XIAOZHI_CONVERSATIONAL`, LCD touch PTT enabled, WN9
  `wn9_nihaoxiaozhi_tts`, a WakeNet AFE pipeline, Wi-Fi RSSI -41 dBm, and a
  Xiaozhi cloud Session ID.
- The action gateway was deliberately started after the device. Firmware
  retried without reset, authenticated, completed hello, and exposed 40 device
  tools. Read-only status calls and a small `yaw 0 -> 8 -> 0` body-motion round
  trip succeeded while the independent Xiaozhi voice channel remained owned by
  AI.AGENT.
- Two later Xiaozhi service-side disconnects each scheduled a 5-second retry,
  reconnected, and obtained a new Session ID. The action gateway connection
  remained independent.
- The Kimito companion itself now authenticates to the token-protected MCP
  endpoint. A live, read-only companion-originated probe reached the same
  physical device and returned an active session, head angles and touch state.
  This proves the behavior-layer-to-body route rather than only a generic MCP
  client route. Evidence: `kimito-companion-authenticated-probe.json`.
- A later no-reset, read-only 120-second serial capture produced three complete
  cloud turns. STT returned `今.`, mixed-language `今 is识日.`, and phonetic
  `Xingengfu.`; the agent replied in English on all three turns. Audio capture,
  upload, cloud turn execution and TTS therefore work, but both default Chinese
  cloud transcription and default Chinese reply policy fail. The raw serial
  evidence is `a-wakenet-chinese-default-probe.log`, SHA256
  `346bdf3f295a522b89ea17bc55e7452f5cba216b4375b4a11b8d2e726e9f2a1d`;
  its structured verdict is `a-wakenet-chinese-default-probe.json`.
- The A binary contains `CONFIG_LANGUAGE_ZH_CN=y`, `Lang::CODE="zh-CN"`,
  and sends `Accept-Language: zh-CN` during OTA activation. This proves that
  device/display language is not sufficient to set the service-owned ASR
  language prior or bound-agent response language. Those are separate test
  variables and must not be attributed to the local MultiNet wake model.

One loader defect was discovered after the successful boot: the generated
target OTA entry used IDF state `UNDEFINED`, which boots normally but bypasses
the configured `NEW -> PENDING_VERIFY -> VALID` automatic rollback state
machine. The current A image is running normally and the original `ota_0` is
still untouched, but this particular selection record is not automatic-
rollback protected. The host generator now writes `NEW` and has 42/42 passing
tests. Correcting the current 8 KiB otadata and proving the state transition
requires a separate explicit authorization.

## Guarded two-approval device workflow

Approval 1, read-only evidence collection, is complete:

1. Query Secure Boot and Flash Encryption; abort the unsigned workflow if
   either is enabled.
2. Read and SHA256-verify the complete 16 MiB flash.
3. Require the device partition table to exactly equal the candidate table.
4. Parse both OTA metadata copies with ESP-IDF CRC/state rules, identify the
   active slot, and extract original assets plus OTA metadata for rollback.

Approval 2 was separately authorized for A with the exact verified backup and
App hashes. The implemented workflow is:

1. Before the first write, read the live partition table, both OTA metadata
   copies, the current App image, and the complete shared assets partition.
   Refuse the write if any critical hash/identity differs from the approved
   phase-1 backup.
2. Write the candidate only to the non-active OTA slot. Never write the current
   App slot, NVS, Wi-Fi/activation data, bootloader, or partition table.
3. Write assets, then generated OTA selection metadata, then reset.
4. Accept the boot only when serial reports the candidate's embedded ELF SHA.
5. If a shared-state write, serial capture, or identity check fails,
   automatically attempt to restore original assets and OTA metadata. OTA
   metadata restoration is still attempted if assets restoration itself fails;
   the preserved original App slot then becomes active again.

`merged-binary.bin` is recovery evidence only and is never used by this loader.

## Real-device scoring order

1. A/B blinded negative control to establish the procedure noise floor.
2. Restore the preserved baseline between every candidate.
3. A/C wake acceptance: false accept, false reject, and wake latency only.
4. A/D/E: quiet speech, fan noise, loudspeaker idle, and device playback;
   score transcription, task success, endpoint latency, echo, clipping, and
   interruption behavior.
5. F: local single-shot turn boundary and LCD touch PTT only.
6. Restart the local action gateway after the device is already running and
   prove the action channel reconnects without disturbing Xiaozhi audio.

## Remaining unproved evidence

- A runs on the physical StackChan with verified identity; action reconnect and
  a small physical motion are proven.
- A's audio transport and cloud turn are proven, while default Chinese
  transcription and reply language are now proven failures. Wake acceptance,
  automatic post-TTS re-listening, and LCD touch PTT still need separately
  scored owner interaction.
- Corrected OTA `NEW -> PENDING_VERIFY -> VALID` and deliberate rollback to the
  preserved baseline remain unproved on COM7.
- B/C/D/E/F have not yet run on the physical StackChan. WakeNet/MultiNet/AEC
  comparisons must not begin until A's manual scoring row is complete.
- `AR-AIPet/services/agent-service` remains a data/state service, not the
  current voice runtime; A-E use the external Xiaozhi service.

Only the exact A phase-2 write recorded above was authorized. No statement in
this report authorizes another COM7 device write.
