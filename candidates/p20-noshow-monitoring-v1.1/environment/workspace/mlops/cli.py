import argparse

from mlops.monitor import write_readout


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mlops", description="model monitoring readout")
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("monitor", help="produce the monitoring readout")
    m.add_argument("--db", default="data/appointments.sqlite")
    m.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    if a.cmd == "monitor":
        write_readout(a.db, a.out)
    return 0
