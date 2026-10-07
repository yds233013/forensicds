#!/bin/bash
# Reference solution for P20: evaluate the model on the population MRM-04 section 4.1 requires, on the scores it
# produced in service, audit the feature feed against the source record and the event log, decompose the gap to
# the validation figure along a single chain, and apply section 4.4 in the order the standard states.
set -euo pipefail
cd /workspace
cp -f /solution/mlops/population.py mlops/population.py
cp -f /solution/mlops/programme.py mlops/programme.py
cp -f /solution/mlops/monitor.py mlops/monitor.py
python -m mlops monitor --db data/appointments.sqlite --out out
