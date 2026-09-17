# Overnight log, 2026-09-17 (autonomous mode)

Rules in force:
- no Gemini, Claude or any other model; $0 API spend;
- no changes to frozen tasks (01–06, 02-explicit-invariant, G08, G10, G24);
- no post-hoc tolerance tuning;
- failed rounds are recorded.

| Time (PDT) | Action | Result / decision | Next |
|---|---|---|---|
| 05:01 | Checked G05 round 6: 4 regime processes, 60 calibration + 60 validation worlds each, disjoint seeds | calibration 41/60 per regime; nothing modified while running | wait; read G01 material (read-only) meanwhile |
| 13:41 | Round 6 finished (480 worlds) and adjudicated | PASS for accepted estimators (7/7 at 240/240, worst 0.92); wrong-method criterion met for 20/21; kit-conditioned DiD best-regime fail rate 59/60 = 98.3% (< 99%) recorded as an unresolved risk, no tolerance or DGP change | freeze calibration; commit |
| 13:55 | Committed G05 build + gate rounds 1-6 (a13a1a3); frozen checksums verified; secret scan clean | G05 checksum at commit 77a6e432d9d2cba2 | run 38-case mutation suite |
| 14:05 | Launched 38-case in-container mutation suite (2 jobs) | running | audits in parallel (light CPU) |
| 14:10 | Image vs cache warehouse: raw bytes differ, content digests identical (c56669651fc2f1ff) | SQLite page layout only; verifier compares content | no action |
| 14:30 | Falsification audit (estimator-based) | unconditional placebo pre-effects mean 0.0106 vs 0.0004 format-conditional; pharmacy negative control +0.0115 vs +0.0011; per-kit effects recoverable; mediator decomposition visible | diagnostics adequate |
| 14:40 | Answer-key audit on final image | no estimator recipe, transport rule, conditioning set, hidden regimes, verifier or truth in any agent-visible file | pass |
| 14:50 | Decision-shortcut audit (3 dev variants forcing STOP) | all fail effects on all 4 extracts at 2.1-11.7 tau | pass |
| 16:05 | 38-case mutation suite completed | 38/38 as expected, but 3 panel mutations scored 0 by crashing | diagnose (dev-tool bug suspected) |
| 16:15 | Diagnosed: `install_variant` injected the VARIANT dict with json.dumps, so booleans became JSON `true` (invalid Python). Dev tool only; task/verifier untouched | fixed in tools/g05/{quickcheck,shortcuts}.py | rerun the 3 cases |
| 16:35 | Panel mutations rerun (local + container) | effects within 0.02-0.31 tau, panel check catches them: planned dates 17,004 rows, txns-comparability 4,642, event-week origin 83,616; container: 4 failed = visible + 3 hidden panel checks | suite report updated |
| 17:10 | Harbor oracle/nop on final task | oracle 1 (14 passed), nop 0 (10 failed) | harbor check |
| 17:30 | harbor check | 11/11 pass | clean clone |
| 17:50 | Clean clone: rebuild + oracle/nop | same checksum 77a6e432d9d2cba2, warehouse digest c56669651fc2f1ff, no tests/solution, oracle 1, nop 0 | finalize report, freeze |
| 18:10 | G05 frozen: report finalised, committed (0b86b03), tree clean | checksum 77a6e432d9d2cba2; frozen checksums unchanged; secret scan clean | G01 design gate |
| 18:40 | G01 fresh design gate written: REDESIGN (cut holdout/IPW duplicating G24 and the treatment estimand duplicating G05; policy acts on label availability) | decision recorded | build Phase-0 sim |
| 19:20 | G01 Phase-0 iteration 1 | wrong analyses reproduce the correct status in most regimes; AUC differences <= 0.001 | retune once: status from recent evaluable vintages |
| 19:50 | G01 Phase-0 iteration 2 | W1/W2/W6/W8 separate in some regimes; W3/W4/W5/W7/W9 still never separate on status | STOP: further tuning would be fitting the DGP to the mutation list |
| 20:00 | G01 stopped and documented with three options for the maintainer | no task files created; nothing built | benchmark synthesis |
