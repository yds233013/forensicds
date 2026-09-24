"""Infrastructure-validity adjudication for one prospective trial, from job artefacts alone.

Applies research/phase3/analysis_plan.md §2 mechanically and prints only infrastructure facts. It deliberately
does not open the trajectory: reading a trial's reasoning before adjudicating it is a protocol violation.

    python tools/bench/adjudicate.py jobs/<job-name>
"""
from __future__ import annotations

import glob
import json
import os
import sys

EXPECTED_DIGEST = {
    "p22-gauge-recalibration": "sha256:72fedb37da7b48c8488ad8afbcdf0d46b501dcdb52a6b05698a20370425629a7",
    "p20-noshow-monitoring": "sha256:f033ea1f5a8876514566174e8a99cf36d24e09cd54e9bba7ddfb5c16ffe60d8a",
    "p31-fill-rate-dispute": "sha256:3208a6d39014bff924784636da9a0837d528833f22e0666197d445330821f3ae",
}
AUTH_MARKERS = ("ApiUsageLimitError", "AgentAuthenticationError", "ModelNotFoundError", "quota",
                "RESOURCE_EXHAUSTED", "PERMISSION_DENIED", "UNAUTHENTICATED", "api key", "API key")
SETUP_MARKERS = ("AgentSetupTimeout", "agent setup timed out", "AgentTimeoutError")


def main(job: str) -> int:
    out = {"job": job}
    lock = json.load(open(f"{job}/lock.json"))
    tr = lock["trials"][0]
    task = tr["task"]
    out["task"] = task["name"]
    out["task_digest"] = task["digest"]
    out["model"] = tr.get("agent", {}).get("model_name")
    out["agent"] = tr.get("agent", {}).get("name")
    out["digest_matches_freeze"] = (task["digest"] == EXPECTED_DIGEST.get(task["name"]))

    res = json.load(open(f"{job}/result.json"))
    out["started_at"], out["finished_at"] = res.get("started_at"), res.get("finished_at")

    tp = glob.glob(f"{job}/*/result.json")
    trial = json.load(open(tp[0])) if tp else {}
    out["trial_name"] = trial.get("trial_name")
    out["exception_info"] = trial.get("exception_info")
    out["failure_mode"] = trial.get("failure_mode")
    vr = trial.get("verifier_result") or {}
    out["rewards"] = vr.get("rewards")

    d = os.path.dirname(tp[0]) if tp else job
    so = f"{d}/verifier/test-stdout.txt"
    out["verifier_stdout_bytes"] = os.path.getsize(so) if os.path.exists(so) else 0
    out["verifier_reward_txt_present"] = os.path.exists(f"{d}/verifier/reward.txt")
    exc = glob.glob(f"{d}/**/exception.txt", recursive=True)
    out["exception_files"] = exc

    # cost / usage, where Harbor exposes it
    for k in ("total_cost", "cost", "usage", "token_usage", "n_input_tokens", "n_output_tokens"):
        if k in trial:
            out[k] = trial[k]
    blob = json.dumps(trial)
    for key in ("total_cost_usd", "cost_usd", "input_tokens", "output_tokens"):
        if f'"{key}"' in blob:
            out.setdefault("usage_keys_present", []).append(key)

    # --- the preregistered rule, applied
    reasons = []
    text = (json.dumps(out.get("exception_info")) or "") + " ".join(
        open(f).read()[:4000] for f in exc if os.path.exists(f))
    if any(m in text for m in AUTH_MARKERS):
        reasons.append("API, quota or authentication error")
    if any(m in text for m in SETUP_MARKERS):
        reasons.append("agent-setup timeout")
    if out["verifier_stdout_bytes"] == 0:
        reasons.append("verifier never executed (0-byte verifier stdout)")
    rw = (out["rewards"] or {}).get("reward")
    if rw == 0 and out["verifier_stdout_bytes"] == 0:
        reasons.append("container-teardown signature (reward 0 with 0-byte verifier stdout)")
    if not out["digest_matches_freeze"]:
        reasons.append("task digest does not match the freeze")

    out["verdict"] = "VALID" if not reasons else "INVALID"
    out["invalid_reasons"] = reasons
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
