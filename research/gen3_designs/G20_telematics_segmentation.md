# G20: Fleet telematics trip segmentation under a firmware sampling change and device clock drift

Status: design only. Nothing built, no model run. Numbers are generator design targets, to be recalibrated at build.

## Workspace sketch

```
/workspace
├── README.md                                    pipeline overview; `python -m fleetkpi run --start --end`; outputs
├── CHANGELOG.md                                 incl. 2026-04-22 "gap_threshold_s 60 → 180 for new firmware idle heartbeat"
├── config/pipeline.yaml                         gap_threshold_s: 180, min_trip_km: 0.2, idle_speed_kmh: 3, paths
├── config/bonus_targets.csv                     vehicle class → L/100km target; idle ratio cap; min weekly km
├── src/fleetkpi/
│   ├── cli.py
│   ├── ingest.py                                reads parquet pings; sorts by (vehicle_id, received_at)  (faulty)
│   ├── segment.py                               split on gap > threshold or ignition == 0; drop trips < min_trip_km  (faulty)
│   ├── distance.py                              haversine path length over trip pings  (faulty)
│   ├── fuel.py                                  fuel = last − first fuel_used_total_l in trip  (fine given correct trips)
│   ├── idle.py                                  idle_s = count(speed < 3) × 10 s nominal  (faulty)
│   ├── attribution.py                           driver = latest card_in with device_ts ≤ trip start (receive-time based)  (faulty)
│   ├── kpi.py                                   driver × ISO week aggregation (local week)  (fine)
│   └── bonus.py                                 eligibility rules from bonus_targets.csv  (fine)
├── extract/
│   ├── pings/date=YYYY-MM-DD/part-0.parquet     ~3.4 M pings, ~95 MB, 2026-04-13 → 2026-06-07 (8 weeks)
│   └── fleet.sqlite                             vehicles, device_inventory, firmware_installs, device_config_profiles,
│                                                sync_events, driver_card_events, drivers, depots, fuel_card_transactions,
│                                                coaching_enrolments, maintenance_odometer_readings
├── docs/
│   ├── telematics/device_message_spec_v5.md     fields, triggers (periodic, ignition_on/off, motion_start/stop, heartbeat, harsh), counters, resolutions
│   ├── telematics/firmware_5.2_release_notes.md adaptive sampling; motion triggers; store-and-forward buffering "most recent first"; 20-min time sync
│   ├── telematics/device_time_and_sync.md       RTC, GNSS/NTP sync, what sync_events records
│   ├── data/data_dictionary.md                  every table/column; received_at = server receipt; device_ts = device clock
│   ├── policy/driver_performance_bonus_2026.md  definitions of trip, driving distance, fuel, idle, weekly eligibility
│   ├── pipeline/trip_pipeline_design_2024.md    original design (10 s firmware era) and its assumptions
│   └── ops/ecodrive_programme.md                coaching programme at North depot from 2026-05-04
├── reports/
│   ├── bonus/2026-Q1_statement.csv              issued Q1 (all 5.1 era)
│   ├── bonus/2026-Q2_provisional.csv            faulty pipeline output for Q2 so far
│   └── fleet_kpi_dashboard_2026-06-08.csv       vehicle × week KPIs, firmware column
├── notebooks/fw52_impact_analysis.ipynb         (generated, executed) analyst: "5.2 is more accurate; 5.1 GPS jitter inflated idle distance"
├── notes/finance/2026-06-09_bonus_query.md      (generated) Finance's overpayment concern
├── notes/fleet_ops/2026-06-02_ecodrive_results.md  (generated) coaching results for North, vs South
└── ops/incidents/INC-TEL-311_rural_coverage.md  cellular dead zones on the A-road corridor; 5.1 drops, 5.2 buffers
```

## 1. Research question

Can an agent rebuild a state segmentation (engine-on trips, idle spans) from irregular, differently-sampled,
partly-buffered telemetry whose device clocks drift? Specifically, can it:

- infer vehicle state from state-bearing signals (ignition events, cumulative counters) rather than from sampling gaps;
- place every event on a common time axis by correcting device clocks with server-observed sync offsets;
- choose the authoritative distance signal;
- while not "correcting away" a real behavioural improvement that coincides with the firmware change?

## 2. Enterprise setting

A regional freight carrier runs ~1,200 trucks from several depots.

- **Telemetry.** Each truck has a telematics unit sending GPS + CAN pings: odometer, cumulative fuel used, ignition,
  speed.
- **Pipeline.** An in-house Python pipeline turns pings into trips and driver-week KPIs.
- **Bonus.** Weekly driver bonus (€150) if fuel efficiency beats the class target by 5%, idle ratio ≤ 12%, and
  distance ≥ 800 km.
- **Firmware.** Firmware 5.2 rolled out to ~300 trucks from late April 2026.
- **Coaching.** An eco-driving coaching programme ("EcoDrive") started at North depot on 2026-05-04.
- **Extract.** The workspace holds Finance's *audit sample*: 64 trucks from two depots (North, South), 84 drivers,
  8 weeks.

