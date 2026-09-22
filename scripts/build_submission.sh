#!/usr/bin/env bash
# Build submission/{samples,logs,report} and submission.zip from the repository (no model runs).
#   samples/<task>/        tracked files of each final task (git archive: no caches, no untracked files)
#   logs/<task>/trials/    Harbor output of each counted trial; artifacts/ keeps files <= 1 MB (agent code and
#                          outputs) and drops large regenerable data (warehouse extracts, big CSVs)
#   logs/<task>/invalid/   infrastructure-invalid runs, kept for transparency (not counted)
#   logs/<task>/validation/ final Oracle / Nop runs on the frozen checksum + harbor check reports
#   report/                REPORT.md, figures, results.json, TRIALS.md, VALIDATION.md
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=submission; rm -rf "$OUT" submission.zip; mkdir -p "$OUT"/{samples,logs,report}
python3 - <<'PY' > /tmp/fds_plan.txt
import json, glob, os
cfg = json.load(open("scripts/final_tasks.json"))
for t in cfg["tasks"]:
    name = os.path.basename(t["path"])
    print("TASK", t["path"], name)
    for tr in t["valid_trials"]:
        for d in glob.glob(f"jobs/*/{tr}"):
            print("TRIAL", name, d)
    for tr in cfg.get("invalid_trials", {}):
        for d in glob.glob(f"jobs/*/{tr}"):
            if tr.startswith(name + "__"):
                print("INVALID", name, d)
    for d in glob.glob(f"jobs/final-*-{name}/*/"):
        print("VALID", name, d.rstrip("/"))
    for d in sorted(glob.glob("jobs/*/check_report.json") + glob.glob("jobs/*/*/check_report.json")):
        r = json.load(open(d))
        if any(x.get("task_name") == name for x in r.get("results", [])):
            print("CHECK", name, d)
PY
while read -r kind a b; do
  case "$kind" in
    TASK)    mkdir -p "$OUT/samples/$b"; git archive HEAD "$a" | tar -x -C "$OUT/samples" --strip-components=1 ;;
    TRIAL)   dst="$OUT/logs/$a/trials/$(basename "$b")"; mkdir -p "$dst"
             rsync -a --max-size=1m "$b/" "$dst/"
             jd=$(dirname "$b"); for f in config.json result.json job.log; do [ -f "$jd/$f" ] && cp "$jd/$f" "$OUT/logs/$a/trials/job_$(basename "$jd")_$f"; done ;;
    INVALID) dst="$OUT/logs/$a/invalid/$(basename "$b")"; mkdir -p "$dst"; rsync -a --max-size=1m "$b/" "$dst/" ;;
    VALID)   dst="$OUT/logs/$a/validation/$(basename "$(dirname "$b")")"; mkdir -p "$dst"; rsync -a --max-size=1m "$b/" "$dst/" ;;
    CHECK)   d="$OUT/logs/$a/validation/harbor_check"; mkdir -p "$d"; cp "$b" "$d/$(echo "$b" | tr '/' '_')" ;;
  esac
done < /tmp/fds_plan.txt
cp report/REPORT.md "$OUT/report/"; cp -r report/figures "$OUT/report/"; mkdir -p "$OUT/report/data"
cp report/data/results.json "$OUT/report/data/"
cp report/LOGS_README.md "$OUT/logs/README.md"
for f in report/TRIALS.md report/VALIDATION.md; do [ -f "$f" ] && cp "$f" "$OUT/report/"; done
# the report's sample paths refer to samples/<task-dir>; rename samples to match the task dirs (already named)
find "$OUT" -name "__pycache__" -type d -prune -exec rm -rf {} + ; find "$OUT" -name ".DS_Store" -delete
(cd "$OUT" && zip -qr ../submission.zip samples logs report)
du -sh "$OUT" submission.zip
