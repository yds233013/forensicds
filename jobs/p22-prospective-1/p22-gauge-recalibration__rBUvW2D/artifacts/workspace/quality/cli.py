import argparse

from quality.report import write_report


def main(argv=None):
    ap = argparse.ArgumentParser(prog="quality", description="MAN-4471 first-pass yield reporting")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report", help="produce the six-week yield readout")
    r.add_argument("--db", default="data/inspection.sqlite")
    r.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    if a.cmd == "report":
        write_report(a.db, a.out)
    return 0