## 3. Visible symptom

Memo (Finance Director):

> Trucks on firmware 5.2 "improved" fuel efficiency by 14% and halved idle time. Q2 provisional bonuses are up 2.3×
> for those drivers. Fleet Ops says EcoDrive is working and the analytics team says the new firmware simply measures
> better. I'm not paying Q2 until the numbers are right.
>
> 1. `python -m fleetkpi run --extract extract --start 2026-04-13 --end 2026-06-07` must write `out/trips.csv`,
>    `out/driver_week_kpi.csv` and `out/bonus_eligibility.csv` as described in the README. It will be run on other
>    extracts.
> 2. Trip, distance, fuel and idle must follow the bonus policy's definitions. `extract/` and `config/bonus_targets.csv`
>    are authoritative; don't modify them.
> 3. No special handling of particular vehicles, devices, drivers, dates or firmware rollout waves.
> 4. Real improvements must still be paid.

No mention of gaps, clocks, buffering or odometer.

## 4. Source distribution inspiration

- **Adaptive sampling.** Telematics devices commonly send motion-dependent samples and event-triggered records, and
  store-and-forward when out of coverage. Upload order varies by vendor.
- **Counters.** Heavy-vehicle CAN data exposes cumulative total distance and total fuel used at coarse resolutions (SAE
  J1939 PGNs for high-resolution distance and total fuel; to verify exact resolutions).
- **Trip segmentation** by fixed time-gap thresholds is a common heuristic in GPS trajectory processing and is known to
  be sensitive to sampling rate (general literature on stay-point detection; to verify).
- **Clock drift** in embedded RTCs, corrected at GNSS/NTP sync, is routine.

## 5. Causal graph / ground truth

**True world** (generator, continuous time, 1 s resolution):
- **Vehicles:** 64. 40 rigid 18 t (target 30.5 L/100 km), 24 articulated 40 t (target 35.0). Depots: North (32,
  EcoDrive from 2026-05-04), South (32).
- **Drivers:** 84. Shift patterns; vehicle swaps at depot with card-out → card-in 2–15 min apart, same vehicle,
  different driver.
- **Duty day:** 1–2 shifts.
  - Urban delivery runs have 4–14 key-off stops of 45 s – 25 min (18% of stops are 2–6 min).
  - Highway legs.
  - Engine-on idle: warm-up 2–15 min, loading with engine on, breaks with engine on.
  - Traffic stops of 10–55 s.
- **Engine state timeline** → speed profile → odometer (continuous) and fuel flow:
  - idle 2.2–3.0 L/h;
  - moving: class base × speed and acceleration factor.
- **EcoDrive** (coached North drivers after 2026-05-04):
  - idle-on probability −35%;
  - aggressive acceleration factor −40%;
  - true effect ≈ −3.8% L/100 km and idle ratio 0.140 → 0.098.
- **Counters:** `odometer_km` with 0.005 km resolution; `fuel_used_total_l` with 0.5 L resolution.

**Firmware and emission:**

| | fw 5.1 | fw 5.2 profile A (18 devices) | fw 5.2 profile B (4 devices) |
|---|---|---|---|
| Engine on | periodic every 10 s | moving (speed ≥ 3 km/h) every 30 s; stationary engine-on every 300 s | moving 20 s; stationary 600 s |
| Events | ignition_on / ignition_off records | `ignition_on/off`, `motion_start/stop` (speed crossing 3 km/h sustained 5 s), `harsh` | same as profile A |
| Engine off | heartbeat every 30 min | heartbeat every 60 min | heartbeat every 60 min |
| Out of coverage | pings **dropped** | buffered; on reconnect uploaded **most-recent-first** in batches of 50 with shared `upload_batch_id` | buffered, as profile A |
| Latency (live) | 97%: 1–4 s; 3%: 20–180 s retry | same | same |
| Time sync | at first GNSS fix after ignition_on (30–120 s), then every 4 h engine-on; 10% fail in covered yards | every 20 min | every 20 min |

- **Rollout:** 22 of 64 vehicles on 5.2. `firmware_installs.scheduled_at` lies between 04-27 and 05-18; the switch
  actually happens at the next ignition_on (`confirmed_at`). Every ping carries `fw_version`.
- **Dead zones** (INC-TEL-311): on highway legs only, 4–25 min, never within 3 min of a key event or a stationary span
  (generator constraint).

**Device clock.** `device_ts = t + offset(t)`.
- Normal RTCs drift −2 to +2 s/h.
- `hw_rev = 'B'` units (7 devices: 5 on 5.1, 2 on 5.2) run fast at 55–110 s/h, including while engine-off.
- At a successful sync at server time `s`, the device records `sync_events(device_id, device_ts_before, server_ts,
  offset_s)` and resets offset to 0 (±0.5 s).
