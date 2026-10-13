#!/usr/bin/env python3
"""Tool-measured code quality of one solution, against the untouched baseline.

The measures and thresholds are defined in docs/quality-model.md. Each one comes from a
published, widely used source, so that anyone can recompute it and nobody has to trust a
grader for it:

- new-code coverage (line and branch): coverage.py on the lines the change adds, the
  "new code" idea of the SonarQube "Sonar way" quality gate (>= 80%);
- cyclomatic complexity per function: radon (McCabe 1976; > 10 flagged);
- cognitive complexity per function: complexipy (SonarSource 2017; > 15 flagged, the
  Sonar default);
- maintainability index: radon (the Visual Studio variant, 0-100);
- lint: ruff with a fixed rule set (pyflakes, pycodestyle without line length, bugbear,
  pylint, simplify, pyupgrade, mccabe); only violations the change adds count;
- type errors: mypy with its default settings; only errors the change adds count.

usage: quality_metrics.py SOLUTION_DIR BASELINE_DIR [--package ledgerlite]
SOLUTION_DIR holds the package, tests/ and CHANGE.diff (a diff from the baseline).
Prints one JSON object. Needs uv (tools run through `uvx` and `uv run --with`).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RUFF_RULES = "E,F,W,B,PL,SIM,UP,C90"
RUFF_IGNORE = "E501"  # line length is formatting, not a defect; the Sonar way gate does not use it
THRESHOLDS = {"new_code_coverage": 80.0, "cyclomatic": 10, "cognitive": 15}


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def added_lines(diff: str, package: str) -> dict[str, set[int]]:
    """{file: added line numbers} for .py files of the package, from a unified diff."""
    out: dict[str, set[int]] = {}
    current, line_no = None, 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[4:].strip()
            path = path[2:] if path.startswith("b/") else path
            current = path if path.startswith(f"{package}/") and path.endswith(".py") else None
            if current:
                out.setdefault(current, set())
        elif line.startswith("@@") and current:
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            line_no = int(m.group(1)) if m else 0
        elif current and line.startswith("+") and not line.startswith("+++"):
            out[current].add(line_no)
            line_no += 1
        elif current and not line.startswith("-"):
            line_no += 1
    return out


def coverage(solution: Path, package: str, added: dict[str, set[int]]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "cov.json"
        proc = _run(["uv", "run", "--quiet", "--no-project", "--with", "pytest", "--with", "pytest-cov",
                     "python", "-m", "pytest", "-o", "addopts=", "-p", "no:cacheprovider", f"--cov={package}", "--cov-branch",
                     f"--cov-report=json:{report}"], solution)
        if not report.is_file():
            return {"error": proc.stdout[-400:] + proc.stderr[-400:]}
        data = json.loads(report.read_text())
    tests = re.search(r"(\d+) passed", proc.stdout)
    failed = re.search(r"(\d+) failed", proc.stdout)
    new_exec = new_hit = 0
    for path, lines in added.items():
        f = data["files"].get(path) or {}
        executable = set(f.get("executed_lines", [])) | set(f.get("missing_lines", []))
        new_exec += len(lines & executable)
        new_hit += len(lines & set(f.get("executed_lines", [])))
    totals = data["totals"]
    return {
        "tests_passed": int(tests.group(1)) if tests else 0,
        "tests_failed": int(failed.group(1)) if failed else 0,
        "line_coverage": round(totals.get("percent_covered", 0.0), 1),
        "branch_coverage": round(100 * totals.get("covered_branches", 0) / totals["num_branches"], 1)
        if totals.get("num_branches") else None,
        "new_code_coverage": round(100 * new_hit / new_exec, 1) if new_exec else None,
        "new_executable_lines": new_exec,
    }


def cyclomatic(path: Path, package: str) -> list[int]:
    data = json.loads(_run(["uvx", "--quiet", "radon", "cc", "-j", package], path).stdout or "{}")
    values = []
    for blocks in data.values():
        for b in blocks if isinstance(blocks, list) else []:
            if b.get("type") in ("function", "method"):
                values.append(b["complexity"])
            for m in b.get("methods", []):
                values.append(m["complexity"])
    return values


def cognitive(path: Path, package: str) -> list[int]:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "cx.json"
        _run(["uvx", "--quiet", "complexipy", package, "--output-format", "json", "--output", str(out), "-q"], path)
        return [f["complexity"] for f in json.loads(out.read_text())] if out.is_file() else []


def maintainability(path: Path, package: str) -> float | None:
    data = json.loads(_run(["uvx", "--quiet", "radon", "mi", "-j", package], path).stdout or "{}")
    values = [v["mi"] for v in data.values() if isinstance(v, dict) and "mi" in v]
    return round(sum(values) / len(values), 1) if values else None


def lint(path: Path, package: str) -> dict[str, int]:
    proc = _run(["uvx", "--quiet", "ruff", "check", "--no-cache", "--output-format", "json",
                 "--select", RUFF_RULES, "--ignore", RUFF_IGNORE, package], path)
    counts: dict[str, int] = {}
    for v in json.loads(proc.stdout or "[]"):
        counts[v["code"]] = counts.get(v["code"], 0) + 1
    return counts


# Findings that are likely bugs, the analogue of the gate's "no new bugs": pyflakes (F),
# syntax and runtime errors (E9), bugbear (B) and pylint errors (PLE). The rest are smells.
BUG_PREFIXES = ("F", "E9", "B", "PLE")


def _bugs(counts: dict[str, int]) -> int:
    return sum(n for code, n in counts.items() if code.startswith(BUG_PREFIXES))


def type_errors(path: Path, package: str) -> int:
    proc = _run(["uvx", "--quiet", "mypy", "--ignore-missing-imports", "--no-error-summary", package], path)
    return sum(1 for line in proc.stdout.splitlines() if ": error:" in line)


def measure(solution: Path, baseline: Path, package: str) -> dict:
    added = added_lines((solution / "CHANGE.diff").read_text(encoding="utf-8", errors="replace"), package)
    cc, cc0 = cyclomatic(solution, package), cyclomatic(baseline, package)
    cx, cx0 = cognitive(solution, package), cognitive(baseline, package)
    ruff, ruff0 = lint(solution, package), lint(baseline, package)
    mypy, mypy0 = type_errors(solution, package), type_errors(baseline, package)
    cov = coverage(solution, package, added)
    result = {
        **cov,
        "cyclomatic_max": max(cc, default=0),
        "cyclomatic_over_10_added": sum(v > THRESHOLDS["cyclomatic"] for v in cc) - sum(v > THRESHOLDS["cyclomatic"] for v in cc0),
        "cognitive_max": max(cx, default=0),
        "cognitive_over_15_added": sum(v > THRESHOLDS["cognitive"] for v in cx) - sum(v > THRESHOLDS["cognitive"] for v in cx0),
        "maintainability_index": maintainability(solution, package),
        "lint_violations_added": max(0, sum(ruff.values()) - sum(ruff0.values())),
        "bug_findings_added": max(0, _bugs(ruff) - _bugs(ruff0)),
        "lint_by_rule": ruff,
        "type_errors_added": max(0, mypy - mypy0),
        "package_lines_added": sum(len(v) for v in added.values()),
    }
    lines = result["package_lines_added"]
    result["smells_per_100_new_lines"] = round(100 * result["lint_violations_added"] / lines, 1) if lines else 0.0
    ncc = result.get("new_code_coverage")
    result["gate"] = {
        "new_code_coverage_at_least_80": ncc is not None and ncc >= THRESHOLDS["new_code_coverage"],
        "no_new_function_over_cognitive_15": result["cognitive_over_15_added"] <= 0,
        "no_new_function_over_cyclomatic_10": result["cyclomatic_over_10_added"] <= 0,
        "no_new_bug_findings": result["bug_findings_added"] == 0,
        "no_new_type_errors": result["type_errors_added"] == 0,
    }
    result["gate_passed"] = all(result["gate"].values())
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tool-measured quality of one solution")
    parser.add_argument("solution", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("--package", default="ledgerlite")
    args = parser.parse_args(argv)
    print(json.dumps(measure(args.solution.resolve(), args.baseline.resolve(), args.package), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
