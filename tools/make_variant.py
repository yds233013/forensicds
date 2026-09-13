#!/usr/bin/env python3
"""Create a paired-condition copy of a Harbor task that differs only in instruction.md.

usage: make_variant.py <task_dir> <instruction.md> [--suffix NAME]
"""
import argparse
import hashlib
import re
import shutil
from pathlib import Path


def tree_digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_dir", type=Path)
    ap.add_argument("instruction", type=Path)
    ap.add_argument("--suffix", default=None)
    args = ap.parse_args()
    src = args.task_dir.resolve()
    suffix = args.suffix or args.instruction.stem
    dst = src.with_name(f"{src.name}__{suffix}")
    if dst.exists():
        raise SystemExit(f"{dst} exists")
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "jobs"))
    canary = (src / "instruction.md").read_text().splitlines()[0]
    body = args.instruction.read_text()
    (dst / "instruction.md").write_text(body if body.startswith("<!--") else f"{canary}\n{body}")
    toml = (dst / "task.toml").read_text()
    toml = re.sub(r'^name = "([^"]+)"', lambda m: f'name = "{m.group(1)}-{suffix}"', toml, count=1, flags=re.M)
    digests = {k: tree_digest(src / k) for k in ("environment", "tests", "solution")}
    prov = "\n".join(f'variant_{k}_sha256 = "{v}"' for k, v in digests.items())
    toml = toml.replace("[metadata]\n", f'[metadata]\nvariant_of = "{src.name}"\nvariant_condition = "{suffix}"\n{prov}\n', 1)
    (dst / "task.toml").write_text(toml)
    for k, v in digests.items():
        assert tree_digest(dst / k) == v, f"{k} differs after copy"
    print(dst)


if __name__ == "__main__":
    main()
