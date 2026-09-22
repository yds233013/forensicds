#!/usr/bin/env bash
# Scan a directory (default: submission/) and a zip (default: submission.zip) for credential patterns.
# Prints only file paths and pattern NAMES, never matched values. Exit 1 on any finding.
set -uo pipefail
TARGET="${1:-submission}"; ZIP="${2:-submission.zip}"
python3 - "$TARGET" "$ZIP" <<'PY'
import os, re, sys, zipfile
PATS = {"google_api_key": rb"AIza[0-9A-Za-z_\-]{30,}", "anthropic_key": rb"sk-ant-[A-Za-z0-9_\-]{10,}",
        "openai_key": rb"sk-(proj-)?[A-Za-z0-9]{32,}", "github_token": rb"gh[pousr]_[A-Za-z0-9]{30,}",
        "aws_access_key": rb"AKIA[0-9A-Z]{16}", "private_key": rb"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        "slack_token": rb"xox[baprs]-[A-Za-z0-9-]{10,}",
        "env_assignment": rb"(GEMINI|ANTHROPIC|OPENAI|GOOGLE)_API_KEY\s*=\s*['\"]?[A-Za-z0-9_\-]{12,}"}
BAD_NAMES = {".env", ".envrc", ".zshrc", ".bashrc", ".bash_history", ".zsh_history", "id_rsa", "credentials"}
target, zpath = sys.argv[1], sys.argv[2]; findings = 0
def scan(name, data):
    global findings
    base = os.path.basename(name)
    if base in BAD_NAMES or base.startswith(".env"):
        print(f"FORBIDDEN FILE: {name}"); findings += 1
    for k, p in PATS.items():
        if re.search(p, data):
            print(f"PATTERN {k}: {name}"); findings += 1
for root, _, files in os.walk(target):
    for f in files:
        p = os.path.join(root, f)
        try:
            scan(p, open(p, "rb").read())
        except OSError:
            pass
if os.path.exists(zpath):
    with zipfile.ZipFile(zpath) as z:
        for n in z.namelist():
            scan("zip:" + n, z.read(n))
print(f"secret scan: {findings} finding(s)"); sys.exit(1 if findings else 0)
PY
