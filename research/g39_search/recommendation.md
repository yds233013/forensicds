# G39 search — recommendation: **SEARCH AGAIN** (no concept proceeds to design)

## Result
0 / 12 concepts pass all gates.

| gate | outcome |
|---|---|
| separation (pre-registered, ≥ 3) | 11 / 12 fail on the panel; C2 passes at 4.07, then fails the counterexample search |
| recognition vs execution | collapses under H2 for 10 / 12 |
| correct-table | fails for all B/C concepts |

## Three structural findings (new, general)
1. **Conditional-trap coincidence.** In deterministic structural tasks, a wrong object equals the
   right one *exactly* whenever its trap is inactive in the data. It is then detectable only in
   regimes built to activate it, and building those regimes is fixture engineering.
2. **Near-equivalent aggregations recur.** Weighting and pooling variants differ by 0.1–5 % in
   realistic data (C4, B1, C1, B2, A4). This is the G36 CE06 pattern, now seen across five domains.
3. **The pinning / execution tension.** Semantic sharpness requires the contract to pin the
   definition. For deterministic normalisation and aggregation objects, pinning the definition
   *is* pinning the computation. H2 and the correct-table gate then collapse the task.

## Closest concept
**B3 (data-centre usable power headroom).** 9 / 10 wrong objects are ≥ 10 × tolerance on ≥ 2
regimes. It fails on:
- pooling across halls (a conditional trap);
- rack-increment rounding (2.8 ×, and a legitimate convention);
- H2 / correct-table collapse.

**Do not rescue it.**

## What the next search should look for (evidence-based)
- **Traps that are active by business construction in every world**, not conditional on the data
  configuration. Examples: a unit mismatch present in every record; a population rule that always
  excludes a material share.
- **Execution that remains after the definition is pinned.** This means reconstructing a *large
  missing mass* or state from evidence, as G10 does for censored demand. The contract can state the
  object without stating the computation.
- **Neither deterministic one-liners nor fine estimator refinements.** The sweet spot is
  "first-order structural correction + genuine reconstruction", which is where G10 and G05 live.

## Recommended next action (research only)
1. **Gate-calibration audit before any new search.** Re-score the frozen survivors (G05, G10, G24)
   against this exact pre-registered criterion: min over wrong objects of the p05 error on the
   second-best regime, ≥ 3 × the valid bound. Use their existing fixtures and panels only: no model
   calls, no task changes.
   - If known-good tasks also fail, the criterion is **mis-specified for its purpose**. It must be
     re-derived on principle *before* the next search, never after seeing a candidate.
   - If they pass, the criterion stands, and the next search targets the profile above.
2. Then a new search over the profile above (G10-like large-mass reconstruction with always-active
   structural traps).

**No implementation. No G39 candidate.**
