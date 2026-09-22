# Top 12 — target objects and qualitative scoring (before simulation)

Scores are H/M/L on: industry realism, DS ownership, expected structural separation, execution
difficulty, semantic sharpness, multiple valid routes, cheap-solve resistance, distinctness, fixture
potential, verification quality.

| id | target object | realism | DS own. | exp. sep. | exec. | sem. | routes | CS-res. | distinct | fixtures | verif. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | min Σ p_k max(x_k, m_k) s.t. Σ y_k x_k ≥ D, x ≤ cap | H | M | H | M | H | H | M | H | M | H |
| A2 | Σ N_j − maxflow(ATP surplus → need, arcs with L_ij ≤ T_j) | H | M | H | M | H | H | M | H | M | H |
| A3 | max Σ c q s.t. line hours, shared paint, demand | M | **L** | H | M | H | H | M | M | M | H |
| A4 | Σ_regions argmin_Q cost(Q) on hourly residual demand, integer cores | H | **H** | M | M | H | H | M | H | M | H |
| B1 | Σ good·ict / Σ PPT | H | H | H | M | H | M | M | M | M | H |
| B2 | Σ_s F_s · direct_hours_s / units_s | H | H | H | L | H | M | M | M | M | H |
| B3 | Σ_h max(0, usable_h − peak_h − reserved_h) | H | M | H | L | H | M | M | H | M | H |
| B4 | Σ E / Σ (eff_MW × COD hours) | H | H | M | L | H | M | M | M | M | H |
| C1 | Σ_f S_f Π_s FPY_fs / Σ S_f | H | H | H | M | H | M | M | M | M | H |
| C2 | 1 − Σ\|F − A\| / Σ A, SKU-store-week, active SKUs | H | H | H | **L** | H | M | M | M | M | H |
| C3 | Δ pooled conversion over the comparable set | H | H | M | L | H | M | M | M | M | H |
| C4 | Σ_s w_s recall_s, w ∝ t_s r_s | H | H | M | M | H | M | M | M | M | H |

The target formulas are in `family_*.md` and implemented in `sim/g39_sims.py`.
