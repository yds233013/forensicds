#!/bin/bash
# Oracle: replace the planner's stock picture and rebalancing step with the availability policy.
set -euo pipefail
cp -f /solution/service_parts/inventory.py /workspace/service_parts/inventory.py
cp -f /solution/service_parts/network.py /workspace/service_parts/network.py
cp -f /solution/service_parts/cli.py /workspace/service_parts/cli.py
cd /workspace
rm -rf out
python -m service_parts plan --warehouse data/warehouse.sqlite --out out
