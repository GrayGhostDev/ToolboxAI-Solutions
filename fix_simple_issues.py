#!/usr/bin/env python3
"""Fix simple flake8 issues: trailing whitespace, blank lines, etc."""

from pathlib import Path

BACKEND_DIR = Path("apps/backend")


def fix_file(filepath):
    """Fix simple issues in a single file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        original = content
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            # Remove trailing whitespace (W291)
            line = line.rstrip()
            fixed_lines.append(line)

        content = "\n".join(fixed_lines)

        if content != original:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False


def main():
    fixed = 0
    for pyfile in BACKEND_DIR.rglob("*.py"):
        if "__pycache__" in str(pyfile):
            continue
        if fix_file(pyfile):
            fixed += 1
            print(f"Fixed: {pyfile.relative_to(BACKEND_DIR)}")

    print(f"\nTotal files fixed: {fixed}")


if __name__ == "__main__":
    main()
