# Cheap-solve / proxy panel (C1, D2)

| proxy | outcome |
|---|---|
| constant "notify" | right on 3/5 fixtures (a, c, d); wrong on visible and b |
| constant "no notification" | right on 2/5 |
| raw dashboard Ppk decision | 0 %, 65 %, 0 %, 100 %, 100 % correct (vis, a, b, c, d); **not reliable** |
| raw pre→post direction ("it dropped, so notify") | dashboard drops on vis, b, c, d, rises on a; the truth decision is notify on a, c, d. Wrong on vis, b and a |
| vendor block number | = W02, fails 5/5 numerically |
| bridge mean difference | = W03, fails 3/5 |
| observed-variance threshold | equivalent to raw; fails |
| row counts, file names, fixture identity | no information: designed volumes are identical across regimes (see `representation_leakage.md`) |

**The decision cannot be guessed from the raw direction. This gate passes.** It is not the failing gate.
