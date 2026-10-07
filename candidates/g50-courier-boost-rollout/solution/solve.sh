#!/bin/bash
# Reference solution for G50: estimate the programme effect at the unit Boost was assigned at in
# phase 1, where Boost was on for every eligible order, rather than from the phase-2 arm contrast.
set -euo pipefail
cd /workspace
cp -f /solution/northline_eval/effects.py northline_eval/effects.py
cp -f /solution/northline_eval/report.py northline_eval/report.py
python -m northline_eval readout --db data/northline.sqlite --out out
