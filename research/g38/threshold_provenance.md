# Threshold provenance — fixed BEFORE any simulation

## A. Operational trigger: rolling 3-month ppm > 1,500 → SDP enrolment next month
- **Practice.** Automotive supplier-quality manuals escalate on a *rolling-quarter* ppm, e.g.
  "Level 1 escalation / controlled shipping when 3-month rolling ppm exceeds the target by N×".
  The 3-month window is the operational norm: monthly is judged too volatile, annual too slow.
- **Level.** 1,500 ppm is the company's supplier-quality manual escalation level, 2.5 × the
  600 ppm corporate supplier target. It is a pre-existing policy value.
- **Fixed before simulation:** yes. The trigger window is **not** tuned for separation.
  `trigger_window_audit.md` only *evaluates* other windows. It never selects one.

## B. Business rollout threshold: expand SDP iff Q1 ≥ 75 defects averted per enrollee over 6 months
- **Programme cost per enrollee:** 0.25 FTE supplier-quality engineer × 6 months × $150k/yr loaded
  = **$18,750**.
- **Cost per defect reaching the plant:** $250 in finance's cost-of-poor-quality ledger (sorting,
  containment, line stoppage allocation, warranty reserve).
- **Break-even:** 18,750 / 250 = **75 defects averted per enrollee**.
- **Fixed before simulation:** yes. Neither number refers to any fixture.
