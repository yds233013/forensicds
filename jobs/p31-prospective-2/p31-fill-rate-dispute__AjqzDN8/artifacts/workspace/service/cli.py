import argparse

from service.report import write_report


def main(argv=None):
    ap = argparse.ArgumentParser(prog="service", description="category service-level reporting")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fill", help="produce the category fill-rate readout")
    f.add_argument("--db", default="data/service.sqlite")
    f.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    if a.cmd == "fill":
        write_report(a.db, a.out)
    return 0
