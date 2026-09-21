# G34 semantic audit A — contract-only derivation

**Written before opening `tests/`, `solution/`, `environment/build/world.py`, the G34 research notes
or the Gemini trajectories.** Sources: `instruction.md`, `docs/outputs/analysis_contract.md`,
`docs/aftermarket_planning_memo.md`, `docs/engineering_note.md`, `docs/event_dictionary.md`,
`docs/maintenance_sop.md`, `reports/installed_base_reliability_2026Q2.md`, `README.md`, and the
incumbent `fleet_reliability/`. G34 was not modified.

## 1. Population
**Every unit in `asset_register`.** The contract says "proportions of the installed base in the
extract" and "`installed_base_units` — units in the extract". The dictionary adds that the register
is "not filtered to units still running".
*Prose tension:* the memo says "today's installed base", which could suggest currently running
units only. The contract pins the denominator to the extract, so the contract governs. **Minor
documentation risk** (see interpretation E2).

## 2. Time origin
Commissioning (`commissioned_on`); ages are service ages.

## 3. Horizon
**36 months of service age** (contract `horizon_months: 36`; memo and rule "within 36 months of
service age").

## 4. Competing events
`UNPL_FAIL`, `PM_OVHL`, `ASSET_RET`. At most one per unit, and **each ends the original assembly's
life** (dictionary). They are mutually exclusive first events.

## 5. Censoring
- **Administrative only:** a unit with no work order was "still in service with its original
  assembly" at `extract_cut_off` (dictionary).
- **Telemetry outages are NOT exits** ("records data availability, not unit status"; SOP §4: "A unit
  is only out of service when a work order says so").
- *Latent-risk note:* the SOP's remark that a quiet channel often precedes a hot housing is a lure
  towards treating outages as events or censoring. The documents rule both out.

## 6. Crude / current-policy quantity (Q1 — aftermarket)
**Memo:** "how many units in today's installed base will actually suffer an unplanned failure of their
original assembly within 36 months of service age … Units whose assembly is exchanged at scheduled
overhaul before that happens are supplied from [another line]; units retired … generate nothing."

This is the probability that the **first** event by 36 months is `UNPL_FAIL`, under the actual
overhaul and retirement practice. Overhaul and retirement *prevent* the failure; they do not censor
it. **Q1 = CIF_FAIL(36)**, the Aalen–Johansen cumulative incidence with only administrative
censoring.

**Contract:** "the four outcomes … as proportions of the installed base. They describe mutually
exclusive outcomes of the same units." So:
- `unplanned_failure_rate_36m` = CIF_FAIL(36)
- `overhaul_rate_36m` = CIF_OVHL(36)
- `retirement_rate_36m` = CIF_RET(36)
- `still_original_assembly_36m` = S(36), the all-cause Kaplan–Meier survival

These four sum to 1, which is an algebraic constraint. The published 55.2 / 78.4 / 24.1 % sum to
158 %, which the contract's "mutually exclusive" wording exposes.

"Proportions of the installed base" must still account for administrative censoring. A unit
commissioned 20 months before cut-off has an unknown 36-month outcome. A crude count ÷ N is
therefore not "the proportion … by 36 months" (see the counterexamples in audit F).

## 7. Net / latent quantity (Q2 — engineering)
**Engineering note:** "a property of the **assembly**, not of the maintenance programme: how long does
a critical assembly last in service before it fails? … overhaul … and retirement … the field record is
incomplete for this purpose in the ordinary way — we do not see the failure that would have happened
later … Provided the overhaul schedule and the retirement decision are driven by the SOP interval and
by site economics rather than by the condition of the individual assembly … the incomplete records
can be handled in the standard way and the underlying assembly life is recoverable."

This is the **net (latent) probability that an assembly fails by 36 months of service age if it were
never removed for overhaul or retirement**. Under the stated independence assumption, overhaul and
retirement are treated as **censoring**, alongside administrative censoring. **Q2 = 1 − KM_FAIL(36)**,
censoring `PM_OVHL`, `ASSET_RET` and administrative end. The key `assembly_failure_rate_36m`
confirms it is a probability by 36 months, not a hazard or a mean life.

**The weighting is pinned:** each original assembly counts once, with one per unit. **The population
is pinned:** the installed base. **The horizon is pinned:** 36 months.

It is pinned **by prose, not formula**. "Handled in the standard way" is the only method pointer.

## 8. Business decision
The procurement rule is on **Q1**: `recommendation = "expanded"` iff CIF_FAIL(36) **> 0.28**
(strict), else `"baseline"`. The engineering number "should not be used for theirs".

## 9. Every reward-bearing numeric quantity (as the contract defines it)
| field | contract definition |
|---|---|
| `horizon_months` | 36 |
| `installed_base_units` | count of register units |
| `event_counts` | units per `wo_type`; `no_work_order` = remainder (four counts summing to N) |
| `units_at_risk[12/24/36]` | count of units with no event before age a **and** still inside the extract window at age a. That is exit_age > a, where exit_age is the WO age or the age at cut-off. Boundary: "still in service … at a months" reads as strict > a |
| `aftermarket.*` | four CIFs / survival at 36 as in §6 |
| `engineering.assembly_failure_rate_36m` | 1 − KM_FAIL(36), censoring overhaul, retirement and administrative end |
| `recommendation` | Q1 > 0.28 |

## Open questions for the verifier comparison (audit B)
1. Does the verifier grade the counts and `units_at_risk` exactly, and with which boundary (≥ or >)?
2. Does it grade Q1 and Q2 against latent truth or against an estimator applied to the data?
3. How is the tolerance set at 36 months, where the overhaul at 24 months (plus a few months of
   slack) leaves few assemblies at risk? **Q2 is an extrapolation beyond the overhaul age.** Its
   identifiability at 36 months is the principal G36-type risk (lesson 11).
4. Where is Q1 relative to 28 % on each fixture, and what is the tolerance (lesson 13)?
