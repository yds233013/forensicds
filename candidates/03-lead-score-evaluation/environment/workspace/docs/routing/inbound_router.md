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

The exploration holdout keeps a random slice of inbound leads in the SDR queue whatever their score. It exists
so that we keep seeing how leads across the whole score range convert when SDRs work them; without it,
sub-threshold leads would only ever be seen in nurture. Holdout leads are handled exactly like threshold-routed
leads (same queue, same SLA). Holdout selection is fixed when the lead is routed at intake; later routing events
do not change it, and a holdout lead that an SDR fails to reach within SLA is still a holdout lead.

Sales leadership reviews the holdout share each half-year because holdout leads use SDR capacity.

## Later routing events

| Policy | When |
|--------|------|
| `manual_rep_claim` | an SDR pulls a nurture lead into their queue (e.g. a demo request from a known account) |
| `territory_reassign` | a lead already in the SDR queue moves to another SDR pod after territory changes |

## Threshold history

| Router version | From | Threshold | Holdout |
|----------------|------|-----------|---------|
| router-2025.11 | 2025-01-01 | 0.30 | 10% |
| router-2026.06 | 2026-06-15 | 0.22 | 10% |

The June 2026 change lowered the threshold after SDR headcount was added (two new reps in July).
