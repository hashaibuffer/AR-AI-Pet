# StackChan device consistency report

- Variant: `a-wakenet`
- App file SHA256: `38913ccf93d3a0ec815197b91e633efaa56de2a837473292bdac14aba0038884`
- App ELF SHA256: `87800cc56e41289b20dd205dac9ad1cf16d544172c0a395a892c77067ee2cbc9`
- Device-reported ELF values: `['87800cc56e41289b20dd205dac9ad1cf16d544172c0a395a892c77067ee2cbc9', '87800cc56e41289b20dd205dac9ad1cf16d544172c0a395a892c77067ee2cbc9']`
- Build model evidence: `{"wakenet": ["wn9_nihaoxiaozhi_tts"], "multinet": [], "skipped_multinet": []}`
- Preserved original OTA slot: `0`
- Candidate OTA slot: `1`
- Full backup SHA256: `91a1baf6db14852ca39dab48d4475c05b679ba590bb235f58a7911bbde2f1b63`
- Config-model-firmware-serial consistent: `True`

The configuration and model facts are bound to the archived App ELF at build time; 
the serial gate accepts only the ELF identity reported by the running device.
A host-injected file-hash header is retained for traceability but is not boot proof.