- Rate is constant within a sync span, with a random walk ≤ 3 s.
- For a hw_rev B unit on 5.1 parked for 10 h, the `ignition_on` record and the driver's card-in carry device_ts ~15 min
  fast until the post-fix sync.

**Card reader events** (`driver_card_events`) are produced by the same device, so they carry the same `device_ts`
clock, and are received with the same latency and buffering.

**Faulty pipeline (incident code):**
1. `ingest.py` sorts by `received_at`.
2. `segment.py` starts a new trip whenever the time gap (received_at diff) is > 180 s or `ignition == 0`, and drops
   trips < 0.2 km.
3. `distance.py` sums haversine over consecutive GPS points.
4. `idle.py` computes `count(speed < 3) × 10 s`.
5. `attribution.py` compares card `device_ts` with trip start `received_at`.

History:
- 2024 design: threshold 60 s for the 10 s firmware.
- 2026-04-22: raised to 180 s "for new firmware idle heartbeat" (CHANGELOG).

## 6. Latent statistical/business invariant

**Clock.** Every record's event time is its device timestamp corrected by the device's sync-bounded drift. For a
record between successful syncs `s0` (server_ts₀) and `s1` (offset₁ observed at `device_ts_before₁`), drift is
linear in device time from 0 at s0 to offset₁ at s1:

```
t ≈ d − offset₁ · (d − server_ts₀) / (device_ts_before₁ − server_ts₀)
```

Records after the last sync in the extract use the rate of the previous span. Ordering and all durations use
corrected time.

**Trip** (policy): a continuous engine-on period from `ignition_on` to `ignition_off`. Key-off periods shorter than
120 s are merged into one trip, and their duration is not engine time. Sampling gaps and coverage gaps never end a
trip. Where a key event is missing, state comes from heartbeats (`ignition=0`) and counters.

**Distance and fuel** are counter deltas between trip boundaries: odometer (authoritative per policy) and fuel counter.
GPS is not used.

**Idle** is engine-on stationary time in spans of at least 60 s. Span boundaries come from motion events (5.2) or
speed samples (5.1); a stationary span is counted in full once it exceeds 60 s. Merged key-off time is excluded.

**Driver.** The driver whose card-in (corrected time) is the latest one ≤ trip start on that vehicle, with no card-out
in between. Otherwise `UNASSIGNED` (excluded from KPIs).

**Driver-week.** ISO week of trip start in Europe/London. Sums, then `l_per_100km = 100 · fuel / distance`,
`idle_ratio = idle / engine`, and eligibility per `bonus_targets.csv` (distance-weighted class target).

**Real improvements stay:** no firmware-based normalisation of KPIs.

## 7. Grains and state variables

| Grain | State |
|---|---|
| ping / event record | device_ts, corrected t, received_at, trigger, fw_version, profile, ignition, speed, counters, upload_batch_id |
| device × sync span | server_ts₀, offset₁, rate |
| inter-record interval | engine state, motion state, Δodometer, Δfuel, Δt |
| stationary span | start/end, engine on, ≥ 60 s? |
| key-off span | duration (< 120 s merge?) |
| trip | start/end, distance, fuel, engine_s, idle_s, driver |
| driver card session | card_in/out corrected |
| driver × ISO week | KPIs, eligibility |
| vehicle × 8 weeks | fuel-card litres (validation), maintenance odometer readings (validation) |

## 8. Evidence graph

(★ = on natural path)

| Artifact | Shows |
|---|---|
| ★ memo, ★ dashboard, ★ Q2 provisional | 5.2 vehicles −14% L/100km, idle −50%; Q2 eligible driver-weeks 38% (5.2) vs 16% (5.1) |
| ★ `segment.py`, `config`, ★ CHANGELOG | gap rule and the April threshold change "for new firmware" |
| ★ release notes 5.2 | adaptive sampling, motion triggers, buffering most-recent-first, 20-min sync |
| ★ pings parquet | 5.2 stationary samples every 300 s; out-of-order received_at in batches; `trigger` column |
| ★ notebook `fw52_impact_analysis` | GPS path on 5.1 accumulates 0.6–1.2 km/h while stationary (real jitter). Conclusion: "5.1 overstated distance and idle", so 5.2 is "more accurate". Half-true attractor. |
| ★ EcoDrive results note | North coached drivers −4% fuel, −30% idle (real) |
| `device_message_spec_v5.md` | counters, resolutions, trigger semantics, heartbeat ignition flag |
| `device_time_and_sync.md` | device RTC may drift; sync events record offset at sync; "device_ts is the device's clock" |
| `data_dictionary.md` | received_at = server receipt time; `device_inventory.hw_rev`; `firmware_installs.scheduled_at/confirmed_at` |
| `bonus policy` | trip definition (engine-on, key-off < 2 min merged), distance "as recorded by the vehicle odometer", idle definition (> 1 min stationary with engine on), week in local time |
| `trip_pipeline_design_2024.md` | "gaps longer than 6 samples indicate the engine is off, since the device reports every 10 s while running". The assumption, stated as history. |
| `INC-TEL-311` | dead zones: 5.1 loses data, 5.2 stores and forwards |
| `fuel_card_transactions` | litres pumped per vehicle; over 8 weeks ≈ counter total (±tank) |
| `maintenance_odometer_readings` | workshop odometer readings confirm CAN odometer; GPS totals are 3–7% off |
| `sync_events` | large offsets (up to 17 min) for 7 devices |
| Q1 statement | 5.1 era, faulty pipeline at 60 s threshold; approximately right for non-drift trucks (a trap for "match Q1") |
| Finance note | overpayment estimate using fuel card vs KPI fuel for 5.2 trucks (KPI fuel 15% below card litres) |

