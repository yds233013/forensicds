#!/bin/bash
set -euo pipefail
cp -f /solution/fleet_reliability/*.py /workspace/fleet_reliability/
cd /workspace
python -m fleet_reliability analyse --warehouse data/warehouse.sqlite --out out
