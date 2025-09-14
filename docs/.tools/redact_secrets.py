#!/usr/bin/env python3
import re
import sys
from pathlib import Path

DOCS_ROOT = Path("Documentation")

SECRET_KV = re.compile(
    r"(API[_-]?KEY|ACCESS[_-]?KEY|SECRET|TOKEN|PASSWORD|PASS|CLIENT[_-]?SECRET)([:= ]+)" r"[A-Za-z0-9_\-\./+=]{8,}"
)
GITHUB_PAT = re.compile(r"ghp_[A-Za-z0-9]{20,}")
OPENAI_KEY = re.compile(r"sk-[A-Za-z0-9]{20,}")
GOOGLE_API = re.compile(r"AIzaSy[A-Za-z0-9\-_]{33}")
PEM_BLOCK = re.compile(
    r"(-----BEGIN [A-Z ]+ PRIVATE KEY-----)([\s\S]*?)(-----END [A-Z ]+ PRIVATE KEY-----)",
    re.MULTILINE,
)


def redact_text(text: str) -> str:
    text = SECRET_KV.sub(r"\1\2[REDACTED]", text)
    text = GITHUB_PAT.sub("[REDACTED]", text)
    text = OPENAI_KEY.sub("[REDACTED]", text)
    text = GOOGLE_API.sub("[REDACTED]", text)
    text = PEM_BLOCK.sub(r"\1\n[REDACTED]\n\3", text)
    return text


def main() -> int:
    if not DOCS_ROOT.exists():
        print("No Documentation/ directory found", file=sys.stderr)
        return 0

    changed = 0
    for md in DOCS_ROOT.rglob("*.md"):
        try:
            original = md.read_text(encoding="utf-8")
        except Exception:
            continue
        redacted = redact_text(original)
        if redacted != original:
            md.write_text(redacted, encoding="utf-8")
            changed += 1
    print(f"Redaction complete. Files changed: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

