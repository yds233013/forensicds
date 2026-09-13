#!/usr/bin/env bash
# The verifier regenerates pristine data with tests/world.py; it must be identical to the build generator.
set -euo pipefail
T="$(cd "$(dirname "$0")/../../candidates/01-revenue-reconciliation" && pwd)"
cmp "$T/environment/build/world.py" "$T/tests/world.py" && echo "world.py in sync"
