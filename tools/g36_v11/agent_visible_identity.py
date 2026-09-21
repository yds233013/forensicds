"""Agent-visible byte-identity gate: original G36 vs v1.1.
Agent-visible = instruction.md + everything under environment/ (the only inputs to the image the agent
works in). Also compares every file of /workspace inside the two BUILT images when --images is given."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT = Path("/Users/yashshah2311/forensicds/candidates")
O, N = ROOT / "g36-tou-capacity-gate", ROOT / "g36-tou-capacity-gate-v1.1"


def files(base):
    out = [base / "instruction.md"]
    out += sorted(p for p in (base / "environment").rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return out


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def image_tree(tag):
    cmd = ("cd /workspace && find . -type f -not -path '*/__pycache__/*' | LC_ALL=C sort | "
           "while read f; do sha256sum \"$f\"; done")
    r = subprocess.run(["docker", "run", "--rm", tag, "bash", "-c", cmd], capture_output=True, text=True)
    return dict((l.split()[1], l.split()[0]) for l in r.stdout.splitlines() if l.strip())


def main():
    rows, bad = [], 0
    for p in files(O):
        rel = p.relative_to(O); q = N / rel
        a = sha(p); b = sha(q) if q.exists() else "MISSING"
        rows.append((str(rel), a, b, a == b)); bad += a != b
    extra = [str(p.relative_to(N)) for p in files(N) if not (O / p.relative_to(N)).exists()]
    for r in rows:
        print("%-70s %s %s %s" % (r[0], r[1][:16], r[2][:16], "identical" if r[3] else "*** DIFFERS ***"))
    print("\nsource artefacts: %d, differing: %d, extra in v1.1: %s" % (len(rows), bad, extra or "none"))
    digest = hashlib.sha256("".join(r[0] + r[1] for r in rows).encode()).hexdigest()[:16]
    print("agent-visible manifest digest (original): %s" % digest)
    digest_n = hashlib.sha256("".join(r[0] + r[2] for r in rows).encode()).hexdigest()[:16]
    print("agent-visible manifest digest (v1.1)    : %s" % digest_n)
    res = {"rows": rows, "extra": extra, "digest_orig": digest, "digest_v11": digest_n}
    if "--images" in sys.argv:
        ti, tn = image_tree(sys.argv[sys.argv.index("--images") + 1]), image_tree(sys.argv[sys.argv.index("--images") + 2])
        diff = sorted(set(ti) ^ set(tn)) + [k for k in ti if k in tn and ti[k] != tn[k]]
        print("\nbuilt-image /workspace files: original %d, v1.1 %d, differing %d" % (len(ti), len(tn), len(diff)))
        for k in sorted(ti): print("   %-58s %s %s" % (k, ti[k][:16], "identical" if tn.get(k) == ti[k] else "*** DIFFERS ***"))
        res["image"] = {"orig": ti, "v11": tn, "diff": diff}
        bad += len(diff)
    Path("/Users/yashshah2311/forensicds/research/g36/v1_1/agent_visible_identity.json").write_text(json.dumps(res, indent=1))
    print("\nGATE: %s" % ("PASS - agent information set identical" if bad == 0 and not extra else "FAIL"))
    sys.exit(0 if bad == 0 and not extra else 1)


if __name__ == "__main__":
    main()
