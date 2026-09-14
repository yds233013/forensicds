# G26: Twin incident — one real loader bug, one real mix shift that looks like a bug

Status: generation-3 detailed design. Not built. No model has been run. Replaces the rejected Task 09 design
(`research/task09_design.md`, `research/gen2_design_review.md` §2–3). Numbers are design targets.

## Workspace sketch

```
/workspace   (a git repository; history is part of the evidence)
├── README.md                                   growth_metrics: how the weekly metrics job runs
├── CHANGELOG.md                                v1.8.0 … v2.3.0 (neutral one-line entries)
├── growth_metrics/
│   ├── __main__.py                             `python -m growth_metrics run --extract <dir> --out <dir>`
│   ├── common/time.py                          day_bounds_utc(day, tz) -> naive UTC bounds (pre-existing, correct for its contract)
│   ├── loaders/events.py                       PR #418: account-local activity days (FAULTY)
│   ├── loaders/billing.py                      reads stripe_charges + app_store_notifications (correct)
│   ├── sql/v_trial_attribution.sql             PR #412: channel taxonomy v3 view (correct)
│   ├── sql/v_first_paid_charge.sql             PR #412: first paid charge per trial (correct)
│   ├── metrics/activation.py                   activation cohort metric (correct given loader)
│   ├── metrics/conversion.py                   conversion cohort metric (correct)
│   └── export.py                               writes weekly CSVs
├── seeds/excluded_email_domains.csv            internal/test domains (moved from a Python constant in PR #412)
├── config/core_actions.yaml                    activation core actions
├── data/extract/                               read-only
│   ├── accounts.csv              ~92k          account_id, created_at_utc, timezone (IANA), region, email_domain
│   ├── trials.csv                ~92k          trial_id, account_id, started_at_utc, platform(web|ios|android),
│   │                                           install_source(nullable), utm_source, utm_medium, campaign_id
│   ├── events/dt=YYYY-MM-DD/*.parquet ~21M     event_id, account_id, event_name, event_ts_utc, client(web|ios|android)
│   ├── stripe_charges.csv        ~14k          charge_id, account_id, created_at_utc, amount, currency, status, refunded
│   ├── app_store_notifications.jsonl ~190k     notification_uuid, notification_type, subtype, signed_date_utc,
│   │                                           app_account_token, transaction_info{…} (decoded JWS)
│   ├── fx_daily.csv                            date, currency, usd_rate
│   └── extract_manifest.json                   extract date, published-week range
├── published/                                  what the dashboard currently shows (export of weekly tables)
│   ├── activation_weekly.csv, activation_by_region.csv
│   └── conversion_weekly.csv, conversion_by_channel.csv, conversion_by_platform.csv
├── patches/growth-ops/0001-count-app-store-conversions.patch   teammate's proposed fix (wrong)
├── docs/
│   ├── metrics_catalog.md                      definitions: trial cohort week, conversion, activation (account-local days since 2026-08-24 decision)
│   ├── decisions/2026-08-24_activation_local_days.md   metrics council decision (why local days)
│   ├── marketing/channel_taxonomy_v3.md        channel rules, effective 2026-09-01
│   ├── vendor/app_store_server_notifications.md  internal summary of notification types and transaction fields
│   └── runbooks/weekly_metrics.md              job, publish, restatement procedure (restatement.csv format)
├── logs/
│   ├── deploys.csv                             2026-09-01 v2.2.0 (PR #412), 2026-09-02 v2.3.0 (PR #418)
│   └── parity/pr412_parity_2026-08-28.txt      old vs new pipeline on Jun–Aug cohorts
├── notes/
│   ├── marketing/2026-09_calendar.md           launches, campaigns; includes "App Store featuring (Apple editorial), from Sep 3" among 9 items
│   ├── support/2026-09-15_apac_csm_thread.md   "activation emails firing late for Sydney customers"
│   └── growth/2026-09-29_vp_growth_escalation.md  VP claim: ~9,600 iOS trials with App Store transactions not counted
└── reports/app_store_connect/subscriptions_2026-09.csv   ASC export: "subscriptions started" incl. free-trial starts
```

About 350 MB of events as Parquet (compressed ~120 MB). If this is too heavy, events are sampled to ~8M rows while
preserving ≥ 2k APAC trials per week.

---

## 1. Research question

Can an agent, handed two simultaneous metric escalations and explicitly asked to fix them, repair the one that is a
genuine pipeline defect and correctly refuse to change the other, which is a genuine population change?

The negative control must survive:

- a plausible teammate patch;
- a latent-bug hypothesis that parity testing cannot refute;
- a vendor report that seems to confirm missing conversions;
- a partial-recovery signal after the real fix that invites further "fixing".

The capability probed is epistemic discipline under a "fix it" framing: verification against definitions and raw
events, not transcription.

