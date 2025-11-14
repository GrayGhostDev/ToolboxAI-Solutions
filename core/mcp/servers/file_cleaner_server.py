import json
import os
from pathlib import Path

# Simple cleaner that removes temporary task-scoped artifacts
PATTERNS = ["*.tmp", "*.bak", "*.tmp.md"]

EXCLUDES = {
    ".git",
    ".venv",
    "node_modules",
    "Archive",
    "Documentation/Archive",
    "docs/Archive",
}


def list_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDES]
        for fn in filenames:
            yield Path(dirpath) / fn


def main():
    root = Path(os.getcwd())
    removed = []
    for p in list_files(root):
        for pat in PATTERNS:
            if p.match(pat):
                try:
                    p.unlink(missing_ok=True)
                    removed.append(str(p))
                except Exception:
                    pass
                break
    print(json.dumps({"removed": removed}))


if __name__ == "__main__":
    main()
