# StackChan device consistency report

- Variant: `official-stackchan-zh`
- App file SHA256: `d385fb7a2786b6a23eaed3b1df5db4fcca46756fcd677b8a92a98346b6821a87`
- App ELF SHA256: `9004b1e9b04993a4da2ed8ca7cb2129db800135b991cf1ff3346691336b9594f`
- Device-reported ELF values: `[]`
- Build model evidence: `{"wakenet": ["wn9_histackchan_tts3", "wn9_xiaoluxiaolu_tts2"], "multinet": []}`
- Preserved original OTA slot: `1`
- Candidate OTA slot: `0`
- Full backup SHA256: `906aedfcadd9244d6701d462e152e44ebc92b69afac280c23d8d80d12b14d3df`
- Config-model-firmware-serial consistent: `False`

The configuration and model facts are bound to the archived App ELF at build time; 
the serial gate accepts only the ELF identity reported by the running device.
A host-injected file-hash header is retained for traceability but is not boot proof.
