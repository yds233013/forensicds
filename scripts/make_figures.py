#!/usr/bin/env python3
"""Render report figures from report/data/results.json (plus the per-trial failure labels below, taken from the
trajectory analyses in research/). Run with a Python that has matplotlib."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, "report", "data", "results.json")))
FIG = os.path.join(ROOT, "report", "figures"); os.makedirs(FIG, exist_ok=True)
INK, MUTED, ACCENT, GRID = "#1f2933", "#9aa5b1", "#2f6f9f", "#e4e7eb"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK,
                     "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False})

# 1. Pilot pool: successes out of 3, final set highlighted
p = R["pilot"]; order = sorted(p, key=lambda k: (p[k]["successes"], k))
fig, ax = plt.subplots(figsize=(7.2, 3.6))
cols = [ACCENT if k in R["final"] else MUTED for k in order]
ax.barh([f"{k}  {p[k]['name']}" for k in order], [p[k]["successes"] for k in order], color=cols, height=0.62)
for i, k in enumerate(order):
    fin_ = k in R["final"]
    if fin_:
        ax.plot([0.04], [i], marker="s", color=ACCENT, ms=7, clip_on=False)
    ax.text(p[k]["successes"] + (0.14 if fin_ and p[k]["successes"] == 0 else 0.05), i,
            f"{p[k]['successes']}/3" + ("   final suite" if fin_ else ""), va="center", color=ACCENT if fin_ else INK, fontsize=9)
for lab in ax.get_yticklabels():
    if lab.get_text().split()[0] in R["final"]:
        lab.set_fontweight("bold"); lab.set_color(ACCENT)
ax.set_xlim(0, 4.0); ax.set_xticks([0, 1, 2, 3]); ax.set_xlabel("successful trials out of 3 (gemini-3-flash-preview)")
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
fig.suptitle("All 12 measured pilot tasks (blue = final suite)", x=0.02, ha="left", color=INK, fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "pilot_successes.png"), dpi=180); plt.close(fig)

# 2. Difficulty curve: empirical per-attempt success vs task rank, pilot vs final
fig, ax = plt.subplots(figsize=(6.4, 3.2))
pil = sorted((p[k]["successes"] / 3 for k in p), reverse=True)
ax.step(range(1, len(pil) + 1), pil, where="mid", color=MUTED, label="pilot pool (12 tasks)")
fin = sorted((p[k]["successes"] / 3 for k in R["final"]), reverse=True)
ax.step(range(1, len(fin) + 1), fin, where="mid", color=ACCENT, lw=2.2, label="final suite (5 tasks)")
ax.set_ylim(-0.05, 1.05); ax.set_xlabel("task rank (easiest first)"); ax.set_ylabel("successes / 3")
ax.grid(color=GRID); ax.set_axisbelow(True); ax.legend(frameon=False, loc="upper right")
ax.set_title("Difficulty curve", loc="left", color=INK, fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "difficulty_curve.png"), dpi=180); plt.close(fig)

# 3. Failure modes of the 13 failed final-suite trials (primary label; from research/*analysis*.md)
FAIL = {"F9 right method family, wrong statistical object": 10, "F4 root cause found, repair incorrect": 2,
        "F7 substantially correct repair, insufficient validation": 1}
fig, ax = plt.subplots(figsize=(6.8, 2.2))
ks = list(FAIL); ax.barh(ks[::-1], [FAIL[k] for k in ks[::-1]], color=ACCENT, height=0.55)
for i, k in enumerate(ks[::-1]):
    ax.text(FAIL[k] + 0.1, i, str(FAIL[k]), va="center", color=INK)
ax.set_xlabel("failed trials (primary label)"); ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
ax.set_title("What went wrong in the 13 failed final-suite trials", loc="left", color=INK, fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "failure_modes.png"), dpi=180); plt.close(fig)
print("figures written to", FIG)
