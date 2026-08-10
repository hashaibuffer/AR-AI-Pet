# Superseded build matrix

Do not flash any image from this run.

This matrix proved the first action-channel reconnect implementation compiled
across all six profiles. A final review then found two retry edges: temporary
`CreateWebSocket(2)` failure did not schedule another attempt, and a synchronous
disconnect during failed `Connect()` could double-advance the backoff. Both were
fixed and the complete matrix was rebuilt.

Current reviewed run: `20260809T104116Z`.
