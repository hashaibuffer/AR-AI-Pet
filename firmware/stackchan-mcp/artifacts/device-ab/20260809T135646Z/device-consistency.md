# StackChan device consistency report

- Variant: `a-wakenet`
- App file SHA256: `ac22644043bd09d0724f813bedcdb3c3cbcbe349df1424e76680866277611984`
- App ELF SHA256: `2972178257309f8c18946d023697aaa3b20612b51cde74cc7f35bc29b7b6f1a4`
- Device-reported ELF values: `['2972178257309f8c18946d023697aaa3b20612b51cde74cc7f35bc29b7b6f1a4', '2972178257309f8c18946d023697aaa3b20612b51cde74cc7f35bc29b7b6f1a4']`
- Build model evidence: `{"wakenet": ["wn9_nihaoxiaozhi_tts"], "multinet": [], "skipped_multinet": []}`
- Preserved original OTA slot: `1`
- Candidate OTA slot: `0`
- Full backup SHA256: `906aedfcadd9244d6701d462e152e44ebc92b69afac280c23d8d80d12b14d3df`
- Config-model-firmware-serial consistent: `True`

The configuration and model facts are bound to the archived App ELF at build time; 
the serial gate accepts only the ELF identity reported by the running device.
A host-injected file-hash header is retained for traceability but is not boot proof.