## 9. Evidence authority hierarchy

1. **The bonus policy** governs definitions: engine-on trips, odometer distance, idle, week. It conflicts with the
   pipeline design doc (gap-based) and the notebook (GPS-based); policy governs because bonuses are paid under it.
2. **Device spec + release notes + sync doc + data dictionary** govern record semantics: trigger meaning, buffering,
   clocks. Where release notes say "most recent first" and the data show received_at inversions, both agree.
3. **Server-side timestamps** (`received_at`, `sync_events.server_ts`) are the time standard. `device_ts` is
   authoritative only after correction. `received_at` includes latency and buffering, so it is not event time.
4. **Physical reconciliations** (fuel card litres, workshop odometer) validate totals, not trips.
5. **The notebook, EcoDrive note and Q1 statement** are analyses. Their findings are partly true.

## 10. Plausible hypotheses

| H | For | Against |
|---|---|---|
| H1 real behaviour change (EcoDrive) ★ | programme exists; North coached drivers improved; within North, coached > uncoached | South 5.2 trucks "improved" 13% with no coaching; fuel-card litres for 5.2 trucks unchanged per km |
| H2 firmware measures better ("5.1 was wrong") ★ | notebook shows real 5.1 GPS jitter inflating distance | under odometer distance, 5.1 is fine; 5.2 KPI fuel < card litres |
| H3 data loss ★ | INC-TEL-311; 5.1 gaps; 5.2 batches | loss is highway-only; does not explain idle halving |
| H4 segmentation under new sampling (gap rule) | 300 s stationary samples split by 180 s rule; idle fuel between micro-trips vanishes | — |
| H5 clock/ordering | out-of-order received_at; sync offsets | small fleet share (7 devices), but affects driver attribution |

## 11. Why each wrong hypothesis is plausible

- **H1** is *true in part*. An agent can "explain" the headline by the programme, especially because the note's numbers
  are close for North.
- **H2** has a real, quantified mechanism in an executed notebook, and it points toward "no fix needed".
- **H3** has a documented incident and visible gaps; "fill gaps" is a natural engineering reflex.

## 12. Investigation path (≈ 45–80 actions)

1. (1–8) Memo, dashboard, Q2 provisional, CHANGELOG, `segment.py`. Discovery: threshold raised for new firmware.
2. (9–14) Release notes; ping inspection for one 5.2 truck. Discovery: 300 s stationary samples → micro-trips dropped
   (< 0.2 km); idle and idle fuel vanish.
3. (15–20) Notebook and EcoDrive note; check South 5.2 trucks. Discovery: an improvement without coaching.
4. (21–26) First repair attempt, usually the threshold (§13). Compare fuel-card litres per vehicle vs KPI fuel;
   compare workshop odometer vs GPS distance → policy says odometer.
5. (27–34) Bonus policy definitions. Rewrite segmentation around ignition events; key-off < 120 s merge; idle via
   stationary spans ≥ 60 s.
6. (35–42) Ordering: received_at inversions in 5.2 batches (`upload_batch_id`) → sort by device_ts. Then 5.1 trucks
   with `hw_rev B` show overlapping device_ts after syncs, negative intervals and trip starts before the previous
   trip's end. Read the sync doc and `sync_events`.
7. (43–52) Implement drift correction. The first attempt is a constant step (previous offset) or "offset at next sync
   applied to whole span"; the check is trip start vs card-in plausibility and continuity at syncs.
8. (53–60) Card events use the same clock → correct them too; re-attribute trips at shift changes.
9. (61–68) Missing key events in dead zones? (none near keys, verify); heartbeats; counters confirm engine-off spans.
10. (69–80) Validation (§17), driver-week KPIs, eligibility, report differences by depot and coaching.

## 13. Natural wrong implementation

**"Threshold = 2 × max sampling interval, keep received_at ordering"**:

```python
gap_threshold_s = 600          # 2 × 300 s stationary interval of 5.2
df = df.sort_values(["vehicle_id","received_at"])
new_trip = (df.received_at.diff().dt.total_seconds() > gap_threshold_s) | (df.ignition == 0)
```

It may also switch distance to odometer after reading the policy.

What it gets wrong, on the visible audit sample:

