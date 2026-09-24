#!/bin/bash
# Reference solution for P22: replace the quality package with one that establishes the drawing's conformance
# reference for each measuring machine under QP-07, re-dispositions the post window against it, allocates the
# remaining change over the readout's five causes, and applies Schedule 3 section 3.2 to the rate it names.
set -euo pipefail
cd /workspace
cp -f /solution/quality/conformance.py quality/conformance.py
cp -f /solution/quality/attribution.py quality/attribution.py
cp -f /solution/quality/report.py quality/report.py
python -m quality report --db data/inspection.sqlite --out out
