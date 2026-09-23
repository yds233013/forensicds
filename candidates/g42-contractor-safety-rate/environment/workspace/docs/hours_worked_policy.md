# Hours-worked policy (HSE / Payroll, Meridian Industrial Services)

The denominator of the contract rate is **hours actually worked**. It is not payroll hours and it is
not scheduled hours.

## 1. What counts

`shift_entries.hour_type` distinguishes them:

| Value | Counts as hours worked? |
|---|---|
| `WORKED` | **yes**, including overtime (the `hours` column is the time actually worked) |
| `PTO` | no - paid, not worked |
| `HOLIDAY` | no |
| `TRAINING` | no - paid off-tools time |
| `TRAVEL` | no - paid travel between sites |

`scheduled_hours` is the roster figure and is kept only for variance reporting. Hours worked come from
the `hours` column of `WORKED` entries.

## 2. Whose hours count

Both employees and agency workers, for the same reason their cases count: they work under our
supervision on our sites. A rate that keeps agency **cases** in the numerator while dropping agency
**hours** from the denominator overstates the rate, and has been the subject of a client dispute before.

## 3. Which site the hours belong to

`shift_entries.site_id` is the site where the shift was worked. A worker assigned to more than one site
in the window contributes hours to each site they worked, regardless of `workers.home_site_id`.

## 4. Headcount is not exposure

Headcount multiplied by a nominal 2,000 hours is not an acceptable denominator under the contract:
crews are seasonal, agency workers rotate, and overtime is heavy on turnaround work.