- **5.1 dead zones (4–25 min)** split trips mid-highway. Each split drops the dead-zone interval's fuel and distance
  if the pipeline sums per-trip deltas; with GPS distance, the chord across the gap undercounts. Trips matched to
  truth: 5.1 vehicles 93%.
- **Short key-offs.** With `ignition == 0` rows present (5.2 sends `ignition_off` events), key-off stops still split.
  If the agent removes `ignition == 0` splitting to stop micro-trips, every 2–10 min delivery stop merges and its
  key-off time is counted as idle (speed 0 samples). Idle ratio for urban drivers rises to ~0.21 and eligibility
  collapses.
- **Received_at ordering on 5.2 batches (LIFO)** creates backwards time. With `diff()`, negative gaps never split, but
  first/last-ping counter deltas are wrong: trip fuel is sometimes negative or truncated, and GPS path zig-zags
  inflate distance by up to 40% for batched trips.
- **Idle as `count × 10 s`** undercounts 5.2 stationary time by ~30×.
- **Drift not handled** (ordering by received_at makes 5.1 drift trucks *mostly* right in order, but trip times are
  received-time and card times are device_ts): 11% of those trucks' trips are attributed to the wrong driver at shift
  changes.

Design-target outcomes:

| Pipeline | Trips matched (±30 s) | 5.2 fleet L/100km change | Idle ratio 5.2 | Eligible driver-weeks (truth 17.4%) |
|---|---|---|---|---|
| faulty (180 s) | 61% | −14.1% | 0.071 | 31.8% |
| 600 s + received_at + GPS | 79% | −6.2% | 0.172 | 9.5% |
| 600 s + received_at + odometer | 79% | −4.9% | 0.168 | 10.8% |
| truth | 100% | −2.7% (North coached −4.1%, South −0.3%) | 0.121 | 17.4% |

The −5% to −6% rows are believable ("firmware ~2%, coaching ~4%").

## 14. Second-order failure modes

1. **Per-firmware threshold** (5.1: 60 s; 5.2: 330 s; profile B ignored or 630 s).
   - 5.1 dead zones still split.
   - 5.2 key-off stops of 120–330 s are merged when the agent does not split on ignition.
   - Using `firmware_installs.scheduled_at` instead of per-ping `fw_version` mislabels 1–3 days per vehicle.
   - Trips matched ~90%.
2. **Ignition-based segmentation + odometer + device_ts ordering, no drift correction.** Correct for 57 of 64 devices.
   The 7 hw_rev B devices:
   - ignition_on stamped up to 17 min early → trip starts and engine time wrong;
   - post-sync records sort before pre-sync records → phantom overlaps and idle spans;
   - card-ins misordered → wrong driver.
   - Trips matched 95.8%; eligibility wrong for 6 of 84 drivers in ≥ 1 week.
3. **Drift correction as a step:** subtract the *previous* sync's offset (≈0) or apply the *next* offset to the whole
   span. Errors up to the full offset early in the span; ~40% of hw_rev B trip boundaries > 30 s off.
4. **Ordering by received_at "because server time is trustworthy":** right for live 5.1 drift trucks within latency,
   but 3% retry latencies (20–180 s) move key events beyond tolerance, and 5.2 buffered batches are wrong. Matched
   ~94%.
5. **Correct pings, uncorrected card events** → wrong drivers at swaps (drift trucks).
6. **Idle = all stationary engine-on time** (no 60 s rule) → traffic stops counted; 5.1 idle +9%.
7. **Key-off merge with idle** (merged key-off counted as engine/idle time).
8. **GPS distance "improved"** (Kalman/map-matching, jitter filter): still not odometer; 2–5% distance error;
   eligibility flips near thresholds.
9. **Normalise away firmware effect** (scale 5.2 KPIs to 5.1 baseline): erases the real EcoDrive gain; coached North
   drivers underpaid.
10. **Match the Q1 statement** (tune threshold to reproduce Q1): Q1 is 60 s-era faulty output. It is approximately
    right only because 10 s sampling hides the gap issue, and it includes drift-truck misattributions.
11. **Fill 5.1 dead-zone gaps by interpolation** when counters already carry the deltas: harmless for totals, but
    agents that also insert synthetic stationary samples create idle.

## 15. Correct repair properties

- Per-device clock correction from `sync_events` by span interpolation, applied to pings, events and card records;
  ordering by corrected time.
- State-based segmentation: ignition events + heartbeats + counters; key-off merge < 120 s; gaps never split.
- Distance and fuel from counters at trip boundaries (or max − min within trip, which is order-robust).
- Stationary spans from motion events and speed samples; ≥ 60 s rule; engine-on only.
- Driver attribution on corrected times.
- Week in local time; eligibility unchanged in logic.
- Nothing keyed on firmware version for *definitions*. Firmware only matters implicitly through which records exist.

## 16. Repair surfaces

