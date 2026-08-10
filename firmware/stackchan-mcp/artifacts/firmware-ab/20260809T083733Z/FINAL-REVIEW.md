# SUPERSEDED — DO NOT FLASH FOR PRODUCT ACCEPTANCE

This historical matrix forced the primary Xiaozhi voice WebSocket to the local
StackChan MCP gateway and left the action-only socket disabled. It does not
match the final ownership boundary. Use `20260809T090648Z` instead.

# StackChan voice/audio A/B firmware historical review

Generated with native ESP-IDF v5.5.4 PowerShell. No serial-port write or flash
command was invoked. Every variant contains a complete offline flash bundle and
keeps `flash_authorized_by_user=false`.

## Verification

- Python configuration/report/orchestration tests: 18/18 passed.
- C++ host state-machine tests: 15/15 passed.
- Full bundle integrity: 6/6 application hashes and merged-image hashes match.
- Required flash files: 8/8 present for every variant.
- PC-managed profile block: restored after the build matrix.
- Detected device candidate: USB serial device on COM7 (VID 303A, PID 1001).

## Final matrix

| Variant | Isolated purpose | App SHA256 | Full-image SHA256 |
|---|---|---|---|
| `a-wakenet` | Xiaozhi conversational + WN9 baseline, no AEC | `094a3c70e31fb4646dc54f391dc647a09a3ba45f5e9c8be9919377756861de0f` | `3d3bce341e62a5bda5dd402c72aff8b5d4c3f9531db64947d88604b1daf978c6` |
| `b-wakenet-mn6-flag` | WN9 plus MN6 selection flag; MN6 asset deliberately skipped | `23c8feab32e6c04c6c8c1f27e3030636d7456d35d84826db302655023f046eb4` | `4431751c6d839edfabc248e894436593209593b43cb0b6543f1614d72b1c283b` |
| `c-custom-multinet` | Custom wake path with packaged `mn6_cn` and `fst` | `355e002399f72525fd0bf983be4182ef3955bae56b607c1419c38fec89b58aa9` | `904ea52de46303e2588217206406c8932bad80facfd4a07b58125a4a341ec2b7` |
| `d-wakenet-device-aec` | WN9 with device-side AEC | `fd6751cc65dd03394c72117ff6d52bcbb89cb94afb79091b9f9b2bd91426bdf9` | `1f0c986b5b3b7b5b2772420f740dbb7c77916bdeab81810bbe3df0c8e8a0d432` |
| `e-wakenet-server-aec` | WN9 with server-side AEC | `f12397bdf2e4ca57b78661a2856c75d362e3f4e01209c65ced8fff2b58b2317f` | `f821678faab9e990766195c3eb1675fa8b153bc7eb6881cffcc1260a2f36c316` |
| `f-mcp-single-shot` | MCP single-shot behavior control | `1024e8546f9041c80097704a64bac711ed6a9c7f45784c5fdc8b98cbc132038c` | `a2b82354b5e816a28382ad9fb4d25bbde4d5db03ff8e8aeb068e8c90c98c619a` |

## Device test order after explicit authorization

1. Read and hash the current COM7 16 MB flash before any write; save boot logs
   and the current configuration as the rollback baseline.
2. Flash A, then B. Use the same fixed Mandarin utterances, distance, room, and
   Xiaozhi backend. This directly tests the historical checkbox-only claim.
3. Flash D, then E. Test quiet speech, fan noise, loudspeaker idle, and device
   TTS playback; compare Chinese character error rate, task success, clipping,
   endpoint latency, and interruption behavior.
4. Test C separately for wake-word false reject/false accept. It is a local
   MultiNet wake model test, not evidence of improved cloud ASR transcription.
5. Flash F only to compare turn/session semantics and touch PTT; do not mix its
   single-shot behavior result into the ASR/AEC score.
6. Restore the backed-up image if any regression blocks normal use.

No step above authorizes flashing. Flashing starts only after explicit user
confirmation of the device test window and first variant.
