"""Minimal reader for the serving config (the image has no yaml dependency guarantee)."""
from pathlib import Path


def ttl_seconds(path: Path) -> int:
    for line in Path(path).read_text().splitlines():
        s = line.strip()
        if s.startswith("ttl_seconds:"):
            return int(s.split(":", 1)[1].strip())
    raise KeyError("ttl_seconds not found in " + str(path))
