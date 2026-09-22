# Minimal simulations

- **Code:** `sim/g39_sims.py`, 12 concepts, 5 regimes each, 60 worlds per regime, deterministic seeds.
- **Top-3 hybrid search:** `sim/g39_counterexamples.py`, run on the same worlds.
- **Results:** `sim/g39_results.json`, `sim/g39_counterexamples.json`.
- **Cost:** about 20 s CPU. No datasets, scaffolds or model calls.

Each simulation generates only the visible evidence required by the target object. Truth is valid
route V1 applied to that evidence, so the object is deterministic. The pre-registered statistics are
in the `g39_sims.py` docstring.
