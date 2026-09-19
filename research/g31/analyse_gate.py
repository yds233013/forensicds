"""Summarise the G31 Phase-0 gate (research only)."""
import json, glob, os
import numpy as np

QUANT_D = ["delta.ecom_cnp", "delta.marketplace", "delta.travel"]
REGS = ["visible", "high_prev", "slow_cb_big_holdout", "tight_capacity"]


def load():
    out = {}
    for r in REGS:
        p = f"results/gate_{r}.json"
        if os.path.exists(p):
            out[r] = json.load(open(p))
    return out


def errs(rows, nm, q):
    return np.array([x["methods"][nm]["q"][q] - x["truth"][q] for x in rows], float)


def main():
    data = load()
    if not data:
        print("no gate results yet"); return
    quants = list(data[REGS[0]]["calibration"][0]["truth"].keys())
    acc = [n for n, m in data[REGS[0]]["calibration"][0]["methods"].items() if m["kind"] == "accepted"]
    wrong = [n for n, m in data[REGS[0]]["calibration"][0]["methods"].items() if m["kind"] == "wrong"]

    # ---- tolerance: 3.5 x calibration RMSE of the least efficient accepted estimator, per regime+quantity
    tol = {}
    for r, d in data.items():
        for q in quants:
            rms = [np.sqrt((errs(d["calibration"], nm, q) ** 2).mean()) for nm in acc]
            tol[(r, q)] = 3.5 * max(rms)

    print("=" * 108)
    print("TRUTH (validation mean) and TOLERANCE by regime")
    print(f"{'regime':22} {'quantity':22} {'truth':>9} {'tau':>9}")
    for r, d in data.items():
        for q in QUANT_D:
            t = np.mean([x["truth"][q] for x in d["validation"]])
            print(f"{r:22} {q:22} {t:9.4f} {tol[(r,q)]:9.4f}")

    print("=" * 108)
    print("ACCEPTED estimators: bias / RMSE / worst ratio, and validation pass rate (all graded quantities)")
    print(f"{'method':22} {'regime':22} {'bias(delta)':>12} {'RMSE(delta)':>12} {'worst ratio':>12} {'pass':>9} {'dec ok':>7}")
    for nm in acc:
        tot_p = tot_n = 0
        for r, d in data.items():
            e = np.concatenate([errs(d["validation"], nm, q) for q in QUANT_D])
            ratios, passes, decok = [], 0, 0
            for x in d["validation"]:
                ok = True
                for q in quants:
                    rr = abs(x["methods"][nm]["q"][q] - x["truth"][q]) / tol[(r, q)]
                    ratios.append(rr)
                    if not (rr <= 1):
                        ok = False
                if x["methods"][nm]["decision"] == x["truth_decision"]:
                    decok += 1
                else:
                    ok = False
                passes += ok
            tot_p += passes; tot_n += len(d["validation"])
            print(f"{nm:22} {r:22} {e.mean():+12.4f} {np.sqrt((e**2).mean()):12.4f} "
                  f"{max(ratios):12.2f} {passes:4d}/{len(d['validation']):<4d} {decok:3d}/{len(d['validation']):<3d}")
        print(f"{nm:22} {'ALL':22} {'':12} {'':12} {'':12} {tot_p:4d}/{tot_n:<4d}")

    print("=" * 108)
    print("WRONG analyses: validation pass counts per regime, joint pass probability, decision correctness")
    print(f"{'method':24} " + " ".join(f"{r[:12]:>13}" for r in data) + f" {'jointP':>10} {'minratio':>9} {'decOK%':>7}")
    for nm in wrong:
        cells, minr, dec_ok, dec_n = [], 1e9, 0, 0
        for r, d in data.items():
            p = 0
            for x in d["validation"]:
                ok = all(abs(x["methods"][nm]["q"][q] - x["truth"][q]) / tol[(r, q)] <= 1 for q in quants) \
                     and x["methods"][nm]["decision"] == x["truth_decision"]
                p += ok
                rr = max(abs(x["methods"][nm]["q"][q] - x["truth"][q]) / tol[(r, q)] for q in quants)
                minr = min(minr, rr)
                dec_ok += (x["methods"][nm]["decision"] == x["truth_decision"]); dec_n += 1
            cells.append((p, len(d["validation"])))
        jp = np.prod([(c[0] + 0.5) / (c[1] + 1) for c in cells])   # add-half, avoids log(0)
        print(f"{nm:24} " + " ".join(f"{c[0]:6d}/{c[1]:<6d}" for c in cells)
              + f" {jp:10.2e} {minr:9.2f} {100*dec_ok/dec_n:6.1f}%")


if __name__ == "__main__":
    main()
