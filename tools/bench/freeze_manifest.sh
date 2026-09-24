#!/usr/bin/env bash
# Proposed freeze manifest for the three prospective tasks. Run from the repository root AFTER the tasks are
# `git add`-ed, so `git ls-files` sees every file. Prints per-file hashes and one checksum per task, using the
# same convention as the phase-1 freeze scripts.
set -euo pipefail
cd "$(dirname "$0")/../.."
echo "# ForensicDS phase 3 — PROPOSED freeze manifest (not a completed freeze)"
echo "# generated $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "# harbor $(harbor --version 2>&1 | head -1)"
for T in candidates/p22-gauge-recalibration candidates/p20-noshow-monitoring candidates/p31-fill-rate-dispute; do
  echo
  echo "## $T"
  git ls-files "$T" | while read -r f; do
    printf '%s  %s\n' "$(shasum -a 256 "$f" | cut -d' ' -f1)" "$f"
  done
  echo -n "checksum: "
  git ls-files "$T" | sort | while read -r f; do shasum -a 256 "$f"; done \
    | shasum -a 256 | cut -c1-16
done
