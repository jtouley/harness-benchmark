#!/usr/bin/env python3
"""Tool-measured code quality of one solution, against the untouched baseline.

The measures and thresholds are defined in docs/quality-model.md. Each comes from a
published, widely used source, so that anyone can recompute it:

- new-code coverage: coverage.py line coverage of the executable lines the change adds,
  the "new code" idea of the SonarQube "Sonar way" quality gate (>= 80%); line and
  branch coverage of the whole package are reported too;
- cyclomatic complexity per function: radon (McCabe 1976; > 10 flagged);
- cognitive complexity per function: complexipy (SonarSource 2017; > 15 flagged);
  for both, a function is flagged when the change takes it over the threshold: it is
  new and over it, or it was at or under it in the baseline and is over it now;
- maintainability index: radon (the Visual Studio variant, 0-100), reported;
- lint: ruff with a fixed rule set (pyflakes, pycodestyle without line length, bugbear,
  pylint, simplify, pyupgrade, mccabe);
- type errors: mypy with --check-untyped-defs, so unannotated code is checked too.

"New" means on the lines the change adds (from CHANGE.diff): a finding on an added line,
or a function whose body holds an added line. Fixing an old problem cannot hide a new one.

A tool that fails (an exit code outside its normal codes, or output that does not parse)
raises. Its measure is then None, and the gate fails: an unmeasured value never passes.
Tool versions are pinned below, so the numbers reproduce.

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

TOOLS = {"ruff": "ruff==0.17.0", "radon": "radon==6.0.1", "complexipy": "complexipy==8.0.1", "mypy": "mypy==2.4.0"}
PYTEST = ["--with", "pytest==9.1.1", "--with", "pytest-cov==7.1.0", "--with", "coverage==7.16.2"]
RUFF_RULES = "E,F,W,B,PL,SIM,UP,C90"
RUFF_IGNORE = "E501"  # line length is formatting, not a defect; the Sonar way gate does not use it
# Findings that are likely bugs, the analogue of the gate's "no new bugs": undefined or
# redefined names and broken comparisons or statements from pyflakes (F82, F811, F63, F7),
# syntax and runtime errors (E9), bugbear (B) and pylint errors (PLE). The rest, such as
# an unused import (F401), are smells.
BUG_PREFIXES = ("F82", "F811", "F63", "F7", "E9", "B", "PLE")
THRESHOLDS = {"new_code_coverage": 80.0, "cyclomatic": 10, "cognitive": 15}


class ToolError(RuntimeError):
    """A measuring tool failed, so its measure is unknown."""


def _run(args: list[str], cwd: Path, ok: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if proc.returncode not in ok:
        raise ToolError(f"{' '.join(args[:4])} exited {proc.returncode}: {(proc.stderr or proc.stdout)[-300:]}")
    return proc


def _json(text: str, what: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ToolError(f"{what}: output is not JSON: {text[:200]}") from exc


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
        elif current and not line.startswith(("-", "\\")):  # "\ No newline at end of file" is not a line
            line_no += 1
    return out


def is_bug(code: str) -> bool:
    return code.startswith(BUG_PREFIXES)


def newly_over(after: list[dict], before: list[dict], threshold: int) -> list[str]:
    """Functions the change takes over the threshold: new and over it, or over it now and not before."""
    was = {(f["file"], f["name"]): f["value"] for f in before}
    return sorted(f"{f['file']}:{f['name']}={f['value']}" for f in after
                  if f["value"] > threshold and was.get((f["file"], f["name"]), 0) <= threshold)


def new_line_coverage(data: dict, added: dict[str, set[int]]) -> tuple[int, int]:
    """(covered, executable) counts over the added lines, from a coverage.py JSON report."""
    hit = executable = 0
    for path, lines in added.items():
        f = data["files"].get(path) or {}
        executed = set(f.get("executed_lines", []))
        executable += len(lines & (executed | set(f.get("missing_lines", []))))
        hit += len(lines & executed)
    return hit, executable


def coverage(solution: Path, package: str, added: dict[str, set[int]]) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "cov.json"
        proc = _run(["uv", "run", "--quiet", "--no-project", *PYTEST, "python", "-m", "pytest", "-o", "addopts=",
                     "-p", "no:cacheprovider", f"--cov={package}", "--cov-branch", f"--cov-report=json:{report}"],
                    solution, ok=(0, 1))
        if not report.is_file():
            raise ToolError(f"pytest wrote no coverage report: {proc.stdout[-300:]}")
        data = _json(report.read_text(), "coverage")
    passed = re.search(r"(\d+) passed", proc.stdout)
    failed = re.search(r"(\d+) failed", proc.stdout)
    errors = re.search(r"(\d+) errors?\b", proc.stdout)
    new_hit, new_exec = new_line_coverage(data, added)
    totals = data["totals"]
    return {
        "tests_passed": int(passed.group(1)) if passed else 0,
        "tests_failed": (int(failed.group(1)) if failed else 0) + (int(errors.group(1)) if errors else 0),
        "line_coverage": round(totals.get("percent_covered", 0.0), 1),
        "branch_coverage": round(100 * totals.get("covered_branches", 0) / totals["num_branches"], 1)
        if totals.get("num_branches") else None,
        "new_code_coverage": round(100 * new_hit / new_exec, 1) if new_exec else None,
        "new_executable_lines": new_exec,
    }


def cyclomatic(path: Path, package: str) -> list[dict]:
    """Functions and methods with their complexity and line span (radon lists each once at top level)."""
    data = _json(_run(["uvx", "--quiet", TOOLS["radon"], "cc", "-j", package], path).stdout, "radon cc")
    out = []
    for file, blocks in data.items():
        for b in blocks if isinstance(blocks, list) else []:
            if b.get("type") in ("function", "method"):
                name = f"{b['classname']}.{b['name']}" if b.get("classname") else b["name"]
                out.append({"file": file, "name": name,
                            "lines": set(range(b["lineno"], b["endline"] + 1)), "value": b["complexity"]})
    return out


def cognitive(path: Path, package: str) -> list[dict]:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "cx.json"
        _run(["uvx", "--quiet", TOOLS["complexipy"], package, "--output-format", "json", "--output", str(out), "-q"],
             path, ok=(0, 1))
        if not out.is_file():
            raise ToolError("complexipy wrote no report")
        rows = _json(out.read_text(), "complexipy")
    return [{"file": r["path"], "name": r["function_name"], "value": r["complexity"]} for r in rows]


def maintainability(path: Path, package: str) -> float | None:
    data = _json(_run(["uvx", "--quiet", TOOLS["radon"], "mi", "-j", package], path).stdout, "radon mi")
    values = [v["mi"] for v in data.values() if isinstance(v, dict) and "mi" in v]
    return round(sum(values) / len(values), 1) if values else None


def lint(path: Path, package: str) -> list[dict]:
    proc = _run(["uvx", "--quiet", TOOLS["ruff"], "check", "--no-cache", "--output-format", "json",
                 "--select", RUFF_RULES, "--ignore", RUFF_IGNORE, package], path, ok=(0, 1))
    return [{"code": v["code"], "file": Path(v["filename"]).resolve().relative_to(path.resolve()).as_posix(),
             "line": v["location"]["row"]} for v in _json(proc.stdout or "[]", "ruff")]


def type_errors(path: Path, package: str) -> list[dict]:
    proc = _run(["uvx", "--quiet", TOOLS["mypy"], "--check-untyped-defs", "--ignore-missing-imports",
                 "--no-error-summary", "--no-incremental", package], path, ok=(0, 1))
    out = []
    for line in proc.stdout.splitlines():
        m = re.match(r"^(.+?):(\d+):(?:\d+:)? error:", line)
        if m:
            out.append({"file": Path(m.group(1)).as_posix(), "line": int(m.group(2))})
    return out


def _on_added(items: list[dict], added: dict[str, set[int]]) -> list[dict]:
    return [i for i in items if i["line"] in added.get(i["file"], set())]


def _measure(fn, *args):
    try:
        return fn(*args), None
    except ToolError as exc:
        return None, str(exc)


def measure(solution: Path, baseline: Path, package: str) -> dict:
    added = added_lines((solution / "CHANGE.diff").read_text(encoding="utf-8", errors="replace"), package)
    errors: dict[str, str] = {}
    result: dict = {"package_lines_added": sum(len(v) for v in added.values())}

    cov, err = _measure(coverage, solution, package, added)
    result.update(cov or {"tests_passed": None, "tests_failed": None, "new_code_coverage": None})
    if err:
        errors["coverage"] = err

    for kind, tool in (("cyclomatic", cyclomatic), ("cognitive", cognitive)):
        after, err1 = _measure(tool, solution, package)
        before, err2 = _measure(tool, baseline, package)
        if err1 or err2:
            errors[kind] = err1 or err2
            continue
        result[f"{kind}_max"] = max((f["value"] for f in after), default=0)
        result[f"{kind}_newly_over_{THRESHOLDS[kind]}"] = newly_over(after, before, THRESHOLDS[kind])

    mi, err = _measure(maintainability, solution, package)
    result["maintainability_index"] = mi
    if err:
        errors["maintainability"] = err

    findings, err = _measure(lint, solution, package)
    if err:
        errors["lint"] = err
    else:
        new = _on_added(findings, added)
        result["lint_new_by_rule"] = {c: sum(1 for f in new if f["code"] == c) for c in sorted({f["code"] for f in new})}
        result["bug_findings_new"] = sum(1 for f in new if is_bug(f["code"]))
        lines = result["package_lines_added"]
        result["smells_per_100_new_lines"] = round(100 * (len(new) - result["bug_findings_new"]) / lines, 1) if lines else 0.0

    types, err = _measure(type_errors, solution, package)
    if err:
        errors["types"] = err
    else:
        result["type_errors_new"] = len(_on_added(types, added))

    ncc = result.get("new_code_coverage")
    result["gate"] = {
        "tests_pass": result.get("tests_failed") == 0 and (result.get("tests_passed") or 0) > 0,
        "new_code_coverage_at_least_80": ncc is not None and ncc >= THRESHOLDS["new_code_coverage"],
        "no_function_newly_over_cyclomatic_10": "cyclomatic" not in errors and not result["cyclomatic_newly_over_10"],
        "no_function_newly_over_cognitive_15": "cognitive" not in errors and not result["cognitive_newly_over_15"],
        "no_new_bug_findings": "lint" not in errors and result["bug_findings_new"] == 0,
        "no_new_type_errors": "types" not in errors and result["type_errors_new"] == 0,
    }
    result["gate_passed"] = all(result["gate"].values())
    result["tool_errors"] = errors
    result["tools"] = {**TOOLS, "pytest": "pytest==9.1.1", "pytest-cov": "pytest-cov==7.1.0", "coverage": "coverage==7.16.2"}
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
