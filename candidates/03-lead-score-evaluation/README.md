# forensicds/lead-score-evaluation-03

Selective-label / evaluation-population incident in an inbound lead-score model.

- **Agent sees:** a RevOps memo (evaluation shows the model much stronger; Sales wants to retire the exploration
  holdout; inbound conversion flat) and a lead_eval repository at `/workspace` with a SQLite RevOps extract.
- **Hidden root cause:** lead_eval 2.0 evaluates every matured lead because lifecycle v2 records outcomes for all.
  The score estimates conversion if worked, and routing on the score decides who is worked, so the evaluation
  rewards the model for its own routing.
- **Correct repair:** evaluation population = exploration holdout as assigned at intake (intent-to-treat).
- **Verifier:** behavioural checks on the default as-of date and three hidden extracts; binary reward.

Design: `research/task03_design.md`. Validation: `report/task03_validation.md`. Dev tooling: `tools/task03/`.
