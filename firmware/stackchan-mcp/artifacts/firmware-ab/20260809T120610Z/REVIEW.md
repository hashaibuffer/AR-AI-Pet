# Official StackChan baseline compatibility review

## Decision

Use the complete `D:\sc\firmware` StackChan project as the product baseline.
Do not transplant or split its voice, UI, assets, wake-word, or Xiaozhi paths
into the modified `stackchan-mcp` firmware. Keep Kimito and AR-AIPet behind
small external interfaces.

## Verified result

- Clean ESP-IDF 5.5.4 build: pass (`stack-chan` 1.4.5).
- Host motion-math test: pass.
- Firmware language: `zh-CN`.
- Speech path: AFE WakeNet; packaged models are
  `wn9_histackchan_tts3` and `wn9_xiaoluxiaolu_tts2`; MultiNet is disabled.
- App SHA256:
  `d385fb7a2786b6a23eaed3b1df5db4fcca46756fcd677b8a92a98346b6821a87`.
- Assets SHA256:
  `386193a4ab06e3eb5ebb2c58499f017f24a0d2bb200b02a8382a3586ae6b3575`.
- App and assets fit the verified live 16 MiB partition layout.
- The official runtime finds `assets` by partition label and selects OTA slots
  through ESP-IDF, so the official App/assets need no code or binary changes.

## Deliberate compatibility layer

The official source partition table differs from the live device table. This
bundle therefore binds unchanged official App/assets to the previously verified
live partition-table evidence. The official source table is archived under
`provenance/` and is never a write payload.

## Device state boundary

No serial port was opened and no device write occurred while producing or
validating this bundle. The previous full backup predates the A installation;
it is valid recovery evidence but must not be reused to infer the current
inactive slot. Before any future official-baseline write, make a new read-only
16 MiB backup and re-evaluate Secure Boot, Flash Encryption, partition table,
OTA metadata, active App identity, and shared assets. Based on the last proven
state, A occupies `ota_1`, so an official-baseline trial would normally target
inactive `ota_0`; that requires a new exact user authorization.

Bootloader, partition table, NVS, and the active OTA slot remain forbidden.
No text in this review authorizes a device write.
