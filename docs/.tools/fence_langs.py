#!/usr/bin/env python3
import re
import json
from typing import Optional
from pathlib import Path

DOCS = Path("Documentation")

FENCE_RE = re.compile(r"```([a-zA-Z0-9_-]*)\n(.*?)\n```", re.DOTALL)

BASH_MARKERS = (
    "curl ", "npm ", "yarn ", "pnpm ", "pip ", "uvicorn ", "python ",
    "git ", "make ", "alembic ", "pytest ", "docker ", "lsof ", "psql ",
    "uvicorn", "node ", "npx ", "brew ", "sed ", "perl ", "grep ", "find "
)

HTTP_PREFIXES = ("GET http://", "GET https://", "POST http://", "POST https://",
                 "PUT http://", "PUT https://", "DELETE http://", "DELETE https://")


def detect_lang(body: str) -> Optional[str]:
    s = body.strip()
    # HTTP examples
    for p in HTTP_PREFIXES:
        if s.startswith(p):
            return "http"
    # Bash-like
    for m in BASH_MARKERS:
        if s.startswith(m) or f"\n{m}" in s:
            return "bash"
    # JSON (try parsing)
    if s.startswith("{") or s.startswith("["):
        try:
            json.loads(s)
            return "json"
        except Exception:
            pass
    # Lua heuristics
    if ("local " in s and "function" in s and "end" in s) or ("game." in s or "workspace" in s):
        return "lua"
    # Python heuristics
    if ("import " in s and "def " in s) or ("from " in s and " import " in s and ":\n" in s):
        return "python"
    return None


def process(md: Path) -> bool:
    orig = md.read_text(encoding="utf-8")
    changed = False
    def repl(m: re.Match) -> str:
        nonlocal changed
        lang = m.group(1)
        body = m.group(2)
        if lang and lang != "text":
            return m.group(0)
        dl = detect_lang(body)
        if dl:
            changed = True
            return f"```{dl}\n{body}\n```"
        # If no detection and no lang, leave as-is (possibly text)
        if not lang:
            # default to text for unlabeled
            changed = True
            return f"```text\n{body}\n```"
        return m.group(0)

    new = FENCE_RE.sub(repl, orig)
    if new != orig:
        md.write_text(new, encoding="utf-8")
    return changed


def main() -> int:
    if not DOCS.exists():
        return 0
    count = 0
    for md in DOCS.rglob("*.md"):
        try:
            if process(md):
                count += 1
        except Exception:
            continue
    print(f"Updated fences in {count} files")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
