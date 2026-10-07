#!/usr/bin/env bash
# Cross-model evaluation: Claude on the frozen ForensicDS final ten.
#
#   ./scripts/run_claude_crossmodel.sh [model] [trials-per-task]
#
# Runs strictly sequentially (8-CPU host; concurrency caused every agent-setup timeout in the Gemini
# campaign). Writes to crossmodel_logs/claude/ only. NEVER touches jobs/ or any Gemini trajectory.
# THE BENCHMARK IS NOT MODIFIED BY THIS SCRIPT.
set -uo pipefail
cd "$(dirname "$0")/.."
MODEL="${1:-claude-opus-5-5}"
N="${2:-3}"
OUT=crossmodel_logs/claude
mkdir -p "$OUT" logs

# --- credential gate -------------------------------------------------------------------------
source ~/.zshrc >/dev/null 2>&1
if [ -z "${ANTHROPIC_API_KEY:-}${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
  echo "STOP: no Anthropic credential available."; exit 2
fi
# Guards against reusing a credential that was once exposed, identified by sha256 fingerprint
# rather than by a literal key prefix so that no key material appears in this file.
REVOKED_FINGERPRINT="10b97de263f9"
if [ "$(printf %s "${ANTHROPIC_API_KEY:-}" | shasum -a 256 | cut -c1-12)" = "$REVOKED_FINGERPRINT" ]; then
    echo "STOP: the available ANTHROPIC_API_KEY is a credential that was previously exposed"
    echo "      and revoked. Rotate at https://console.anthropic.com/settings/keys, update the"
    echo "      profile, then re-run."
    exit 3
fi
export ANTHROPIC_API_KEY
[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && export CLAUDE_CODE_OAUTH_TOKEN
FP=$(printf %s "$ANTHROPIC_API_KEY" | shasum -a 256 | cut -c1-12)
echo "credential: present, not the exposed key (sha256 $FP)"

TASKS="02-renewal-risk-regression g05-sco-rollout-gate g10-censored-demand g24-recommender-ope
g36-tou-capacity-gate p20-noshow-monitoring p22-gauge-recalibration p31-fill-rate-dispute
g50-courier-boost-rollout g08-forecast-accuracy-vintages"

# --- frozen-integrity gate: refuse to measure a benchmark that has drifted --------------------
rm -rf /tmp/xm_zipcheck && mkdir -p /tmp/xm_zipcheck
unzip -q submission_final10.zip 'samples/*' -d /tmp/xm_zipcheck || { echo "STOP: cannot read the submission archive"; exit 4; }
for t in $TASKS; do
  if ! diff -rq --exclude=__pycache__ "/tmp/xm_zipcheck/samples/$t" "candidates/$t" >/dev/null 2>&1; then
    echo "STOP: candidates/$t differs from the evaluated version. Not measuring a drifted benchmark."; exit 5
  fi
done
echo "frozen-integrity gate: all 10 tasks byte-identical to the evaluated versions"

# --- smoke test then the full matrix ----------------------------------------------------------
run_one() {
  local t="$1"
  local i="$2"
  local J="claude-${t}-${i}"
  local existing
  existing=$(cat "$OUT/$J"/*/verifier/reward.txt 2>/dev/null | head -1)
  if [ -n "$existing" ]; then echo "$J already has reward=$existing, skipping"; return 0; fi
  rm -rf "$OUT/$J"
  harbor run -p "candidates/$t" -a claude-code -m "$MODEL" \
    -k 1 -n 1 -o "$OUT" --job-name "$J" -y --agent-setup-timeout-multiplier 3.0 \
    > "logs/$J.log" 2>&1
  local rc=$? rw
  rw=$(cat "$OUT/$J/"*/verifier/reward.txt 2>/dev/null)
  if [ -z "$rw" ]; then
    echo "$J rc=$rc reward=NONE  -> INVALID (no reward emitted)"
    tail -8 "logs/$J.log" | sed 's/^/      /'
    mv "$OUT/$J" "$OUT/${J}__INVALID-no-reward-emitted" 2>/dev/null
    return 1
  fi
  if grep -q "refusing to grade" "$OUT/$J"/*/verifier/*.txt 2>/dev/null; then
    echo "$J -> INVALID (verifier refused to grade)"
    mv "$OUT/$J" "$OUT/${J}__INVALID-verifier-refused" 2>/dev/null
    return 1
  fi
  echo "$J rc=$rc reward=$rw"
  cat "$OUT/$J"/*/verifier/reward.json 2>/dev/null | sed 's/^/      /'
  return 0
}

echo; echo "=== STEP 4: smoke test (one trial, p22) ==="
run_one p22-gauge-recalibration 1 || { echo "SMOKE TEST INVALID - fix infrastructure only, never the task"; exit 6; }
echo "smoke test infrastructure-valid; it counts as p22 trial 1"

echo; echo "=== STEP 5: remaining trials, model=$MODEL, $N per task ==="
for t in $TASKS; do
  case " ${SKIP_TASKS:-} " in *" $t "*) echo "skipping $t (SKIP_TASKS)"; continue;; esac
  for i in $(seq 1 "$N"); do
    [ "$t" = "p22-gauge-recalibration" ] && [ "$i" = "1" ] && continue
    attempt=0
    until run_one "$t" "$i"; do
      attempt=$((attempt+1))
      [ "$attempt" -ge 3 ] && { echo "  giving up on $t trial $i after 3 invalid attempts"; break; }
      echo "  retrying $t trial $i (invalid attempt $attempt)"
    done
  done
done
echo; echo "ALL CLAUDE TRIALS COMPLETE"