| Surface | Why |
|---|---|
| `ingest.py` (+ new `clock.py`) | clock correction; ordering |
| `segment.py` | state-based trips, key-off merge; remove gap and min-km rules |
| `distance.py` | odometer deltas |
| `idle.py` | stationary spans with 60 s rule, interval-based |
| `attribution.py` | corrected card times; card-out handling |
| `config/pipeline.yaml` | obsolete keys (gap threshold) removed or ignored |
| unchanged | `fuel.py` logic (given trips), `kpi.py`, `bonus.py` |

## 17. Validation requirements

- **Row/state-level:**
  - For one 5.2 truck-day and one hw_rev B truck-day, lay out corrected records and compare trips with ignition
    events.
  - Verify no negative intervals and no overlapping trips per vehicle.
- **Physical reconciliation:**
  - Per vehicle over 8 weeks, Σ trip fuel should be ≈ counter delta over engine-on time, and within ±3% of fuel-card
    litres (tank-level noise). The faulty pipeline is −15% for 5.2.
  - Σ trip distance should be ≈ workshop odometer difference.
- **Sync continuity:** corrected time should be continuous across sync events (no jumps > 2 s).
- **Driver-swap audit:** trips around card changes on drift trucks.
- **Effect decomposition:** after repair, the 5.2 vs 5.1 difference within South (no coaching) ≈ 0, and coached vs
  uncoached within North ≈ −4%.
- **Aggregates cannot replace these:** the wrong pipelines in §13–14 give believable fleet-level numbers, and the
  EcoDrive story absorbs residual improvement.

## 18. Hidden fixture strategy

| Fixture | Invariant stressed | Surface change | Overfit caught | Same distribution |
|---|---|---|---|---|
| **hidden_a** "sampling mix" (30 trucks, 4 weeks, autumn calendar) | gaps never define state | profile B on 40% of 5.2 devices (600 s stationary, 20 s moving); longer engine-on waits at depots (idle 20–40 min sampled 3–4 times); dead zones longer (up to 45 min) | per-firmware thresholds; hard-coded 300 s; `scheduled_at` regime switch | both profiles, dead zones in visible |
| **hidden_b** "clocks & swaps" (36 trucks, 4 weeks) | interpolated drift correction; card events on same clock | 30% hw_rev B, some *slow* clocks (−40 to −90 s/h); 25% sync failures; frequent mid-day swaps (card changes 2–6 min); 5.2 LIFO batches of 200 | step correction; received_at ordering; uncorrected card events; hard-coded device ids | slow clocks follow the same sync mechanism (sign of offset only); visible has two slightly slow normal RTCs |
| **hidden_c** "urban stops & real improvement" (40 trucks, 6 weeks) | key-off < 120 s merge; idle ≥ 60 s; real effect preserved | dense urban routes (key-offs 60–180 s common); EcoDrive at South instead of North with larger effect (−7%); different class targets in `bonus_targets.csv` | threshold-based merge of short stops; firmware normalisation; hard-coded depot/programme dates; hard-coded targets | same policy, programme table, targets file mechanism |

## 19. Mutation strategy

| Mutation | Class | Expected |
|---|---|---|
| `nop` | control | 0 |
| `oracle` | control | 1 |
| `independent_state_machine` (record-by-record FSM over corrected stream) | alt | 1 |
| `interval_table_sql` (DuckDB/SQLite: intervals via LAG over corrected time, run-length spans) | alt | 1 |
| `oracle_order_robust_counters` (max − min per trip) | alt | 1 |
| `threshold_600_received_at` | natural wrong | 0 |
| `threshold_600_odometer` | natural wrong | 0 |
| `per_firmware_threshold` | second-order | 0 |
| `per_firmware_threshold_scheduled_at` | second-order | 0 |
| `ignition_segmentation_device_ts_no_drift` | second-order | 0 |
| `drift_step_prev_offset` / `drift_next_offset_whole_span` | second-order | 0 |
| `order_by_received_at_oracle_else` | second-order | 0 |
| `uncorrected_card_events` | partial | 0 |
| `idle_no_60s_rule` / `keyoff_counted_as_idle` | partial | 0 |
| `gps_distance_kalman` | wrong | 0 |
| `normalise_fw_effect` | wrong (erases real effect) | 0 |
| `fit_threshold_to_q1_statement` | attractor | 0 |
| `oracle_hardcoded_drift_devices` | overfit | visible 1 / hidden_b 0 |
| `oracle_hardcoded_300s_stationary` (used to label idle spans) | overfit | visible 1 / hidden_a 0 |
| `oracle_hardcoded_targets` | overfit | visible 1 / hidden_c 0 |
| `patched_outputs`, `edited_extract` | cheat | 0 |

## 20. Alternative valid implementations

- FSM vs interval tables vs pandas run-length encoding: all accepted within tolerance.
- Clock interpolation in device time vs server time: they differ by `rate²` effects (< 0.3 s).
- Idle span boundaries from speed samples vs motion events vs odometer-delta intervals: equivalent within the 5.1
  10 s sampling and exact for 5.2 events.
