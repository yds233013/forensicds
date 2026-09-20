#!/bin/bash
set -euo pipefail
cp -r /solution/dispatch_experiment/. /workspace/dispatch_experiment/
cd /workspace
python -m dispatch_experiment analyse --warehouse data/warehouse.sqlite --out out
