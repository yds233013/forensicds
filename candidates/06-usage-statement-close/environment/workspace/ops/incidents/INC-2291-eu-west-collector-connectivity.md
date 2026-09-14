# INC-2291: eu-west edge collector connectivity loss

Severity 3. Resolved. Owner: Edge Platform.

- **2026-08-30 14:02 UTC:** eu-west collectors lose connectivity to the landing service after a network change at the
  edge site. Meters keep reporting; collectors buffer records locally.
- **2026-09-02 09:00 UTC:** connectivity restored. Collectors flush their buffers. As designed after an unclean
  disconnect, collectors also resend their recent send log (records sent in the 6 hours before the disconnect),
  because they cannot confirm which sends the landing service received.
- **Impact:** usage from eu-west customers arrived up to about 67 hours late. No records were lost. Landing volume spike
  on 2026-09-02.
- **Follow-up:** EDGE-512, alerting on collector silence longer than 30 minutes.
