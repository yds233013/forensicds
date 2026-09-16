"""Writing the gate outputs."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ORDER = ["v6", "v7", "v7_pd"]


def write_all(out: Path, decisions: pd.DataFrame, targets: pd.DataFrame, values: pd.DataFrame) -> None:
    out.mkdir(parents=True, exist_ok=True)
    decisions.to_csv(out / "decisions.csv", index=False)
    targets.to_csv(out / "target_slates.csv", index=False)
    values = values.set_index("policy").loc[ORDER].reset_index()
    values.to_csv(out / "policy_values.csv", index=False)
    qualifies = [r.policy for r in values.itertuples() if r.policy != "v6" and r.lift_ci_low > 0]
    if qualifies:
        launch = max(qualifies, key=lambda p: float(values.set_index("policy").loc[p, "value"]))
    else:
        launch = "v6"
    (out / "launch.json").write_text(json.dumps({"launch": launch}, indent=2) + "\n")
