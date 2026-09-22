# Recognition-vs-execution (H0–H4), R1 — from existing results

Hint conditions are mapped to the route sets an analyst holding that hint would use. The figures are
the **bias** in SE_REF units (visible / hidden_a / hidden_b / hidden_c / hidden_d) from the 200-draw run.

| condition | natural routes | bias | remaining work if the hint is taken |
|---|---|---|---|
| H0 no hint | dashboard pre/post (W01/W02) | +2.0 / +2.7 / +0.5 / −1.8 / +0.7 | — |
| H1 "selected because unusually bad" | exclude the trigger window (W04), DiD vs never-enrolled (W05/W07) | −1.6 … −2.7; −0.4 … −3.1 | persistent vs transient separation |
| H2 "RTM may explain improvement" | historical mean (W03), match on long-run mean (W10), shrink to fleet (W28) | −0.6 … −2.4; −1.3 … −3.6; −0.2 … −2.1 | persistence, time zero, seasonality |
| H3 "persistent risk + transient shock" | V2 with iid shocks (W21), V2 with fixed ρ (W26) | −0.3 … −2.0; −1.3 … +0.5 | estimate ρ, filter |
| H4 all three | V1 / V2 | ≈ 0 | — |

**Result.** Substantial statistical work *does* remain after H4 (estimate α and ρ, filter, align
time zero, seasonal offset, a valid counterfactual). But **the gate cannot credit it.** Every
intermediate hint level's routes are within ~1–3 SE_REF of the correct answer, which is inside the
valid band. The design fails because nothing is *gradable*, not because execution is trivial.
