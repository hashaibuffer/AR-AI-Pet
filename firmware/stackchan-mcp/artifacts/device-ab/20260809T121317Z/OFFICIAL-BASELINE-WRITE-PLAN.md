# Official StackChan baseline: proposed device write plan

Status: **review only; not authorized; not executed**.

## Bound evidence

- Current full 16 MiB backup SHA256:
  `906aedfcadd9244d6701d462e152e44ebc92b69afac280c23d8d80d12b14d3df`
- Secure Boot: disabled.
- Flash Encryption: disabled.
- Live partition-table SHA256:
  `4811619cacae08ef2e0e71b7220c6033a346ca5da7ca179082408c963ef530b5`
- Current active App: A in `ota_1`, image SHA256
  `38913ccf93d3a0ec815197b91e633efaa56de2a837473292bdac14aba0038884`.
- Current OTA metadata SHA256:
  `a1ed149677f974e7b1fd3b926c817a1db72ce01ca26b31929937d4ab01f5be22`.

## Candidate

- Unmodified official `stack-chan` 1.4.5 App SHA256:
  `d385fb7a2786b6a23eaed3b1df5db4fcca46756fcd677b8a92a98346b6821a87`.
- Embedded App ELF SHA256:
  `9004b1e9b04993a4da2ed8ca7cb2129db800135b991cf1ff3346691336b9594f`.
- Official assets SHA256:
  `386193a4ab06e3eb5ebb2c58499f017f24a0d2bb200b02a8382a3586ae6b3575`.
- Configuration: `zh-CN`, AFE WakeNet, official StackChan wake models,
  rollback enabled.

## Proposed guarded sequence

1. Re-read and verify the live partition table, OTA metadata, active A image,
   and complete shared assets partition. Abort before any write on any mismatch.
2. Write only the official App (3,797,904 bytes) to inactive `ota_0` at
   `0x20000`.
3. Write only official assets (2,589,204 bytes) to the shared `assets`
   partition at `0x800000`.
4. Write an 8 KiB OTA selection image at `0xd000`: copy 0, sequence 3,
   state `NEW`, SHA256
   `bfb9c9900c360d0e0d9d15edb70fb41de65775b14183fcc7e6700a1aca487bea`.
5. Reset and accept the run only if serial reports ELF SHA prefix matching
   `9004b1e9b04993a4da2ed8ca7cb2129db800135b991cf1ff3346691336b9594f`.
6. If App writing fails, leave A active and do not touch shared state. If any
   later step or boot-identity check fails, restore the complete previous assets
   partition and original OTA metadata from the new 16 MiB backup.

## Explicit non-targets

Do not write the active `ota_1`, bootloader, partition table, NVS, PHY, or any
other partition. Do not use an official merged/full-flash image.

This would preserve the current A App in `ota_1`, but it would replace the old
inactive firmware in `ota_0`. Both the pre-A backup and the new current-state
backup retain recovery copies. A new exact user authorization is required for
the three proposed writes above.