## 2. Enterprise setting

Tallyworks (fictional) sells a self-serve collaboration product with a 14-day free trial on web, iOS and Android.
`growth_metrics` is a Python + DuckDB-SQL job that publishes weekly cohort metrics to the growth dashboard. Conversion
rates feed the paid-acquisition bidding model; activation rates feed lifecycle email targeting.

- **Web and Android** trials pay through Stripe.
- **iOS** trials start an Apple introductory free-trial offer and convert through App Store auto-renewal. App Store
  server notifications land in `app_store_notifications`.

**Two deploys in the same week:**
- **2026-09-01, v2.2.0 (PR #412), attribution refactor.**
  - Channel derivation moved from Python into SQL views.
  - Channel taxonomy v3 adopted: `app_store` channel retired; installs without campaign attribution are `organic`.
  - The first-paid-charge logic moved to `v_first_paid_charge.sql`.
  - The exclusion domain list moved to a seed CSV.
  - Behaviour-preserving for all conversion rates; channel labels change by design.
- **2026-09-02, v2.3.0 (PR #418), activation days in account-local time.** This implements the 2026-08-24 metrics
  council decision and introduced the loader defect.

**Two external facts in the same week:**
- **2026-09-03:** Apple editorially featured the iOS app in several storefronts, mainly US and UK. Low-intent iOS trials
  surged.
- **2026-10-04:** Australia/Sydney DST starts inside the visible window.

## 3. Visible symptom

The instruction memo (Head of Data, forwarding two escalations) says:

1. **Conversion.**
   - VP Growth: trial→paid conversion "collapsed" from 14.2% (Jul–Aug cohort weeks) to 10.9% (cohort weeks from
     2026-09-07), right after the attribution refactor.
   - Growth Ops found "9,640 September iOS trials with App Store transactions that the dashboard counts as unconverted".
     They prepared a patch (`patches/growth-ops/0001-…`).
   - "Please fix conversion and restate September before bidding budgets lock."
2. **Activation.**
   - Lifecycle team: activation fell from 41.5% to 39.0% the same week.
   - APAC CSMs say Sydney customers' activity "stops showing after lunch".

Deliverables:

1. `python -m growth_metrics run --extract <dir> --out <dir>` must produce the five weekly tables in the formats already
   in `published/`. It will be re-run on other extracts.
2. `out/restatement.csv`, in the format in `docs/runbooks/weekly_metrics.md`: one row per published cell (weeks listed
   in `extract_manifest.json`) whose value changes, with the published and restated values.
3. Do not modify `data/extract/` or `published/`. No handling specific to accounts, regions, weeks or storefronts.
4. "If you conclude a metric does not need restating, say why in `out/incident_note.md`." The note is required but not
   graded numerically; see §21.

The memo *asks for both fixes*. It does not say either escalation is real or unreal.

## 4. Source distribution inspiration

- **Composition shifts after a platform or channel surge** are among the most common "broken metric" escalations in
  growth analytics (Simpson's-paradox-style mix effects).
- **App-store introductory offers.** Subscription apps selling through Apple's App Store receive server notifications
  in which a free-trial start is a transaction with zero price and an introductory offer type, and the first paid
  renewal comes later. Field names in this design are simplified and *to verify* against Apple's documentation; the
  workspace carries an internal summary doc, not vendor text.
- **Timezone bugs** from comparing local wall-clock timestamps with UTC-derived bounds are a recurring class of
  analytics defects, especially when a metric moves from UTC days to local days.
- **Teammate patches that restore a headline number** are a realistic organisational attractor.

## 5. Causal graph / ground truth

**Trials per cohort week (targets)**

| Segment (platform × install_source) | Jul–Aug per week | Conv (21d) | Sep 7–27 per week | Conv |
|---|---|---|---|---|
| web (all channels) | 4,600 | 14.9% | 4,620 | 14.9% |
| ios × app_store_search | 230 | 9.5% | 380 | 9.5% |
| ios × app_store_browse | 120 | 4.8% | 2,950 (feature) | 4.8% |
| ios × web_referrer | 60 | 12% | 70 | 12% |
| android × all | 250 | 10.0% | 260 | 10.0% |
| **Overall** | 5,260 | **14.2%** | 8,280 | **10.9%** |

- Within-segment rates are identical in expectation. Realised binomial noise is about ±0.6 pp at segment level for web
  and larger for small iOS segments.
- By platform alone, iOS falls from 8.5% to 5.5%: a within-iOS mix shift to browse. **A platform-only segmentation
  therefore shows a "within-segment" decline** (a planted second-level Simpson's trap).
- The surge is 78% Americas and EMEA storefronts, 6% APAC.
- 38% of iOS trials use Apple private-relay email domains (a realistic side effect of Sign in with Apple).

**Conversion definition** (catalog, unchanged since 2024)
- A trial converts if the account has a first paid charge within 21×24 h of `started_at_utc`.
- Paid charge means one of:
  - a Stripe charge with `status = succeeded` and `amount > 0`;
  - an App Store notification whose transaction has `price > 0`.
- Refunds do not reverse conversion.
- The cohort week is the ISO week (Monday) of `started_at_utc` in UTC.
- Trials from excluded domains are removed.

**App Store notifications (generator)**
- Each iOS trial produces `SUBSCRIBED/INITIAL_BUY` at start with `offerType = 1`, `offerDiscountType = FREE_TRIAL` and
  `price = 0`.
- Converters get `DID_RENEW` at day 14 with `price > 0`.
- Cancellers get `DID_CHANGE_RENEWAL_STATUS/AUTO_RENEW_DISABLED` then `EXPIRED/VOLUNTARY`.
- 3% of iOS trials in an August promo used `offerDiscountType = PAY_UP_FRONT` with `price > 0` at start. These are
  conversions at day 0 under the catalog definition.
- 2% of renewals go through `DID_FAIL_TO_RENEW` and then `DID_RENEW` on day 16–27. Those ≤ 21 days convert; later ones
  do not.
- `app_account_token` maps to `account_id`.

**PR #412 (conversion side): correct**
- Old Python: `charges[charges.amount > 0]` ∪ `iap[iap.price > 0]`.
- New SQL: the same predicates.
- The parity log (Jun 1–Aug 30 cohorts) shows 0 differences in overall and platform conversion.
- Channel table differences are all `app_store → organic` or `app_store → paid_social` (campaign-attributed), per
  taxonomy v3.

**Growth Ops patch** (`0001-count-app-store-conversions.patch`)
- Changes the IAP predicate to `notification_type IN ('SUBSCRIBED','DID_RENEW')`, which counts free-trial starts as
  conversions.
- Adds relay domains to excluded domains "as likely bot trials".
- Result on the visible extract: September conversion 13.8%, and iOS conversion about 70% (implausible if inspected).
- The VP's "9,640" equals the number of September-cohort (weeks 09-07..09-21) iOS trials with an `INITIAL_BUY`
  (price 0) and no paid renewal within 21 days. It is computed, not typed.

**App Store Connect export:** "Subscriptions started", including free-trial starts, with `proceeds_usd = 0` for those
rows. It seems to confirm "thousands of subscriptions".

**Activation definition** (catalog after the 2026-08-24 decision)
- An account is activated if it performs ≥ 3 core actions on ≥ 2 distinct account-local calendar days among its first
  7 local days. Day 1 is the local date of `started_at_utc`.
- Applies to all cohorts published by v2.3.0.

**PR #418 defect** (`loaders/events.py`)

```python
ev["event_ts"] = local_wall_clock(ev.event_ts_utc, ev.timezone)     # tz-naive local time (new)
for tz, idx in ev.groupby("timezone").groups.items():
    for day in days:
        lo, hi = day_bounds_utc(day, tz)          # naive UTC instants of local midnight .. next local midnight
        sel = ev.loc[idx][(ev.event_ts >= lo) & (ev.event_ts < hi)]
        sel = sel[sel.event_ts.dt.date == day]    # "keep only this local day"
```
(Actual code is vectorised with a merge on (timezone, day); the semantics are identical.)

The defect compares local wall-clock time with UTC instants.

| Offset | Effect |
|---|---|
| Positive h (APAC +8…+11, +5:30 India, EMEA +1/+2) | Window = local [D 00:00 − h, D+1 00:00 − h) ∩ date = D, so the **last h hours of every local day are dropped** |
| Negative h (Americas) | The first \|h\| hours of every local day are dropped (overnight) |
| DST transition days | 23/25-hour asymmetries |

**Activation truth (targets)**

| Segment | Jul–Aug (true) | Sep (true) | Sep published (bugged) |
|---|---|---|---|
| APAC (18% of pre-surge trials) | 44.0% | 43.6% | 30.5% (Sydney loses 14:00–24:00; Singapore 16:00–24:00) |
| EMEA | 42.0% | 41.5% | 41.1% |
| Americas | 40.8% | 39.2% | 39.0% (small: overnight loss) |
| Overall | 41.5% | 40.3% | 39.0% |

- The surge's low-intent iOS trials activate at about 23%, so **true** September activation is 1.2 pp lower than
  August.
- A correct fix therefore does not restore 41.5%. Overall activation after the correct fix is 40.3%.

**Published tables**
- Weeks through 2026-08-24 were published by v2.2 (UTC days) and are outside restatement scope.
- Weeks from 2026-08-31 were published by v2.3.0 (bugged loader).

## 6. Latent statistical/business invariant

1. **Conversion computation is correct**, and its published values from 2026-08-31 are the right numbers:
   - the refactor preserves conversion semantics;
   - free-trial starts are not paid charges;
   - private-relay trials are real trials.

   The decline is a composition change between (platform × install_source) segments with stable within-segment rates.
   Any change to conversion outputs, on any extract, is a defect.
2. **Activation must compare like with like.**
   - Event instants must be assigned to account-local dates using the account's IANA timezone, including DST and
     half-hour offsets.
   - The first-7-local-days window must be computed in the same basis.
   - The local-day definition (not UTC) is authoritative.
3. **Restatement:**
   - exactly the published activation cells whose correct value differs, including small Americas and EMEA cells, not
     only APAC;
   - no conversion cells.

## 7. Grains and state variables

| Grain | Where | Mistake if confused |
|---|---|---|
| Trial × platform × install_source × cohort week | trials | Platform-only segmentation shows a false within-segment decline |
| Channel (taxonomy v3) vs install_source | view vs raw | Channel-level "organic collapse" misread as attribution bug |
| App Store notification → transaction (offer type, price) → account → trial | notifications | Free-trial starts counted as conversions |
| Event instant (UTC) vs account-local wall clock vs local date | events, accounts | The loader defect; "fixed offset" repairs break on DST and half-hour zones |
| Account-local day index (day 1..7) | activation | UTC day windows (revert) change the definition |
| Published cell (metric × week × segment) | published, restatement | APAC-only restatement misses small Americas and EMEA changes |

## 8. Evidence graph

(★ = on the natural path.)

| Artifact | Shows | Path |
|---|---|---|
| ★ Memo, VP escalation, `patches/growth-ops/0001` | Conversion "bug", count of uncounted App Store trials, a ready patch | natural start; attractor |
| ★ `logs/deploys.csv`, `git log`, PR #412 diff | Refactor the day before the drop; diff moves the paid-charge predicate and the exclusion list; channel mapping changes | natural; attractor |
| ★ `published/conversion_by_channel.csv` | `organic` conversion drops from 13.9% to 8.1% after 09-01; `app_store` channel disappears | natural; attractor (looks like mis-attribution) |
| ★ `published/conversion_by_platform.csv` | iOS 8.5% → 5.5% ("within-segment decline") | natural; attractor |
| `reports/app_store_connect/subscriptions_2026-09.csv` | "Subscriptions started" in the thousands | reachable; attractor |
| `logs/parity/pr412_parity_…txt` | 0 conversion diffs on Jun–Aug; expected channel label diffs | reachable; *does not* refute the latent-IAP hypothesis |
| `docs/metrics_catalog.md` | Conversion = first paid charge (price/amount > 0) | must read |
| `docs/vendor/app_store_server_notifications.md` | Free-trial start: `SUBSCRIBED/INITIAL_BUY`, `offerDiscountType FREE_TRIAL`, `price 0`; first charge is `DID_RENEW` | must read or verify in data |
| `app_store_notifications.jsonl` | Uncounted iOS trials have only `price = 0` start rows and cancellation | decisive data check |
| `trials.install_source` | Browse surge; stable rates within platform × install_source | decisive for mix |
| `notes/marketing/2026-09_calendar.md` | Apple featuring on Sep 3 (one of 9 items) | reachable |
| `docs/marketing/channel_taxonomy_v3.md` | Retiring `app_store`; iOS installs without campaign → organic | explains channel table |
| ★ `published/activation_by_region.csv` | APAC collapse; EMEA and Americas slight | natural |
| ★ `notes/support/…apac_csm_thread.md` | "Activity stops showing after lunch" (Sydney) | natural |
| ★ PR #418 diff, `common/time.py` | Local wall clock vs `day_bounds_utc` | natural |
| `docs/decisions/2026-08-24_activation_local_days.md` | Local days are the definition; UTC days were the old definition | must read before any revert |
| `events/` raw | Hour-of-day histograms by tz: APAC has no events after 14:00 local in the loader output but plenty in raw | decisive |

## 9. Evidence authority hierarchy

| Conflict | Governs | Why |
|---|---|---|
| Growth Ops patch / VP claim vs metrics catalog | **Catalog** | Metric definitions are owned by the catalog; the patch is a proposal |
| ASC "subscriptions started" vs catalog "paid charge" | **Catalog + transaction price** | ASC counts offer starts; the data show price 0 |
| Parity log vs "old code shared the defect" | **Neither alone**: definition + raw data decide | Parity proves refactor = old behaviour, not that old behaviour met the definition. The agent must check the definition. |
| Channel-level conversion decline vs taxonomy v3 | **Taxonomy** | Label change by design; channel is not a stable segment across 09-01 |
| Platform-level decline vs platform × install_source | **Finer segmentation in raw data** | Install source is recorded at trial start for every iOS trial |
| Activation "revert to UTC days" vs council decision | **Decision doc + catalog** | Definition changed deliberately |
| CSM anecdote ("after lunch") vs raw events | **Raw events** | Cutoff hour depends on offset (14:00 Sydney, 16:00 Singapore, 18:30 India) |

## 10. Plausible hypotheses

| # | Hypothesis | For | Against |
|---|---|---|---|
| H1 | Refactor broke conversion | ★ timing; diff touches paid-charge predicate; channel table changes | Parity log; re-running v1.8.0 on the current extract gives identical conversion |
| H2 | Pipeline (old and new) never counted App Store conversions; the iOS surge exposed it | ★ VP count; ASC export; iOS conversion "only 5.5%" | Uncounted trials have only price-0 start transactions; `DID_RENEW` rows *are* counted |
| H3 | Bot/low-quality relay-email trials inflate the denominator | ★ 38% relay emails on iOS; many have zero events | Relay trials activate and convert at the same rate as non-relay within segment; the catalog has no quality exclusion |
| H4 | Timezone loader change broke both metrics | ★ same week; shared `common/time.py` | Conversion uses UTC timestamps from billing, not events; conversion drop is concentrated in Americas/EMEA iOS, not APAC |
| H5 | Real composition shift (true for conversion) | marketing calendar; install_source | Needs the finer segmentation |
| H6 | Real loader defect (true for activation) | CSM thread; hour histograms | — |
| H7 | Activation decline is only mix | iOS browse activates at 23% | APAC drop is too large, region-specific and hour-specific |

## 11. Why each wrong hypothesis is plausible

- **H1:** a behaviour-changing-looking diff deployed the day before a step change is the strongest prior in incident
  response. The channel table *does* change.
- **H2:** it survives parity. It is endorsed by a named teammate with a number and a patch. A vendor export seems to
  corroborate it. "Our IAP handling is incomplete" is a very common real bug. Applying the patch restores a
  believable-looking overall number (13.8%).
- **H3:** relay emails look like junk. Excluding them is a one-line seed change in a file the refactor just touched.
- **H4:** "Same week, same shared helper" is a natural unification. Fixing `common/time.py` in a way that also changes
  conversion cohort weeks is easy.
- **H7 (inverse trap):** after the correct loader fix, overall activation is 40.3%, not 41.5%. An agent expecting full
  recovery keeps editing activation. For example, it widens the window to 8 days, or counts UTC and local days.

## 12. Investigation path (≈ 40–75 actions)

| Phase | Actions | Discoveries |
|---|---|---|
| Orient | 1–8 | Memo; VP note; patch; deploys; published tables |
| Conversion, first pass | 9–18 | PR #412 diff; channel table; platform table; ASC export; apply patch in scratch → 13.8% ("fixed?") |
| Doubt | 19–28 | iOS conversion 70% under the patch is implausible *or* the agent reads the catalog; notifications JSON: offer types, price 0 |
| Parity | 29–34 | `git worktree` v1.8.0 on current extract → identical conversion (kills H1, not H2) |
| Mix | 35–42 | Segment by platform × install_source → stable rates; marketing calendar; relay-email rates within segment (kills H3) |
| Activation | 43–55 | Region table; CSM note; PR #418; hour-of-day histogram raw vs loaded per tz; decision doc (keep local days) |
| Fix | 56–62 | Aware-timestamp local-date assignment; window in same basis; DST/half-hour handling via zoneinfo |
| Validate | 63–75 | Row audits for Sydney across 10-04 DST, an India account, a New York account at 00:30 local; overall activation 40.3% explained by mix (activation by segment); conversion outputs byte-identical to before; restatement cell set |

## 13. Natural wrong implementation

**Most likely wrong end state ("fix both").**

1. Apply or adapt the Growth Ops patch (count `SUBSCRIBED` + `DID_RENEW`), possibly with relay exclusions.
2. Fix the activation loader correctly.
3. List conversion restatements for all September cells.

Numerically: conversion 13.8% (Sep), iOS 69%, and restatement rows for every conversion cell. **Fails.**

**Second most likely ("repair what the refactor changed").**

1. Revert PR #412's view to the v1.8.0 Python attribution. Conversion rates are unchanged, but channel labels revert
   to `app_store`.
2. Fix activation.

The channel table differs on every week from 09-01 → **fails**. Principled: taxonomy v3 is the governing definition.

**Third ("fix the timezone helper for both").**

1. Change `common/time.py::day_bounds_utc` to return local bounds.
2. Reuse the same helper in conversion's cohort week (ISO week in account local time "for consistency").

Cohort membership shifts for trials started near Monday 00:00 UTC. Conversion cells change by 0.01–0.2 pp →
**fails**.

**Activation-side natural wrong repairs**
- `event_ts = event_ts_utc + timedelta(hours=OFFSETS[region])` with a fixed region table → wrong for DST and half-hour
  zones (hidden_a), wrong for multi-tz regions.
- Special-case positive offsets only ("APAC bug") → Americas overnight loss remains (restatement and cells fail).
- Revert to UTC days → definition violated on all non-UTC accounts.

## 14. Second-order failure modes

1. **After rejecting the patch, "reweight conversion to the pre-surge mix"** as a "mix-adjusted conversion" in the
   main table → fails. A separate new file is ignored by the verifier but discouraged by the memo.
2. **Exclude low-intent iOS browse trials** "because they distort bidding" → fails.
3. **Count PAY_UP_FRONT offers as non-conversions** ("intro offers aren't real") → changes August iOS cells and hidden
   fixtures → fails.
4. **Extend conversion window for App Store billing retries** (21 → 28 days) → fails.
5. **Activation keeps getting "fixed"** after the correct fix, because 40.3% < 41.5% → fails.
6. **Correct loader but restatement lists only APAC**, or includes pre-scope weeks → fails.
7. **Loader fixed via `tz_localize` on naive local times without DST handling** (`ambiguous='raise'` crashes on
   hidden_a's fall-back day, or `NaT` rows dropped) → fails.

## 15. Correct repair properties

- **Conversion:**
  - no behaviour change on any extract;
  - touching conversion files is allowed only if outputs remain identical (refactoring is not graded).
- **Activation:**
  - each event instant maps to a local date with the account's IANA timezone;
  - day-1 is the local date of trial start;
  - days 1–7 are local calendar dates, which works across DST and fractional offsets;
  - ≥ 3 core actions on ≥ 2 distinct local dates.
- **Restatement:** exact published activation cells that change, with values.
- **Note:** explains why conversion is not restated. Not graded numerically.

## 16. Repair surfaces

| Surface | Change |
|---|---|
| `growth_metrics/loaders/events.py` | Required: consistent-basis local-day assignment |
| `growth_metrics/common/time.py` | Optional: add an aware helper. The existing `day_bounds_utc` is used by conversion's cohort code, so changing its behaviour breaks conversion (a planted interaction). |
| Restatement writer (new or script) | Required output |
| Conversion SQL/Python, seeds | **Must not change behaviour** |

This is deliberately a small repair surface: the difficulty is epistemic, and the multi-component property (I) is not
claimed.

## 17. Validation requirements

- **Conversion:** a decisive check that a paid charge exists. For the uncounted iOS trials, the distribution of
  (notification type, offer discount type, price) must show no `price > 0` within 21 days. This is a row-level check;
  aggregates of "App Store transactions" mislead.
- **Mix:** rates within platform × install_source are stable across periods. A direct standardisation reproduces most
  of the drop. Platform-only segmentation is insufficient.
- **Parity:** old code vs new code on the *current* extract for the conversion tables.
- **Activation:** hour-of-local-day histograms of loaded vs raw events per timezone. Row audits across a DST transition
  and a half-hour zone. After the fix, the residual overall activation gap is explained by segment mix.
- **Behavioural self-check:** conversion outputs before and after the agent's changes are byte-identical.

## 18. Hidden fixture strategy

All fixtures come from the same generator. Every mechanism is visible: DST (Sydney 10-04), India +5:30 accounts (2% of
visible), PAY_UP_FRONT offers (August promo), billing retries, taxonomy v3, and relay emails.

| Fixture | Invariant stressed | Surface change | Overfit caught | Same distribution because |
|---|---|---|---|---|
| `hidden_a` | Activation local-day correctness | APAC share 35%, many India (+5:30) and Auckland (+12/+13) accounts; Auckland DST start and Sydney/US DST *end* inside window; 14% Americas overnight activity; conversion surge from Android Play featuring instead of iOS | Fixed offset tables; positive-offset-only patch; `tz_localize` without DST handling; iOS-specific conversion hacks | DST and half-hour zones visible; Android is a visible platform with the same notification-free Stripe path |
| `hidden_b` | Conversion must not be "corrected" when rates *really* fall | **Genuine within-segment decline**: web conversion 14.9% → 12.1% after a pricing change (no mix shift); small iOS share; activation bug present at low magnitude | Mix reweighting; clamps/caps; any conversion-code change keyed to decline patterns; restatement including conversion | Same metric code; decline is a parameter |
| `hidden_c` | Definition fidelity in conversion inputs | More PAY_UP_FRONT intro offers (8%), billing retries landing day 18–26, Stripe $0 invoices for 100%-off coupons (status succeeded, amount 0; visible has 40), relay emails 60% | Patch predicate (`SUBSCRIBED`/`DID_RENEW`); "intro offers aren't conversions"; 28-day window; relay exclusion; `status = succeeded` without `amount > 0` | Each mechanism appears visibly at lower frequency |

**Named overfit pairings:**
- `fixed_offset_table` and `positive_offset_only` ↔ hidden_a.
- `mix_reweight_conversion` ↔ hidden_b (and visible).
- `intro_offer_exclusion` and `window_28d` ↔ hidden_c.
- `apac_only_restatement` ↔ visible and hidden_a.

## 19. Mutation strategy

| Mutation | Expected |
|---|---|
| `nop` | 0 (activation) |
| `oracle` (aware local-date assignment, conversion untouched, restatement) | 1 |
| `alt_sql_loader` (independent: DuckDB `timezone()` conversion and date truncation) | 1 |
| `alt_refactor_conversion_equivalent` (rewrites conversion SQL differently, identical outputs) | 1 |
| `fix_both_growth_ops_patch` | 0 |
| `fix_both_patch_plus_relay_exclusion` | 0 |
| `revert_pr412` | 0 (channel table) |
| `revert_pr418_utc_days` | 0 (activation) |
| `shared_helper_local_bounds` (breaks conversion cohort week) | 0 |
| `mix_reweight_conversion` | 0 |
| `exclude_ios_browse` | 0 |
| `activation_window_8_days` (chasing 41.5%) | 0 |
| `fixed_offset_table` | visible 0 or 1 (Sydney DST inside visible makes it 0 if the table uses standard offsets; build must check) / hidden_a 0 |
| `positive_offset_only` | 0 (Americas cells in restatement) |
| `apac_only_restatement` (correct loader) | 0 |
| `restatement_includes_conversion_zero_diffs` (rows with equal values) | 0 (runbook: only changed cells) |
| `edit_published` / `write_outputs_only` | 0 |

## 20. Alternative valid implementations

- **Activation:** any correct local-date assignment (pandas `tz_convert`, `zoneinfo`, DuckDB `timezone()`, per-account
  offsets from zoneinfo transitions). Verified by exact outputs.
- **Conversion:** any code change with identical outputs.
- **Restatement:**
  - row order is free;
  - values ±1e-9;
  - `segment` strings as published;
  - rows whose published and restated values are equal at 6-decimal publication precision are omitted.
- **The note** can be any content.

## 21. Verifier design

1. Integrity of `data/extract/` and `published/`.
2. Run the job on visible + 3 hidden extracts (unprivileged); twice on visible (byte-identical).
3. **Activation tables** equal the reference (pure-Python zoneinfo implementation of the catalog definition) exactly
   (rates at 6 dp, counts exact).
4. **Conversion tables** equal the reference, which is the *unmodified* shipped conversion code run in the verifier
   environment and also an independent pure-Python reference. The two are asserted equal at build.
5. **`restatement.csv`:**
   - visible extract: exact cell set and values vs reference (reference activation vs `published/`);
   - hidden extracts: the job must write it too, with published tables supplied inside each hidden extract;
   - there must be zero conversion rows.
6. **`incident_note.md`** must exist. It is not parsed.

**Why not grade the note numerically.** Gen2 review showed that numeric grading of a mix decomposition depends on
week, pooling and segmentation choices. Behavioural invariance on hidden_b, a genuine decline, provides the objective
negative-control signal without an enum or a prescribed decomposition.

Binary reward.

## 22. Answer-key leakage audit (with cheap-solve audit)

| Artifact | Leak? |
|---|---|
| Metrics catalog | States the conversion definition (paid charge, price/amount > 0). Unavoidable and *the* governing fact. It does not say App Store trial starts have price 0. |
| Vendor summary doc | States what notification types and fields mean (facts). Combined with the catalog, it refutes H2. **This is a two-document + one-query refutation**; see the cheap-solve audit. |
| Parity log | Refutes H1 on old cohorts only; silent on H2 |
| Decision doc | Local days are the definition; says nothing about the loader |
| Taxonomy v3 | Explains the channel table; does not mention the surge |
| Marketing calendar | Mentions featuring among 9 items, with no volume figures |
| `restatement.csv` format | Reveals that restatements are cell-level, not which cells |
| PR descriptions (git log) | Neutral ("Move attribution to SQL views; adopt taxonomy v3", "Activation days in account timezone per council decision") |

**Cheap-solve audit:**
- **"Do nothing on conversion" is the correct conversion behaviour.** An agent that ignores the conversion escalation
  entirely and fixes activation passes. This is the core headroom risk of any negative control. Mitigations:
  1. The memo explicitly requests a conversion fix and restatement.
  2. A ready patch exists and is referenced by the memo.
  3. The note must justify non-restatement.

  An instruction-following agent will engage. Still, an agent could write "conversion looks fine" without checking and
  pass.
- **One grep?** `grep -r price` over docs finds the catalog and vendor doc, which together refute the patch. An agent
  that reads both before touching the patch escapes the attractor cheaply.
- **One SQL?** `SELECT offerDiscountType, price, count(*) … GROUP BY 1,2` over uncounted trials' notifications is
  decisive. Cheap *if* the agent thinks to verify the VP's claim at row level. The Task 02/04 evidence suggests agents
  often do not.
- **Old report?** None contains segment-stable rates.
- **Restoring behaviour?** `git checkout v1.8.0 -- growth_metrics/` fixes activation's *numbers* for UTC accounts only.
  It violates the definition elsewhere and reverts taxonomy → fails.
- **Helper?** `day_bounds_utc` is correct for its documented contract (naive UTC bounds). Its misuse is the bug.
  No aware local-date helper exists.
- **Activation side is moderately easy.** Diff + histogram localises it. The task's hardness is almost entirely the
  conversion refusal plus the inverse trap (40.3% after fix).

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| Should a "mix-adjusted" conversion be added? | Memo: the five published tables keep their formats; extra files ignored; main tables graded |
| Is an intro PAY_UP_FRONT charge a conversion? | Catalog: first charge with price > 0, regardless of offer |
| Are relay-email trials excluded? | Catalog: exclusions only for internal/test domains listed in the seed |
| Conversion cohort week timezone | Catalog: UTC ISO week (unchanged) |
| Activation day 1 when trial starts late local evening | Catalog: day 1 = local date of trial start |
| Accounts whose timezone changed | Generator: none; `accounts.timezone` is static (stated in data dictionary) |
| Events before trial start | Excluded by window (catalog: "first 7 local days of the trial") |
| Ambiguous/non-existent local times | Instants are UTC; conversion to local is always defined; no ambiguity |
| Restatement scope | Runbook + manifest: published weeks from 2026-08-31 |
| Rounding of published rates | Published at 6 dp; restatement compares at 6 dp |
| Is the channel taxonomy change itself a "bug"? | Taxonomy v3 doc is approved and effective 09-01; the refactor implements it |

## 24. Expected trajectory length

35–70 tool calls. Activation takes about 20. Conversion investigation, where passing agents spend most of their
budget, takes 15–35: patch evaluation, notifications check, segmentation, parity. Restatement and reruns take about 10.

## 25. Why harder than Tasks 03/05/06

| Task 06 failure | Here |
|---|---|
| Cutoff in faulty code | Activation: the helper exists but its *misuse* is the bug; no aware helper. Conversion: the correct code *is* present, and the task is to leave it. |
| Summary already implemented | N/A |
| Natural design correct | Natural action on conversion (apply patch / revert refactor) is wrong |
| Attractor optional | The patch and VP claim are in the memo itself |
| Traps on unchosen paths | Traps are the memo's requested actions |
| One-row check enough | A one-query check refutes H2. This is a real weakness, softened only because the path to it requires doubting a named, numerically-supported claim. |

## 26. Comparison with Task 02

- **Hardness type.** Task 02 was reconstruction-hard, with the correct design known and the execution failing. G26 is
  judgment-hard: the correct action is known only after refusing a plausible one. It is closer to Task 04's
  failure mode, where agents optimised agreement with a trusted number (here, the pre-drop 14%) and broke a correct
  definition.
- **Evidence.** Task 04 is the only evidence that this pattern generates failures (2/3).
- **Expected difficulty.** Below Task 02 for careful agents; potentially comparable for agents that follow the memo's
  framing.

## 27. Benchmark risks

- **Headroom: M–H.** The design's value depends on agents engaging with the patch. If agents habitually verify
  teammate claims at row level, the task becomes an easy anchor. Mitigation options if baselines show 3/3:
  1. Make the vendor doc an unannotated field reference, so price-0 semantics must be inferred from the data.
  2. Add a second, genuinely correct-looking latent issue: some `DID_RENEW` rows carry `price > 0` but have
     `revocationDate` set. The catalog says refunds do not reverse conversion, so counting them is correct and a
     "fix" that excludes them is wrong.

  Neither adds a hidden rule.
- **"Ignore and pass": M.** An inattentive pass is indistinguishable from a careful refusal in binary reward. The
  required note is ungraded. This is a known limit of behavioural negative controls.
- **Size and runtime: M.** 21M events × 4 extracts; sampling plan in the workspace sketch.
- **Underspecification: L.** Definitions are cataloged; restatement format is in the runbook.
- **Leakage: L–M.** Catalog + vendor doc make the refutation cheap for readers.
- **Realism: H.** App Store free-trial semantics, taxonomy migrations, local-day definitions and teammate patches are
  all mundane.
- **Overlap:**
  - Task 03's mix-shift distractor (storyline changed to an app-store feature, with a two-level Simpson structure);
  - Task 06/G09 time semantics (activation side, secondary).
