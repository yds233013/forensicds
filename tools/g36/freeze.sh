#!/bin/bash
# Freeze manifest for G36. Run from the repository root AFTER `git add`.
set -euo pipefail
T=candidates/g36-tou-capacity-gate
echo "# G36 freeze manifest"
echo "# generated $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo
echo "## files"
git ls-files "$T" | while read -r f; do
  printf '%s  %s\n' "$(shasum -a 256 "$f" | cut -c1-64)" "$f"
done
echo
echo "## generator copies (must match)"
shasum -a 256 "$T/tests/world.py" "$T/environment/build/world.py" | cut -c1-16,66-
echo
echo "## verifier checksum"
shasum -a 256 "$T/tests/test_capacity.py" "$T/tests/test.sh" "$T/tests/scenarios.py" | shasum -a 256 | cut -c1-16
echo
echo "## frozen checksum"
git ls-files "$T" | xargs shasum -a 256 | shasum -a 256 | cut -c1-16
