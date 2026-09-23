#!/usr/bin/env bash
# Run the G41 verifier against each mutant in its own image layer, exactly as Harbor would:
# /tests copied in, test.sh executed as root, reward read from /logs/verifier/reward.txt.
set -uo pipefail
cd "$(dirname "$0")/../.."
TASK=candidates/g41-service-parts-rebalancing
IMG=forensicds-g41-check
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

docker build -q -t "$IMG" "$TASK/environment" > /dev/null || exit 1
pass=0; fail=0
: > tools/g41/mutation_results.txt
while read -r MID WANT; do
  rm -rf "$WORK/ctx"; mkdir -p "$WORK/ctx"
  cp -r "$TASK/solution/service_parts" "$WORK/ctx/service_parts"
  cp -r "$TASK/tests" "$WORK/ctx/tests"
  find "$WORK/ctx" -name "__pycache__" -type d -prune -exec rm -rf {} +
  cp tools/g41/mutations/"$MID"/*.py "$WORK/ctx/service_parts/"
  cat > "$WORK/ctx/Dockerfile" <<EOF
FROM $IMG
COPY service_parts/ /workspace/service_parts/
COPY tests/ /tests/
EOF
  docker build -q -t g41-mut:"$(echo "$MID" | tr 'A-Z_' 'a-z-')" "$WORK/ctx" > /dev/null || { echo "$MID BUILD_FAILED"; fail=$((fail+1)); continue; }
  got=$(docker run --rm g41-mut:"$(echo "$MID" | tr 'A-Z_' 'a-z-')" \
        bash -c 'bash /tests/test.sh > /tmp/out.txt 2>&1; cat /logs/verifier/reward.txt')
  if [ "$got" = "$WANT" ]; then st=OK; pass=$((pass+1)); else st=UNEXPECTED; fail=$((fail+1)); fi
  printf '%-38s want=%s got=%s %s\n' "$MID" "$WANT" "$got" "$st" | tee -a tools/g41/mutation_results.txt
done < tools/g41/mutations/expected.txt
echo "--- mutation suite: $pass as expected, $fail unexpected ---" | tee -a tools/g41/mutation_results.txt
[ "$fail" -eq 0 ]
