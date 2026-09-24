#!/bin/bash
# Reference solution for P31: compute the category fill rate on the basis Schedule 2 actually defines, compute
# the supplier's basis from its own appendix, bridge the two, decompose to account level, reconcile the tickets,
# and settle each consequence only where the readings Schedule 4 leaves open agree.
set -euo pipefail
cd /workspace
cp -f /solution/service/definitions.py service/definitions.py
cp -f /solution/service/adjudicate.py service/adjudicate.py
cp -f /solution/service/report.py service/report.py
python -m service fill --db data/service.sqlite --out out
