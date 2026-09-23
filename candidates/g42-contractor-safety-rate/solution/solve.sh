#!/bin/bash
# Oracle: replace the exposure and case construction with the contract definitions.
set -euo pipefail
cp -f /solution/safety_rate/exposure.py /workspace/safety_rate/exposure.py
cp -f /solution/safety_rate/cases.py /workspace/safety_rate/cases.py
cp -f /solution/safety_rate/cli.py /workspace/safety_rate/cli.py
cd /workspace
rm -rf out
python -m safety_rate rate --warehouse data/warehouse.sqlite --out out
