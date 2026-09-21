#!/bin/bash
set -euo pipefail
cp -r /solution/capacity_forecast/. /workspace/capacity_forecast/
cd /workspace
python -m capacity_forecast analyse --warehouse data/warehouse.sqlite --out out
