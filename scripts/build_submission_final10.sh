#!/usr/bin/env bash
# Assemble and validate the final submission. Does not touch the five-task fallback archive.
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)
STAGE=submission_final10
FINAL10="02-renewal-risk-regression g05-sco-rollout-gate g10-censored-demand g24-recommender-ope
g36-tou-capacity-gate p20-noshow-monitoring p22-gauge-recalibration p31-fill-rate-dispute
g08-forecast-accuracy-vintages g50-courier-boost-rollout"

rm -rf "$STAGE" && mkdir -p "$STAGE"/{samples,logs,report}

echo "== samples: exactly 10 task directories =="
n=0
for t in $FINAL10; do
  [ -d "candidates/$t" ] || { echo "MISSING candidates/$t"; exit 1; }
  rsync -a --exclude '__pycache__' --exclude '.ipynb_checkpoints' "candidates/$t" "$STAGE/samples/"
  n=$((n+1))
done
echo "   staged $n tasks"
# Version forks and the ablation travel alongside, clearly marked, without displacing the ten.
for extra in p20-noshow-monitoring-v1.1 02-renewal-risk-regression-v1.1 \
             02-renewal-risk-regression__explicit-invariant; do
  [ -d "candidates/$extra" ] && rsync -a --exclude '__pycache__' "candidates/$extra" "$STAGE/samples/"
done
cat > "$STAGE/samples/README_SAMPLES.md" <<'RM'
# samples/

**The final ten** (these are the submission):

1. 02-renewal-risk-regression
2. g05-sco-rollout-gate
3. g10-censored-demand
4. g24-recommender-ope
5. g36-tou-capacity-gate
6. p20-noshow-monitoring
7. p22-gauge-recalibration
8. p31-fill-rate-dispute
9. g50-courier-boost-rollout
10. g08-forecast-accuracy-vintages

**Shipped alongside, NOT part of the ten:**

| directory | what it is |
|---|---|
| `02-renewal-risk-regression__explicit-invariant` | ablation of #1 with the invariant stated outright (3 trials, 0 passes) |
| `p20-noshow-monitoring-v1.1` | remediation of #6's unspecified sign convention; separately exposed (3 trials, 0 passes) |
| `02-renewal-risk-regression-v1.1` | remediation of #1's image-layer leak; packaging-only, agent-visible workspace byte-identical to v1 |

Each of the ten carries `REAL_DISTRIBUTION_PROVENANCE.md`. See `../report/FINAL_REPORT.md` and
`../report/HANDOFF_ABUNDANT_FINAL_SUBMISSION.md`.
RM

echo "== logs: every valid Gemini trial for the final ten, plus oracle/nop =="
python3 - <<'PY'
import json, os, glob, shutil
FINAL10={"02-renewal-risk-regression","g05-sco-rollout-gate","g10-censored-demand",
 "g24-recommender-ope","g36-tou-capacity-gate","p20-noshow-monitoring",
 "p22-gauge-recalibration","p31-fill-rate-dispute","g08-forecast-accuracy-vintages",
 "g50-courier-boost-rollout","p20-noshow-monitoring-v1.1",
 "02-renewal-risk-regression__explicit-invariant"}
dst="submission_final10/logs"; kept=0
for cfg in glob.glob("jobs/*/config.json"):
    j=os.path.dirname(cfg); jn=os.path.basename(j)
    try: c=json.load(open(cfg))
    except Exception: continue
    tasks=c.get("tasks") or []
    if not tasks: continue
    tp=os.path.basename(tasks[0].get("path",""))
    if tp not in FINAL10: continue
    ag=(c.get("agents") or [{}])[0].get("name","")
    if ag not in ("gemini-cli","nop","oracle") and "oracle" not in jn: continue
    shutil.copytree(j, os.path.join(dst,jn), dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("*.sqlite","__pycache__"))
    kept+=1
print(f"   staged {kept} job directories")
PY

echo "== report =="
cp report/FINAL_REPORT.md report/CURATION_TABLE.md "$STAGE/report/" 2>/dev/null
mkdir -p "$STAGE/report/analysis" && cp report/analysis/*.json "$STAGE/report/analysis/" 2>/dev/null
cp scripts/extract_trajectories.py scripts/compute_metrics.py "$STAGE/report/" 2>/dev/null
cp OVERNIGHT_FINAL10_PROGRESS.md HANDOFF_ABUNDANT_FINAL_SUBMISSION.md "$STAGE/report/" 2>/dev/null

echo "== validate =="
ls "$STAGE/samples" | grep -v 'v1.1' | wc -l | xargs echo "   task dirs (excluding the version fork):"
for t in $FINAL10; do
  for f in instruction.md task.toml environment/Dockerfile tests/test.sh REAL_DISTRIBUTION_PROVENANCE.md; do
    [ -e "$STAGE/samples/$t/$f" ] || echo "   MISSING $t/$f"
  done
done

echo "== zip =="
rm -f submission_final10.zip
( cd "$STAGE" && zip -qr "$ROOT/submission_final10.zip" . -x '*.DS_Store' )
unzip -t submission_final10.zip > /dev/null && echo "   zip integrity OK"
echo "   size: $(du -h submission_final10.zip | cut -f1)"
echo "   entries: $(unzip -l submission_final10.zip | tail -1)"
echo "   SHA-256: $(shasum -a 256 submission_final10.zip | cut -d' ' -f1)"
echo "== fallback archive must be unchanged =="
echo "   submission_5task_fallback.zip $(shasum -a 256 submission_5task_fallback.zip | cut -d' ' -f1)"
