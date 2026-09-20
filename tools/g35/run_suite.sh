#!/bin/bash
# Run oracle, nop and every mutation against the built G35 image. Local/deterministic; no model.
#   bash tools/g35/run_suite.sh > /tmp/g35_suite.csv
#
# ERRORs are counted and reported separately from FAILUREs on purpose: the first version of this
# runner grepped only for FAILED, which silently hid a template bug that made every mutation crash
# on import. Every case then "scored 0" for the wrong reason and the panel proved nothing.
set -u

score() {
  local label="$1" out="$2"
  local reward nfail nerr checks
  reward=$(printf '%s' "$out" | grep -o 'REWARD=[01]' | cut -d= -f2 || true)
  nfail=$(printf '%s' "$out" | grep -cE '^FAILED' || true)
  nerr=$(printf '%s' "$out" | grep -cE '^ERROR' || true)
  checks=$(printf '%s' "$out" | grep -oE '^(FAILED|ERROR) test_dispatch.py::[^ ]*' \
           | sed 's/.*:://' | tr '\n' '|' || true)
  printf '%s,%s,%s,%s,%s\n' "$label" "${reward:-NA}" "${nfail:-0}" "${nerr:-0}" "${checks:-}"
}

echo "case,reward,n_failed,n_errors,failed_checks"
for M in oracle nop; do
  score "$M" "$(bash /tmp/g35_run.sh "$M" 2>&1)"
done
for f in tools/g35/mutations/*.py; do
  score "$(basename "$f" .py)" "$(bash /tmp/g35_run.sh agent "$f" 2>&1)"
done
