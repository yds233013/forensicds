"""Reproduces the workspace's operating history on the generated warehouse (build stage only).

- reports/programme/sco2_waves1-4_readout_2026-08.md : the Programme team's readout from the house package
- notebooks/fpa_quickcheck_2026-08.ipynb             : FP&A's quick net-sales check
- out/                                               : the house package's outputs, as left in the workspace
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path



def house_readout(ws: Path) -> dict:
    subprocess.run([sys.executable, "-m", "sco_readout", "gate", "--warehouse", "data/warehouse.sqlite", "--out", "out"],
                   cwd=ws, check=True)
    return json.loads((ws / "out/readout.json").read_text())


def programme_report(ws: Path, r: dict) -> None:
    lines = [
        "# SCO 2.0 waves 1–4 readout (Programme team, August 2026)",
        "",
        "Method: `sco_readout` 2.3.1 (store and week fixed effects, store-clustered standard errors), basket size as the",
        "programme KPI, all live stores.",
        "",
        "| Wave | Basket size effect | 95% CI |",
        "|---|---|---|",
    ]
    for w, e in r["effect_by_wave"].items():
        lines.append(f"| {w} | {100 * e['estimate']:+.1f}% | {100 * e['ci_low']:+.1f}% to {100 * e['ci_high']:+.1f}% |")
    g = r["gate_effect"]
    lines += [
        "",
        f"**All waves: basket size {100 * g['estimate']:+.1f}% (95% CI {100 * g['ci_low']:+.1f}% to "
        f"{100 * g['ci_high']:+.1f}%).**",
        "",
        "- Every wave shows a significant basket increase; earlier waves show more, consistent with shoppers learning the",
        "  big-basket lane.",
        "- SCO share is up in all live stores.",
        "- Recommendation: proceed with waves 5–6 on the planned dates.",
        "",
    ]
    out = ws / "reports/programme"
    out.mkdir(parents=True, exist_ok=True)
    (out / "sco2_waves1-4_readout_2026-08.md").write_text("\n".join(lines))


QUICK = r'''import sys
sys.path.insert(0, ".")
from sco_readout import panel, estimate

# the Programme readout uses basket size; the business case gate is on net sales, so rerun it on net sales
p = panel.build("data/warehouse.sqlite")
overall = estimate.twfe(p, outcome="log_net_sales")
by_wave = estimate.twfe_by_wave(p, outcome="log_net_sales")
print(f"net sales effect, all live stores: {100 * overall['estimate']:+.2f}% (se {100 * overall['se']:.2f})")
for w, e in by_wave.items():
    print(f"  wave {w}: {100 * e['estimate']:+.2f}%")'''


def quickcheck(ws: Path) -> float:
    sys.path.insert(0, str(ws))
    from sco_readout import estimate, panel
    p = panel.build(ws / "data/warehouse.sqlite")
    overall = estimate.twfe(p, outcome="log_net_sales")
    by_wave = estimate.twfe_by_wave(p, outcome="log_net_sales")
    lines = [f"net sales effect, all live stores: {100 * overall['estimate']:+.2f}% (se {100 * overall['se']:.2f})\n"]
    lines += [f"  wave {w}: {100 * e['estimate']:+.2f}%\n" for w, e in by_wave.items()]
    cells = [
        {"cell_type": "markdown", "metadata": {}, "source": [
            "# SCO 2.0 net sales quick check (FP&A, August 2026)\n",
            "\n",
            "Basket size is the Programme team's KPI; the business case gate is on net sales. Quick check: the "
            "Programme team's readout, rerun on net sales."]},
        {"cell_type": "code", "execution_count": 1, "metadata": {}, "source": QUICK.splitlines(keepends=True),
         "outputs": [{"name": "stdout", "output_type": "stream", "text": lines}]},
        {"cell_type": "markdown", "metadata": {}, "source": [
            f"Net sales up about {100 * overall['estimate']:.1f}% in live stores, above the 2.5% hurdle. To be tidied "
            "into the readout package for the Committee pack."]},
    ]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                                     "name": "python3"},
                                       "language_info": {"name": "python", "version": "3.12"}},
          "nbformat": 4, "nbformat_minor": 5}
    (ws / "notebooks").mkdir(parents=True, exist_ok=True)
    (ws / "notebooks/fpa_quickcheck_2026-08.ipynb").write_text(json.dumps(nb, indent=1) + "\n")
    return overall["estimate"]


def main(ws: Path) -> None:
    r = house_readout(ws)
    programme_report(ws, r)
    est = quickcheck(ws)
    print(json.dumps({"house_gate": r["gate_effect"]["estimate"], "house_decision": r["decision"],
                      "quickcheck": est}))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
