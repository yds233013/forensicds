import argparse
import json

from northline_eval import effects, report, warehouse


def main(argv=None):
    ap = argparse.ArgumentParser(prog="northline_eval")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("readout"); r.add_argument("--db", required=True); r.add_argument("--out", required=True)
    c = sub.add_parser("checks"); c.add_argument("--db", required=True)
    a = ap.parse_args(argv)
    con = warehouse.connect(a.db)
    if a.cmd == "readout":
        print(json.dumps(report.run(con, a.out), indent=1, sort_keys=True))
        return 0
    print(json.dumps({"sample_ratio": effects.sample_ratio_check(con),
                      "pre_period_balance": effects.pre_period_balance(con),
                      "courier_hours_by_arm": effects.courier_hours_by_arm(con),
                      "control_vs_holdout": effects.control_vs_holdout(con),
                      "by_market": effects.by_market(con).to_dict("records")},
                     indent=1, sort_keys=True, default=float))
    return 0
