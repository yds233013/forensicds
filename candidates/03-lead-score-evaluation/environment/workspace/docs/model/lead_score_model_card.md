# Model card - inbound lead score (lsm)

Owner: RevOps Analytics. Champion: `lsm-3.2` (since 2025-03-03). Shadow challenger: `lsm-3.3-shadow` (scores
logged since 2026-06-01, not used for routing).

## What the score means

For an accepted inbound lead, the estimated probability that the lead becomes a closed-won customer within
60 days of lead creation if the router sends it to the inbound SDR queue. Training data: leads routed to the SDR
queue.

## How it is used

The inbound router (`docs/routing/inbound_router.md`) scores every accepted lead at intake and uses the score
to decide which leads go to the SDR queue. SDR capacity is limited, so the threshold determines how many leads
SDRs receive.

## Inputs

Firmographics (company size, country, industry enrichment), lead source and campaign, form fields, website
engagement before form fill. All available at intake.

## Evaluation

Monthly, by `lead_eval` (`docs/monitoring/lead_score_evaluation.md`). The evaluation is used for two decisions:
whether the champion still ranks leads well enough to route on, and where the router threshold should sit.

## Versions

| Version | Trained on leads created | Deployed | Notes |
|---------|--------------------------|----------|-------|
| lsm-3.0 | 2023-01 .. 2023-12 | 2024-02-12 | first router model |
| lsm-3.2 | 2024-01 .. 2024-12 | 2025-03-03 | added webinar/campaign features |
| lsm-3.3-shadow | 2025-01 .. 2026-03 | shadow 2026-06-01 | candidate |
