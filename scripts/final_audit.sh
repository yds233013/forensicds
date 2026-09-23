#!/usr/bin/env bash
# Final submission audit. Read-only with respect to tasks and models: never runs an agent or a paid job.
# Exit status 0 only if every check passes.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=python3; FAIL=0
ok()  { echo "  PASS  $1"; }
bad() { echo "  FAIL  $1"; FAIL=1; }

# A Harbor job writing into jobs/ while section 3 regenerates results.json makes that check fail for
# a reason that has nothing to do with the submission. Refuse to audit mid-run instead.
running=$($PY - <<'RUNNING'
import glob, json
n = 0
for p in glob.glob("jobs/*/result.json"):
    try:
        if not json.load(open(p)).get("finished_at"):
            n += 1
    except Exception:
        n += 1
print(n)
RUNNING
)
if [ "${running:-0}" != "0" ]; then
  echo "  SKIP  $running Harbor job(s) still running; re-run the audit when they finish"
  exit 2
fi

echo "== 1. final tasks: Oracle=1, Nop=0, 3 valid trials, single checksum, rewards match record"
if $PY scripts/check_final_tasks.py; then ok "check_final_tasks"; else bad "check_final_tasks"; fi

echo "== 2. frozen tracked content unchanged and clean"
while read -r path cs; do
  now=$(git ls-files "$path" | xargs shasum -a 256 | shasum -a 256 | cut -c1-16)
  dirty=$(git status --short "$path" | wc -l | tr -d ' ')
  [ "$now" = "$cs" ] && [ "$dirty" = 0 ] && ok "$path $now" || bad "$path now=$now expected=$cs dirty=$dirty"
done < scripts/frozen_checksums.txt

echo "== 3. results.json regenerates identically from raw jobs"
cp report/data/results.json /tmp/fds_results_before.json
$PY scripts/build_results.py > /dev/null
cmp -s /tmp/fds_results_before.json report/data/results.json && ok "results.json reproducible" || bad "results.json changed on regeneration"

echo "== 4. report arithmetic matches results.json; pass@3 < 30 %"
$PY - <<'PY' || FAIL=1
import json, re, sys
R = json.load(open("report/data/results.json")); rep = open("report/REPORT.md").read(); fs = R["final_summary"]; bad = 0
def chk(cond, msg):
    global bad
    print(("  PASS  " if cond else "  FAIL  ") + msg); bad |= (not cond)
chk(f"{fs['successful_trials']} / {fs['trials']}" in rep, f"trial aggregate {fs['successful_trials']}/{fs['trials']} in report")
chk(f"{fs['tasks_with_pass3']} / {fs['tasks']}" in rep, f"task aggregate {fs['tasks_with_pass3']}/{fs['tasks']} in report")
chk(fs["task_pass_at_3"] < 0.30, f"aggregate pass@3 {fs['task_pass_at_3']:.3f} < 0.30")
chk(5 <= fs["tasks"] <= 10, f"{fs['tasks']} tasks within 5-10")
for tid in R["final"]:
    t = R["pilot"][tid]
    row = next((l for l in rep.splitlines() if l.lower().startswith(f"| {tid} |") and "/ 3" in l), "")
    chk(f"{t['successes']} / 3" in row and all(x["trial"].split("__")[-1] in row for x in t["trials"]),
        f"{tid} row: {t['successes']}/3 with its three trial IDs")
    chk(t["n_valid"] == 3, f"{tid} has exactly 3 counted trials")
for tid, t in R["pilot"].items():
    m = re.search(rf"\|\s*{tid}\s*\|.*?\|\s*(\d) / 3", rep)
excl = [k for k in ("g36", "g37", "g38") if k in R["final"]]
chk(not excl, "no excluded task (G36/G37/G38) in final set")
sys.exit(1 if bad else 0)
PY

echo "== 4b. no trial shows the container-teardown signature (research/harness_process_sweep_defect.md)"
$PY - <<'TEARDOWN' || FAIL=1
import json, pathlib, sys
tasks = json.load(open("scripts/final_tasks.json"))["tasks"]
bad = 0
for t in tasks:
    for tr in t["valid_trials"]:
        hits = list(pathlib.Path("jobs").glob(f"*/*{tr}*/verifier/test-stdout.txt"))
        if not hits:
            print(f"  FAIL  {tr}: no verifier stdout found"); bad = 1; continue
        if all(h.stat().st_size == 0 for h in hits):
            print(f"  FAIL  {tr}: empty verifier stdout (container-teardown signature)"); bad = 1
if not bad:
    print("  PASS  every valid trial carries a full grading report")
sys.exit(bad)
TEARDOWN

echo "== 5. submission structure"
if [ -d submission ]; then
  n=$(ls submission/samples | wc -l | tr -d ' '); [ "$n" -ge 5 ] && [ "$n" -le 10 ] && ok "$n tasks in samples/" || bad "$n tasks in samples/"
  for t in submission/samples/*/; do
    for f in instruction.md task.toml environment/Dockerfile tests/test.sh solution/solve.sh; do
      [ -f "$t$f" ] || bad "missing $t$f"
    done
    name=$(basename "$t"); k=$(ls -d submission/logs/$name/trials/*/ 2>/dev/null | wc -l | tr -d ' ')
    [ "$k" -ge 3 ] && ok "$name: $k trial dirs" || bad "$name: $k trial dirs"
    for d in submission/logs/$name/trials/*/; do
      [ -f "$d/agent/trajectory.json" ] && [ -f "$d/verifier/reward.txt" ] && [ -f "$d/result.json" ] || bad "incomplete trial $d"
    done
  done
  for x in g36 g37 g38; do ls submission/samples | grep -qi "$x" && bad "excluded $x present in samples" || ok "$x absent"; done
  [ -f submission/report/REPORT.md ] && ok "report present" || bad "report missing"
  grep -rIl "/Users/" submission/report submission/samples 2>/dev/null | head -3 | while read -r f; do echo "  WARN  absolute local path in $f"; done
  unzip -tq submission.zip >/dev/null 2>&1 && ok "submission.zip integrity" || bad "submission.zip broken or missing"
else
  bad "submission/ not built (run scripts/build_submission.sh)"
fi

echo "== 6. secret scan"
if bash scripts/secret_scan.sh submission submission.zip; then ok "no secrets"; else bad "secret scan findings"; fi

echo; [ $FAIL = 0 ] && echo "FINAL AUDIT: PASS" || echo "FINAL AUDIT: FAIL"; exit $FAIL