- Trip fuel/distance from first/last records vs max − min: identical on corrected ordering.
- Records after the last sync of the extract: extrapolate the previous rate (oracle), or hold the last offset. The
  generator guarantees ≤ 20 min after last sync for hw_rev B devices, so both are within tolerance.
- Output format: extra columns ignored; timestamps ISO-8601 UTC with or without `Z`; row order ignored.

## 21. Verifier design

**Ground truth:** generator true trips and KPIs, with counter values at true boundaries (the "observable truth" of
distance/fuel, so quantisation is identical).

**A. Integrity.** Extract digest; targets file digest; command success.

**B. Visible.**
1. **Trip matching** per vehicle: greedy 1:1 by start time; match if |Δstart| ≤ 30 s and |Δend| ≤ 30 s. Require
   ≥ 99.5% of true trips matched and ≤ 0.5% unmatched agent trips.
   - Tolerance rationale: max sampling uncertainty at non-event boundaries is 10 s (5.1; key events are records anyway);
     drift residual ≤ 8 s by generator bound; retry latency is irrelevant after correction.
2. **Matched trips, ≥ 99% within all of:**
   - distance max(0.02 km, 0.5%);
   - fuel ≤ 0.5 L;
   - engine_s ≤ 40 s;
   - idle_s ≤ 60 s;
   - driver exact.
3. **Driver-week KPIs:**
   - distance ±1%;
   - fuel ±1.5%;
   - engine hours ±1%;
   - idle hours max(±3%, 0.1 h);
   - `l_per_100km` ±1%;
   - `idle_ratio` ±0.005.
4. **Eligibility** exact for driver-weeks whose truth metrics are outside a ±1.5% band of each threshold; in-band
   driver-weeks are unchecked (reported). Visible has ~4% in band.
5. **Real-effect preservation:** coached vs uncoached North difference in agent KPIs within ±1 pp of truth
   (redundant with 3, but a readable failure message).
6. Determinism rerun.

**C. Hidden ×3.** Checks 1–4.

**Runtime.** Visible 3.4 M records, pandas ~60–120 s; hidden smaller; total < 8 min.

**Why tolerance, not a reference:** multiple valid segmentation implementations differ at sample granularity. Grading
against generator truth with physically justified tolerances accepts all of them. The tolerances are far tighter than
the wrong pipelines' errors: key-off merges miss by minutes, drift by minutes, and dead-zone splits create extra trips.

## 22. Answer-key leakage audit (with cheap-solve audit)

| Artifact | Assessment |
|---|---|
| bonus policy | Defines trip, idle, distance source (business definitions, required for fairness). Does not mention gaps, clocks, buffering, firmware. Risk: "engine-on period" + "odometer" gives two of five pieces. Accepted. |
| release notes 5.2 | Describe adaptive sampling, buffering order, sync interval. Facts; say nothing about the pipeline. |
| sync doc | Explains that sync_events record the offset observed at sync and reset the clock. Must **not** say "interpolate"; states the RTC runs continuously. |
| pipeline design 2024 | Documents the old assumption (gap ⇒ engine off at 10 s). This is the natural-wrong rationale, not a fix. |
| notebook | Wrong conclusion with a real sub-finding. |
| Q1 statement | Matches a faulty pipeline at 60 s; not a key for Q2. |
| fuel card / workshop odometer | Vehicle-level totals over weeks; cannot be transcribed to trips, idle or driver-weeks (drivers share vehicles). |
| `sync_events` | Data, not code. No helper consumes it. |
| faulty code | No clock module, no motion-event handling, no key-off merge, no odometer use; `config` has no unused keys hinting at them. |

**Cheap-solve audit.**

| Path | Outcome |
|---|---|
| One grep (`ignition`) | Segment on ignition only: still received_at ordering, no merge, GPS distance, idle nominal, drift. Fails. |
| One doc (policy) | Definitions only. Fails. |
| One filter (drop micro-trips / min_km = 0) | Keeps micro-trips, sums idle fuel back, but trips fragmented and idle nominal. Fails trip matching. |
| Change a constant (threshold) | §13. Fails. |
| Existing helper | None for clocks or states. Fails. |
| Match an old report (Q1) | Fails (§14.10). |
| Restore previous behaviour (60 s) | Worse: 5.2 fragments further. Fails. |
| Use fuel card as fuel | Vehicle-level only; fails trips and driver-weeks. Fails. |
| Order by device_ts | Fails drift trucks (§14.2). **Residual risk:** only 7/64 devices. The 99.5% trip threshold makes this binding: those devices carry ~11% of trips, and boundary errors hit ~40% of them. |

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| Key-off exactly 120 s | Generator avoids 115–125 s. Policy: "shorter than two minutes". |
| Stationary span exactly 60 s | Generator avoids 55–65 s spans; 5.1 sampling granularity also noted in tolerance. |
| Idle across a merged key-off | Policy: idle requires engine running; key-off excluded. |
| Stationary span inside a dead zone | Generator forbids; spec documents 5.1 drops and counters span the gap. |
| Trip spanning midnight / week boundary | Week of trip start (policy). |
| Driver with no card-in | `UNASSIGNED`, excluded (README output spec; faulty code already does this). |
| Clock correction after the last sync | Either extrapolation or hold, both within tolerance (§20). |
| Distance source when odometer missing | Never missing in extract (spec says counters every record); no fallback required. |
| Should firmware change KPIs at all? | Memo: "real improvements must still be paid"; policy definitions are firmware-independent. |
| Heartbeat 30 vs 60 min | Only used to confirm engine-off; not needed for boundaries (key events always present). |
| Harsh-event records | Ordinary records; no special handling. |
| Motion start threshold vs `idle_speed_kmh: 3` | Same 3 km/h; spec states the 5 s persistence. |
| Negative drift in hidden_b | Same mechanism; visible has mild negative drift on normal RTCs, so the sign is not a new rule. |
| Counter resolution | Spec: 0.5 L fuel; tolerance ≥ resolution. |

