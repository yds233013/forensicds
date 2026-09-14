"""Apply the oracle's small entry-point change: pass issued statements to statement assembly."""
import sys
from pathlib import Path

p = Path(sys.argv[1]) / "jobs/close_month.py"
s = p.read_text()
old = "    lines = assemble_statement(usage, cards, args.month, close_hours)\n"
new = ("    from statements.ledger import billed_to_date\n"
       "    billed = billed_to_date(ROOT / \"ledger/issued\", args.month)\n"
       "    lines = assemble_statement(usage, cards, args.month, close_hours, billed)\n")
assert old in s, "entry point changed"
p.write_text(s.replace(old, new))
