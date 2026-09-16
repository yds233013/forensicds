# Home-row logging schema (`data/logs.sqlite`)

Times are UTC, `YYYY-MM-DD HH:MM:SS`.

**Extract composition.** The evaluation extract contains every session in the exploration stream and a random sample
of production sessions, so exploration is heavily over-represented relative to live traffic
(`serving/config/serving.yaml`). Stream membership is decided per session, before A/B assignment.

## `rec_serves` — one row per served response

| Column | Meaning |
|---|---|
| `serve_id` | id of the response |
| `session_id`, `user_id` | client session; signed-in member |
| `device` | `web`, `mobile`, `tv` |
| `surface` | placement (`home`) |
| `served_at` | when the response was returned |
| `stream` | serving stream: `prod_rank` or `explore_shuffle` |
| `ab_arm` | experiment arm for AB-1182 (`v7`, `control`, `none`) |
| `slot_1` … `slot_5` | the titles in the response, in order |
| `propensity` | probability with which the ranker produced this response |
| `candidate_count` | number of titles retrieved for the request |

## `rec_candidates` — the titles the ranker scored

Written by the ranker for a sampled share of requests (all exploration requests, a small share of production).

| Column | Meaning |
|---|---|
| `serve_id` | response the candidate list belongs to |
| `item_id` | retrieved title |
| `score_v6`, `score_v7`, `score_v7_pd` | model scores for the title on this request |
| `filter_reason` | reason the rules layer suppressed the title (`already_watched`, `licence_window`), NULL if it was not suppressed |

## `click_events` — one row per click

| Column | Meaning |
|---|---|
| `click_id` | id of the click |
| `serve_id` | response the click was attributed to |
| `click_time` | when the click happened |
| `position` | slot clicked (1–5) |
| `item_id` | title clicked |

## `items`

`item_id`, `title`, `genre`, `release_year`.