## 24. Expected trajectory length

50–85 actions, 35–70 minutes:
- ping-level inspection is unavoidable to see sampling and ordering;
- three mechanisms (sampling vs state, ordering/clock, distance authority) plus an attractor to reject (GPS
  notebook) and a real effect to preserve (EcoDrive);
- a clock-correction implementation per device span is real engineering;
- a validation loop over physical reconciliations.

## 25. Why harder than Tasks 03/05/06

| Task 06 flaw | G20 |
|---|---|
| Cutoff inherited | No time or state helper is correct; the only temporal logic (gap rule, received_at sort) is the defect. |
| Summary implemented | `kpi.py`/`bonus.py` are correct but depend entirely on trips; no partial trip logic to reuse. |
| Natural design correct | Threshold change and device_ts ordering are the natural designs; both wrong. |
| Attractor optional | Notebook and EcoDrive note are on path (memo cites both positions); Q1 statement tempts calibration. |
| Traps on unchosen paths | Every trap is the next obvious move of an engineer who recognises "sampling changed". |
| One-entity check enough | Drift trucks, 5.2 buffered trucks, urban-stop drivers and coached drivers are different subsets; no single truck shows all. |

## 26. Comparison with Task 02

- **Different mechanism:** state segmentation and clock reconciliation rather than feature availability.
- **Similar difficulty source:** the natural repair keys state on the wrong axis (gap/receive time instead of
  engine state/corrected time), as Task 02 keyed state on entity instead of entity × cutoff.
- **Harder:** multiple signals must be fused (ignition events, counters, motion events, sync offsets), and there is a
  real effect that must survive the repair (a negative-control element).
- **Easier:** physical reconciliations (fuel cards, workshop odometer) give strong, accessible validation signals, and
  the visual strangeness of 5.2 pings is easy to notice. Recognition will be quick; headroom relies on the clock and
  key-off details.
- Tolerance-based grading is more forgiving than Task 02's exact equality.

## 27. Benchmark risks

- **Implementation cost: H.** A physically consistent simulator is needed: engine state, speed, odometer, fuel flow,
  GPS noise, two firmware emission models, buffering, latency, dead zones, clocks and syncs. The KPI/trip truth must be
  exactly consistent with observable records, and the generator constraints (no ambiguous 120 s / 60 s edges, no idle
  in dead zones) need assertion tests. ~4 engineer-days.
- **Data size:** 3.4 M records is at the upper end for the verifier and agent memory (pandas ~1 GB peak). Option:
  5.1 sampling at 15 s instead of 10 s (still realistic) to halve records.
- **Realism: H.** Adaptive sampling, store-and-forward, RTC drift and odometer-vs-GPS disputes are routine.
  "Most-recent-first" upload is vendor-specific but plausible; keep it in release notes.
- **Gradability: M–H.**
  - Matching thresholds (99.5%) need calibration on the oracle and the alternative implementations; target oracle
    ≥ 99.9%.
  - Eligibility banding removes knife-edge cases.
- **Underspecification: M.** The idle ≥ 60 s rule and key-off < 120 s rule live only in the policy. Fair, but pedantic
  if the policy wording is vague; it must be exact. The drift interpolation choice is accepted within tolerance.
- **Headroom: M.**
  - Drift affects 7 devices. If an agent validates only on typical trucks, it fails (intended), but a strong agent
    reading `sync_events` finds 17-minute offsets quickly.
  - Most headroom likely comes from key-off merging and idle semantics combined with drift attribution.
  - If pilots show easy passes, raise the hw_rev B share to 20%, or make syncs less frequent. This stays within the
    documented mechanism.
- **Overlap:** Task 06 (event vs receipt time) low-moderate; G11/G08 low. It is the only segmentation / physical-signal
  task in the pool: high distinctness.
- **Leakage: L.** The policy is the main source and gives definitions only.
