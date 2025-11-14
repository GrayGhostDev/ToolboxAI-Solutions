import json
import os
import re
import subprocess

TEST_PASS_THRESHOLD = float(os.environ.get("TEST_PASS_THRESHOLD", "0.95"))
COVERAGE_MIN = float(os.environ.get("COVERAGE_MIN", "0.80"))
RE_STUB = re.compile(r"(?i)(TODO|FIXME|STUB|MOCK|SCAFFOLD|TEMPORARY|SHORTCUT)")


def _run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)


def check_no_stubs(diff_text: str) -> tuple[bool, str]:
    m = RE_STUB.search(diff_text or "")
    return (
        m is None,
        "No stubs/simplifications found" if m is None else f"Found stub-like marker: {m.group(0)}",
    )


def check_tests() -> tuple[bool, str]:
    r = _run(
        [
            "pytest",
            "-q",
            "--maxfail=1",
            "--disable-warnings",
            "--json-report",
            "--json-report-file=reports/pytest.json",
            "--cov",
            "--cov-report=xml:reports/coverage.xml",
        ]
    )
    if r.returncode != 0:
        return (False, "pytest failed")
    try:
        with open("reports/pytest.json") as f:
            data = json.load(f)
        s = data.get("summary", {})
        ratio = s.get("passed", 0) / max(1, s.get("total", 1))
        if ratio < TEST_PASS_THRESHOLD:
            return (False, f"Test pass ratio {ratio:.2%} < {TEST_PASS_THRESHOLD:.0%}")
    except Exception:
        return (False, "Could not parse pytest JSON")
    return (True, "Tests meet threshold")


def check_coverage() -> tuple[bool, str]:
    try:
        import xml.etree.ElementTree as ET

        tree = ET.parse("reports/coverage.xml")
        cov = float(tree.getroot().attrib.get("line-rate", "0"))
        if cov < COVERAGE_MIN:
            return (False, f"Coverage {cov:.2%} < {COVERAGE_MIN:.0%}")
        return (True, f"Coverage {cov:.2%}")
    except Exception as e:
        return (False, f"Coverage parse error: {e}")


def check_lint() -> tuple[bool, str]:
    r = _run(["ruff", "check", "--quiet", "."])
    return (r.returncode == 0, "Lint OK" if r.returncode == 0 else r.stderr[:4000])


def check_typecheck() -> tuple[bool, str]:
    r = _run(["mypy", "--strict", "."])
    return (r.returncode == 0, "Typecheck OK" if r.returncode == 0 else r.stdout[:4000])
