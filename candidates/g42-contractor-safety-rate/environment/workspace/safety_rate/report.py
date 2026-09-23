"""Write the outputs described in docs/outputs/rate_contract.md."""
from __future__ import annotations

import json
from pathlib import Path


def write(out: Path, readout: dict, by_site) -> None:
    out.mkdir(parents=True, exist_ok=True)
    by_site.to_csv(out / "site_rates.csv", index=False)
    (out / "readout.json").write_text(json.dumps(readout, indent=2, sort_keys=True) + "\n")
