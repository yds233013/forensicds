# recs_eval release notes

## 1.4.2 (2026-08-20)
- `ope` writes the four files in `docs/outputs/ope_outputs.md` so the launch review has one artefact.

## 1.4.0 (2026-07-02)
- Offline gate: replay a candidate ranker on logged responses and report clicks per matched impression, scaled to a
  five-slot row (`CTR@5`).
- Gate runs on production-stream responses, where the candidate lists are logged.

## 1.3.0 (2026-05-11)
- Candidate list logging (`rec_candidates`) sampled for production traffic; all exploration requests are logged.
