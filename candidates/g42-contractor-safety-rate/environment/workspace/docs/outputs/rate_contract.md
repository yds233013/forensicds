# Output contract - trailing-twelve-month recordable rate

`python -m safety_rate rate --warehouse <db> --out <dir>` writes two files.

## `readout.json`

```json
{
  "window_start": "<YYYY-MM-DD>",
  "window_end": "<YYYY-MM-DD>",
  "hours_worked": <float, 2 dp>,
  "recordable_cases": <int>,
  "rate": <float, 4 dp>,
  "rate_by_site": {"<site_id>": <float, 4 dp>, ...},
  "access_decision": "suspend" | "clear"
}
```

- `window_start`, `window_end` - the reporting window from `contract_terms`; `window_end` is exclusive.
- `hours_worked` - total hours worked in the window, as defined in `docs/hours_worked_policy.md`.
- `recordable_cases` - cases meeting `docs/recordable_case_standard.md`, by occurrence.
- `rate` - `rate_basis_hours` x `recordable_cases` / `hours_worked`, the pooled rate for the company.
- `rate_by_site` - the same rate computed for each site with hours worked in the window. The company
  rate is **not** the average of these.
- `access_decision` - `suspend` when the company rate exceeds `rate_limit`, otherwise `clear`.

## `site_rates.csv`

```csv
site_id,hours_worked,recordable_cases,rate
SITE-00,61234.50,2,6.5321
```

One row per site with hours worked in the window, consistent with `rate_by_site`.
