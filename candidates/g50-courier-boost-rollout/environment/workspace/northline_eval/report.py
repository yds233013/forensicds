"""Write the readout contract artefacts."""
import json
import os

from northline_eval import effects, panel

BREAK_EVEN_PP = 1.4961


def run(con, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    mw = panel.market_week(con)
    mw.to_csv(os.path.join(out_dir, "market_week_panel.csv"), index=False,
              columns=["market_id", "week_start", "orders", "late_orders", "late_rate_pct",
                       "boost_share", "courier_hours"])
    ac = effects.arm_contrast(con)
    cap = effects.courier_hours_by_arm(con)
    effect = ac["effect_pp"]
    decision = "roll_out" if (effect <= -BREAK_EVEN_PP and ac["ci_high_pp"] < 0) else "do_not_roll_out"
    readout = {
        "orders_analysed": ac["n"],
        "order_arm_contrast_pp": round(effect, 4),
        "programme_effect_pp": round(effect, 4),
        "programme_effect_ci_low_pp": round(ac["ci_low_pp"], 4),
        "programme_effect_ci_high_pp": round(ac["ci_high_pp"], 4),
        "inference_unit_n": ac["n"],
        "courier_hours_response_pct": round(cap["pct_gap"], 4),
        "decision": decision,
    }
    with open(os.path.join(out_dir, "readout.json"), "w") as fh:
        json.dump(readout, fh, indent=1, sort_keys=True)
    return readout
