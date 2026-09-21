# v1.1 validation — ABANDONED at the counterexample search

Order authorised: sufficiency → counterexample → natural path → IGQA → mutations → A–H → Oracle/Nop →
tamper → clean builds → identity → Harbor → freeze → checksum → replay.

| gate | status |
|---|---|
| Verifier check audit | done (`verifier_check_audit.md`) |
| Forecast-only sufficiency (§7) | PASS: every section-7 wrong analysis gets reward 0 |
| **Counterexample search (§9)** | **FAIL: CE06 gets reward 1 (max 0.29 tol). STOP.** |
| Natural-path audit | desk audit from the measured panel (no new runs) |
| IGQA | forecast PASS, decision forced, response report-only / not gradable |
| Mutation suite | in-process classification only; Docker suite not run |
| A–H, Oracle, Nop, tamper | not run |
| Verifier edit (response report-only) | **not applied**: abandoned before implementation |
| Clean builds, built-image identity | not run |
| Harbor check | not run ($0.00) |
| Freeze | not performed |
| Replay | not performed |

Agent-visible source identity is unchanged from the earlier PASS (digest `7eea3d3745160c89`). The
v1.1 candidate has no changes since commit `d9eaf9e`.
