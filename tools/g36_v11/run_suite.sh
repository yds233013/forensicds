#!/bin/bash
# Oracle, Nop and every mutation against the built G36 image. ERRORs counted separately from
# FAILUREs, because a crash must never be mistaken for a rejection (the G35 lesson).
set -u
score() {
  local label="$1" out="$2" reward nfail nerr checks
  reward=$(printf '%s' "$out" | grep -o 'REWARD=[01]' | cut -d= -f2 || true)
  nfail=$(printf '%s' "$out" | grep -cE '^FAILED' || true)
  nerr=$(printf '%s' "$out" | grep -cE '^ERROR' || true)
  checks=$(printf '%s' "$out" | grep -oE '^(FAILED|ERROR) test_capacity.py::[^ ]*' | sed 's/.*:://' | tr '\n' '|' || true)
  printf '%s,%s,%s,%s,%s\n' "$label" "${reward:-NA}" "${nfail:-0}" "${nerr:-0}" "${checks:-}"
}
echo "case,reward,n_failed,n_errors,failed_checks"
for M in oracle nop; do score "$M" "$(bash /tmp/g36v11_run.sh "$M" 2>&1)"; done
for f in tools/g36_v11/mutations/*.py; do score "$(basename "$f" .py)" "$(bash /tmp/g36v11_run.sh agent "$f" 2>&1)"; done
