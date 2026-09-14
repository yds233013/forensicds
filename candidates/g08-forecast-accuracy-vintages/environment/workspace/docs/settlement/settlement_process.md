# Settlement volumes: how they are published

The settlement agent publishes volumes for each supply region x settlement class x delivery day in a sequence of
**runs**. Every run is loaded into `settlement_runs` / `settlement_volumes`; status changes are recorded in
`run_status_history`.

## Run types

| Run | Typical publication | What it is |
|---|---|---|
| `EST` | next morning, ~05:00 UK | Operational estimate from network data, for monitoring. Not a settlement run; nothing is charged on it. |
| `IS` Initial Settlement | 7th working day after delivery | First settlement. Imbalance charges are calculated on IS and invoiced to Trading. For non-half-hourly customers most reads are still estimated from standard profiles at this point. |
| `R1` | ~24 working days | First reconciliation: more actual meter reads. |
| `R2` | ~80 working days | Second reconciliation. |
| `RF` | ~14 months | Final reconciliation. |
| `DF` | after RF/R2, rare | Dispute outcome. |

Differences between IS and later runs are settled through the supplier reconciliation account, which Finance manages.
They do not change the imbalance charge already invoiced to Trading.

Publication can slip, for example during settlement agent outages (`ops/settlement_incidents.md`).

## Withdrawals and re-runs

The agent occasionally withdraws a run, usually for a processing fault found after publication. Some faults are found
within hours; others only after days or weeks. The agent sends a withdrawal notice. The run's status becomes
`withdrawn`, void from its publication, and a re-run of the same type follows the notice, normally within a week
(`reason = 'withdrawal_rerun'`, `replaces_run_id` = the withdrawn run).

Billing calculates charges on the runs it holds. A charge calculated on an IS stands until the withdrawal notice is
received; it is then cancelled, and recalculated when the re-run is published.

## Data corrections

When a data-load error is found (for example a duplicated or missing meter batch), the agent publishes a correction run
of the affected run type for the affected delivery days (`reason = 'data_correction'`, `replaces_run_id` = the
corrected run). The corrected run's status becomes `superseded` from the correction's publication. When the corrected
run is an IS, the imbalance charge is re-invoiced on the correction run when the correction is published.
