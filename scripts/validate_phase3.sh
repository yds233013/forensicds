#!/usr/bin/env bash
# Reproducible pre-target-model validation for the three prospective tasks.
#
#   bash scripts/validate_phase3.sh            # everything except the mutation suites
#   bash scripts/validate_phase3.sh --mutations # also the mutation and exploit suites (slow, Docker-heavy)
#
# Runs NO target model. `harbor check` is deliberately not invoked: it uses an LLM judge.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python3}
FAIL=0
ok()  { printf '  ok    %s\n' "$1"; }
bad() { printf '  FAIL  %s\n' "$1"; FAIL=1; }
sec() { printf '\n== %s\n' "$1"; }

TASKS=(p22-gauge-recalibration p20-noshow-monitoring p31-fill-rate-dispute)
KEYS=(p22 p20 p31)
PKGS=(quality mlops service)

sec "1. harbor version"
V=$(harbor --version 2>&1 | head -1)
[ "$V" = "0.21.0" ] && ok "harbor $V" || bad "harbor version is '$V', expected 0.21.0"

sec "2. generator and truth are reproducible, and the extracts differ"
for i in 0 1 2; do
  T=candidates/${TASKS[$i]}
  $PY - "$T" <<'PYEOF' || bad "${TASKS[$i]}: generator/truth check failed"
import json, sys, hashlib, pathlib
sys.path.insert(0, str(pathlib.Path(sys.argv[1]) / "tests"))
import scenarios, world
digests, decisions = {}, {}
for n in scenarios.ALL_NAMES:
    w = world.build(scenarios.by_name(n))
    t = world.truth(w)
    digests[n] = hashlib.sha256(json.dumps(t, sort_keys=True, default=str).encode()).hexdigest()[:16]
    w2 = world.build(scenarios.by_name(n))
    t2 = world.truth(w2)
    assert t == t2, f"{n}: truth is not reproducible"
    for k in ("supplier_decision", "decision", "incumbent_verdict"):
        if k in t:
            decisions[n] = t[k]
assert len(set(digests.values())) == len(digests), "two extracts have identical truth"
print("   extracts:", ", ".join(f"{k}={v}" for k, v in decisions.items()))
PYEOF
  [ $? -eq 0 ] && ok "${TASKS[$i]}: 4 extracts, truth reproducible, decisions recorded"
done

sec "3. the two copies of each generator are identical"
for i in 0 1 2; do
  T=candidates/${TASKS[$i]}
  if diff -q "$T/environment/build/world.py" "$T/tests/world.py" >/dev/null; then
    ok "${TASKS[$i]}: environment/build/world.py == tests/world.py"
  else
    bad "${TASKS[$i]}: the two world.py copies differ"
  fi
done

sec "4. no generator internals, hidden specs or truth in the agent workspace"
for i in 0 1 2; do
  T=candidates/${TASKS[$i]}
  if grep -rqE "HIDDEN_SPECS|def truth\(|def latent_check\(|VISIBLE_SPEC" "$T/environment/workspace" 2>/dev/null; then
    bad "${TASKS[$i]}: generator internals reachable from the workspace"
  else
    ok "${TASKS[$i]}: workspace clean"
  fi
  if [ -e "$T/environment/build/scenarios.py" ]; then
    bad "${TASKS[$i]}: hidden specs are in the image build context"
  else
    ok "${TASKS[$i]}: hidden specs are in tests/ only"
  fi
done

sec "5. the reference solution reproduces truth on all four extracts"
for i in 0 1 2; do
  $PY tools/bench/check_solution.py --task candidates/${TASKS[$i]} --package ${PKGS[$i]} \
    && ok "${TASKS[$i]}: solution matches truth within tolerance on 4/4" \
    || bad "${TASKS[$i]}: solution does not match truth"
done

sec "6. Oracle = 1 and Nop = 0 (no target model involved)"
for i in 0 1 2; do
  for agent in oracle nop; do
    want=1; [ "$agent" = nop ] && want=0
    JOB="validate-${KEYS[$i]}-$agent-$$"
    if harbor run -p "candidates/${TASKS[$i]}" -a "$agent" -k 1 -n 1 -o jobs --job-name "$JOB" -y \
         > "logs/$JOB.log" 2>&1; then
      R=$(find "jobs/$JOB" -name reward.json -exec $PY -c 'import json,sys;print(int(json.load(open(sys.argv[1]))["reward"]))' {} \; 2>/dev/null | head -1)
      [ "$R" = "$want" ] && ok "${TASKS[$i]} $agent reward=$R" || bad "${TASKS[$i]} $agent reward=$R, wanted $want"
    else
      bad "${TASKS[$i]} $agent run failed (see logs/$JOB.log)"
    fi
  done
done

sec "7. secret scan"
bash scripts/secret_scan.sh /nonexistent.zip >/dev/null 2>&1 && ok "no credentials in the tree" \
  || bad "secret scan reported findings"

sec "8. the five-task fallback is untouched"
if git diff --quiet fallback-5task-submission -- report/ candidates/02-renewal-risk-regression \
     candidates/g05-sco-rollout-gate candidates/g10-censored-demand candidates/g24-recommender-ope \
     candidates/g34-fleet-reliability-gate; then
  ok "report/ and the five frozen tasks are identical to the fallback branch"
else
  bad "the fallback's tracked content has changed"
fi
if [ -f submission_5task_fallback.zip ]; then
  H=$(shasum -a 256 submission_5task_fallback.zip | cut -c1-16)
  [ "$H" = "c8561aad8300df6c" ] && ok "submission zip sha256 prefix $H" || bad "submission zip hash is $H"
fi

if [ "${1:-}" = "--mutations" ]; then
  sec "9. mutation and exploit suites (Docker, slow, one at a time)"
  for i in 0 1 2; do
    K=${KEYS[$i]}
    $PY tools/bench/mutation_harness.py --task "candidates/${TASKS[$i]}" --package "${PKGS[$i]}" \
       --mutations "tools/$K/mutations" --out "tools/$K/mutation_results.txt" >/dev/null 2>&1 \
       && ok "$K mutations: all as expected" || bad "$K mutations: see tools/$K/mutation_results.txt"
    $PY tools/bench/mutation_harness.py --task "candidates/${TASKS[$i]}" --package "${PKGS[$i]}" \
       --mutations "tools/$K/exploits" --out "tools/$K/exploit_results.txt" >/dev/null 2>&1 \
       && ok "$K exploits: all rejected" || bad "$K exploits: see tools/$K/exploit_results.txt"
  done
else
  printf '\n(skipping the mutation and exploit suites; pass --mutations to run them)\n'
fi

printf '\n'
[ "$FAIL" -eq 0 ] && { echo "phase 3 validation: PASS"; exit 0; } || { echo "phase 3 validation: FAIL"; exit 1; }
