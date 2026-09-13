# Inbound lead router

Owner: RevOps Systems. Config history: `router_config_log`.

## Routing at intake

Every accepted lead is scored by the champion model and routed once at intake (a `routing_events` row):

| Policy | Queue | Rule |
|--------|-------|------|
| `exploration_holdout` | `sdr_inbound` | a random `exploration_holdout_pct`% of accepted leads, regardless of score |
| `score_threshold` | `sdr_inbound` | score >= router threshold |
| `below_threshold_nurture` | `nurture` | everything else; receives marketing email nurture, no SDR follow-up |

Rejected leads (spam, duplicates) are never scored or routed.

## Exploration holdout

The exploration holdout sends a random slice of accepted leads to the SDR queue whatever their score, so that
sub-threshold leads are not only ever seen in nurture. The draw is made once, by the intake routing decision.
Holdout leads join the same queue as threshold-routed leads.

RevOps can pause the holdout (for example during SDR capacity incidents); a pause is a router configuration
version with `exploration_holdout_pct = 0`. Sales leadership reviews the holdout share each half-year because
holdout leads use SDR capacity.

## SDR queue

SDRs work the `sdr_inbound` queue highest score first, with a first-touch SLA of 30 hours. When the queue is long,
lower-scored leads are the ones not reached within SLA; some are picked up days later, some never.

## Later routing events

| Policy | When |
|--------|------|
| `manual_rep_claim` | an SDR pulls a nurture lead into their queue (e.g. a demo request from a known account) |
| `territory_reassign` | a lead already in the SDR queue moves to another SDR pod after territory changes |

Claims and reassignments change a lead's current queue or pod; they carry no score or threshold.

## Router releases

When a new router version goes live, accepted leads routed in the previous 14 days that no SDR has worked yet are
re-evaluated under the new configuration: the router writes a new routing event with the new version, threshold and
policy (`exploration_holdout`, `score_threshold` or `below_threshold_nurture`, with the holdout draw re-applied), and
the lead moves to that queue.

## Threshold history

| Router version | From | Threshold | Holdout |
|----------------|------|-----------|---------|
| router-2025.03 | 2025-03-03 | 0.30 | 10% |
| router-2026.06 | 2026-06-15 | 0.22 | 10% |

The June 2026 change lowered the threshold after SDR headcount was added (two new reps in July).
