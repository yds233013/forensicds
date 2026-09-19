# G31 proposed artefact graph (not built)

Sketched only after the statistical design was settled. **Nothing here exists; no `candidates/g31-*` directory has
been created.** The purpose of this note is to check that the invariant can be distributed across *operational*
sources without either fragmenting it artificially or handing it over in one file.

## Proposed workspace

```
warehouse.sqlite
  authorisations        auth_id, ts, merchant_id, segment, amount, ... pre-decision features
  risk_scores           auth_id, model_version, score            (v6 rows and v7 shadow rows)
  auth_decisions        auth_id, decision, reason_code, policy_version, bypass_flag
  review_queue          auth_id, queued_ts, worked_ts, analyst_id, determination, sla_breach
  chargebacks           auth_id, posted_date, reason_code, amount
  merchant_segments     merchant_id, segment, mcc, onboarded_on
  policy_versions       policy_version, effective_from, block_threshold, review_threshold,
                        bypass_rate_block, bypass_rate_review

docs/
  risk/decisioning_policy.md      band thresholds; what BLOCK/REVIEW/ALLOW mean operationally
  risk/bypass_programme.md        why the bypass exists, how the rate is set, that it is randomised
  ops/chargeback_operations.md    dispute windows, posting lag, why lag differs by segment
  ops/review_queue_runbook.md     triage is score-ordered; SLA breach means auto-decline
  model/v7_release_notes.md       what v7 changed; that it ran in shadow, driving nothing
  finance/fraud_loss_policy.md    loss is measured in value, not count; the intervention budget

analysis/
  risk_science_readout.md         the incident: "61% -> 78%, ship it"
  legacy_eval.py                  the code behind it (30-day cutoff, settled rows only)

out/                              what the agent must produce
  model_eval.csv                  per segment: maturity_days, eligible_n, fraud_value_total,
                                  recall_v6, recall_v7, delta, adopt
  readout.json                    the per-segment recommendation
```

## What each artefact contributes, and what it deliberately does not

| Artefact | Contributes | Does **not** give away |
|---|---|---|
| `auth_decisions.bypass_flag` | the existence of the bypass | not the rate, not that it is randomised, not which bands it covers |
| `policy_versions.bypass_rate_*` | the probabilities needed for weighting | not that they must be *used* as weights, and not that the block and review rates differ |
| `risk/bypass_programme.md` | that the bypass is randomised and why the programme exists | no estimator, no formula, no mention of recall or of evaluation method |
| `ops/chargeback_operations.md` | that lag varies by segment and that disputes can arrive months later | not the horizon to use, which must be estimated from the data |
| `ops/review_queue_runbook.md` | that triage is score-ordered and SLA breach means decline | not that this makes investigator labels unusable as a representative sample |
| `chargebacks` table | the labels | nothing about which authorisations *could* have produced one |
| `risk_scores` with v7 shadow rows | both scores on every authorisation | not that v7 drove nothing (that is in the release notes) |
| `finance/fraud_loss_policy.md` | that the business measures loss in value, not count | the `W10` trap lives here: the analyst must read it, not assume |

**The single-file-giveaway check.** No document states the correction. The closest is
`risk/bypass_programme.md`, which explains that a randomised fraction of declined authorisations is allowed
through "so that the risk team can keep measuring the block band". That is a statement of *purpose*, which a
competent analyst must still convert into an estimator — and which says nothing about maturity or about the
review band's positivity problem. An agent that reads only this document and reweights by the bypass rate
produces `W9_holdout_only`, which fails.

## Evidence graph (intended discovery path)

```
readout says v7 is much better
   -> legacy_eval.py shows: settled rows only, 30-day window
      -> chargeback_operations.md: lag is much longer than 30 days, and varies by segment
         -> chargebacks table: estimate the real horizon from mature cohorts        [mechanism 3]
      -> auth_decisions: most high-score rows never settled at all
         -> decisioning_policy.md: BLOCK means no settlement, ever                  [mechanism 1]
            -> bypass_flag exists -> bypass_programme.md -> policy_versions rates
         -> review_queue_runbook.md: score-ordered triage, SLA auto-decline         [mechanism 2]
            -> determinations exist only for the top of the band
-> fraud_loss_policy.md: the budget and the loss metric are in value
-> per-segment answer
```

Four dependent discoveries, each of which changes the analysis, and none of which is sufficient alone. That is the
structure G05 had and Task 06 lacked.

## Complexity assessment

Seven warehouse tables, seven documents, one faulty analysis script. That is comparable to G05 (six tables, seven
documents) and smaller than G08. The difficulty is intended to come from the statistical reconstruction, not from
the file count: a solver that understands the observation process can produce the answer in well under a hundred
lines of pandas.
