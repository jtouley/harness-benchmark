#!/usr/bin/env python3
"""Tool-measured code quality of one solution, against the untouched baseline.

The measures and thresholds are defined in docs/method/quality-model.md. Each comes from a
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
- type errors: mypy with --check-untyped-defs, so unannotated code is checked too;
- duplicated lines on new code: jscpd, minimum block 5 lines, over Python, SQL, Scala and
  YAML (the Sonar way gate's duplication condition, <= 3%);
- module coupling: afferent and efferent coupling and instability per module, from the
  import graph (Martin, Agile Software Development, 2002), reported, not gated;
- edit radius (--follow-up REPO BASE HEAD): the existing files a follow-up change modifies
  and their changed lines, apart from the files it adds; for the package and for the whole repo.

"New" means on the lines the change adds (from CHANGE.diff): a finding on an added line,
or a function whose body holds an added line. Fixing an old problem cannot hide a new one.

A tool that fails (an exit code outside its normal codes, or output that does not parse)
raises. Its measure is then None, and the gate fails: an unmeasured value never passes.
Tool versions are pinned below, so the numbers reproduce.

usage: quality_metrics.py SOLUTION_DIR BASELINE_DIR [--package ledgerlite]
SOLUTION_DIR holds the package, tests/ and CHANGE.diff (a diff from the baseline).
Prints one JSON object. Needs uv (tools run through `uvx` and `uv run --with`) and git.
jscpd is a Node tool; it runs as `uvx --from nodejs-wheel==X npx jscpd@Y`, so a pinned Node
comes from PyPI and the host's own node (which can be broken) is never used.
"""

from __future__ import annotations

import argparse
import ast
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
# jscpd 5 with a pinned Node from PyPI (nodejs-wheel); jscpd's default of 50 tokens per block stays.
NODE = "nodejs-wheel==24.19.0"
JSCPD = "jscpd@5.4.1"
JSCPD_FORMATS = "python,sql,scala,yaml"
DUPLICATION_SUFFIXES = (".py", ".sql", ".scala", ".yaml", ".yml")
MIN_CLONE_LINES = 5
THRESHOLDS = {"new_code_coverage": 80.0, "cyclomatic": 10, "cognitive": 15, "new_code_duplication": 3.0}


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


def added_lines(diff: str, package: str, suffixes: tuple[str, ...] = (".py",)) -> dict[str, set[int]]:
    """{file: added line numbers} for the package's files with these suffixes, from a unified diff."""
    out: dict[str, set[int]] = {}
    current, line_no = None, 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[4:].split("\t")[0].strip()  # diff -u appends a tab and a timestamp
            path = path[2:] if path.startswith("b/") else path
            current = path if path.startswith(f"{package}/") and path.endswith(suffixes) else None
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


def duplicated_lines(report: dict, package: str) -> dict[str, set[int]]:
    """{file: lines inside a clone} from a jscpd JSON report; both sides of each clone count.

    jscpd names files relative to the scanned directory, which is the package."""
    out: dict[str, set[int]] = {}
    for clone in report.get("duplicates", []):
        for side in (clone["firstFile"], clone["secondFile"]):
            name = f"{package}/{Path(side['name']).as_posix()}"
            out.setdefault(name, set()).update(range(side["start"], side["end"] + 1))
    return out


def new_code_duplication(duplicated: dict[str, set[int]], added: dict[str, set[int]]) -> dict:
    """Duplicated lines on new code: the share of added lines that sit inside a clone."""
    new = sum(len(lines) for lines in added.values())
    dup = sum(len(lines & duplicated.get(f, set())) for f, lines in added.items())
    return {"new_duplicated_lines": dup, "new_lines": new,
            "new_code_duplication": round(100 * dup / new, 1) if new else 0.0}


def duplication(path: Path, package: str, added: dict[str, set[int]]) -> dict:
    """jscpd over the package. An empty config of our own and --no-gitignore keep a `.jscpd.json`,
    a `package.json` "jscpd" key or a `.gitignore` in the measured solution from changing the scan."""
    with tempfile.TemporaryDirectory() as tmp:
        config = Path(tmp) / "jscpd.json"
        config.write_text("{}")
        _run(["uvx", "--quiet", "--from", NODE, "npx", "--yes", JSCPD, "--config", str(config), "--no-gitignore",
              "--min-lines", str(MIN_CLONE_LINES), "--format", JSCPD_FORMATS, "--reporters", "json",
              "--output", tmp, "--silent", package], path)
        report_file = Path(tmp) / "jscpd-report.json"
        if not report_file.is_file():
            raise ToolError("jscpd wrote no report")
        report = _json(report_file.read_text(), "jscpd")
    try:
        dup = duplicated_lines(report, package)
        total = report["statistics"]["total"]["duplicatedLines"]
    except (KeyError, TypeError) as exc:
        raise ToolError(f"jscpd report has an unexpected shape: {exc!r}") from exc
    return {**new_code_duplication(dup, added), "duplicated_lines_total": total}


def _python_modules(path: Path, package: str) -> dict[str, Path]:
    out = {}
    for file in sorted((path / package).rglob("*.py")):
        parts = list(file.relative_to(path).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        out[".".join(parts)] = file
    return out


def _imported_names(tree: ast.AST, here: str) -> set[str]:
    """Dotted names a module imports; `here` is its package, the anchor of relative imports.
    `from X import y` yields X.y, which resolves to module X.y or, failing that, to X."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                anchor = here.rsplit(".", node.level - 1)[0] if node.level > 1 else here
                base = f"{anchor}.{base}" if base else anchor
            names.update(base if a.name == "*" else f"{base}.{a.name}" for a in node.names)
    return names


def python_import_graph(path: Path, package: str) -> dict[str, set[str]]:
    """{module: modules of the package it imports}; imports from outside the package are left out."""
    modules = _python_modules(path, package)

    def target(name: str) -> str | None:
        while name and name not in modules:
            name = name.rpartition(".")[0]
        return name or None

    graph: dict[str, set[str]] = {}
    for module, file in modules.items():
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        except (SyntaxError, ValueError) as exc:
            raise ToolError(f"cannot parse {file.relative_to(path)}: {exc}") from exc
        here = module if file.name == "__init__.py" else module.rpartition(".")[0]
        graph[module] = {t for n in _imported_names(tree, here) if (t := target(n))} - {module}
    return graph


# One import-graph reader per language; SQL, Scala and YAML readers plug in here.
IMPORT_GRAPHS = {"python": python_import_graph}


def coupling(graph: dict[str, set[str]]) -> dict[str, dict]:
    """Per module: afferent coupling Ca (modules that import it), efferent coupling Ce (modules it
    imports) and instability I = Ce / (Ca + Ce), None for a module with neither (Martin 2002)."""
    afferent = {m: 0 for m in graph}
    for deps in graph.values():
        for d in deps:
            afferent[d] = afferent.get(d, 0) + 1
    out = {}
    for m in sorted(afferent):
        ca, ce = afferent[m], len(graph.get(m, ()))
        out[m] = {"afferent": ca, "efferent": ce, "instability": round(ce / (ca + ce), 2) if ca + ce else None}
    return out


def module_coupling(path: Path, package: str, language: str = "python") -> dict[str, dict]:
    reader = IMPORT_GRAPHS.get(language)
    if reader is None:
        raise ToolError(f"no import-graph reader for {language}")
    return coupling(reader(path, package))


def _radius(existing: list[dict], new: list[dict]) -> dict:
    return {"existing_files_changed": len(existing),
            "existing_lines_changed": sum(e["added"] + e["removed"] for e in existing),
            "existing": existing, "new_files": new}


def edit_radius(repo: Path, base: str, head: str, package: str) -> dict:
    """The existing files (modified or deleted) a change from base to head touches and their
    changed lines, apart from the files it adds. Renames count as a deletion plus a new file.
    Reported for the package and for the whole repo (tests, docs and other files included).
    `git diff -z` keeps file names raw, so a name with a tab or non-ASCII characters is not quoted."""
    status = _run(["git", "diff", "-z", "--no-renames", "--name-status", base, head], repo).stdout
    counts = _run(["git", "diff", "-z", "--no-renames", "--numstat", base, head], repo).stdout
    lines: dict[str, tuple[int, int]] = {}
    for row in filter(None, counts.split("\0")):
        added, removed, name = row.split("\t", 2)
        lines[name] = (int(added) if added != "-" else 0, int(removed) if removed != "-" else 0)
    fields = status.split("\0")
    existing, new = [], []
    for kind, name in zip(fields[0::2], fields[1::2]):
        added, removed = lines.get(name, (0, 0))
        if kind == "A":
            new.append({"file": name, "added": added})
        else:
            existing.append({"file": name, "added": added, "removed": removed})

    def in_package(rows: list[dict]) -> list[dict]:
        return [r for r in rows if r["file"].startswith(f"{package}/")]

    return {"package": _radius(in_package(existing), in_package(new)), "repo": _radius(existing, new)}


def _on_added(items: list[dict], added: dict[str, set[int]]) -> list[dict]:
    return [i for i in items if i["line"] in added.get(i["file"], set())]


def _measure(fn, *args):
    try:
        return fn(*args), None
    except ToolError as exc:
        return None, str(exc)


def _design_measures(solution: Path, package: str, diff: str, errors: dict[str, str]) -> dict:
    """Duplication on new code (gated) and module coupling (reported); tool errors go to `errors`."""
    out: dict = {}
    dup, err = _measure(duplication, solution, package, added_lines(diff, package, DUPLICATION_SUFFIXES))
    out["new_code_duplication"] = dup["new_code_duplication"] if dup else None
    out["duplication"] = dup
    if err:
        errors["duplication"] = err
    out["module_coupling"], err = _measure(module_coupling, solution, package, "python")
    if err:
        errors["module_coupling"] = err
    return out


def measure(solution: Path, baseline: Path, package: str) -> dict:
    diff = (solution / "CHANGE.diff").read_text(encoding="utf-8", errors="replace")
    added = added_lines(diff, package)
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

    result.update(_design_measures(solution, package, diff, errors))
    ncc = result.get("new_code_coverage")
    ndup = result["new_code_duplication"]
    result["gate"] = {
        "tests_pass": result.get("tests_failed") == 0 and (result.get("tests_passed") or 0) > 0,
        "new_code_coverage_at_least_80": ncc is not None and ncc >= THRESHOLDS["new_code_coverage"],
        "no_function_newly_over_cyclomatic_10": "cyclomatic" not in errors and not result["cyclomatic_newly_over_10"],
        "no_function_newly_over_cognitive_15": "cognitive" not in errors and not result["cognitive_newly_over_15"],
        "no_new_bug_findings": "lint" not in errors and result["bug_findings_new"] == 0,
        "no_new_type_errors": "types" not in errors and result["type_errors_new"] == 0,
        "new_code_duplication_at_most_3": ndup is not None and ndup <= THRESHOLDS["new_code_duplication"],
    }
    result["gate_passed"] = all(result["gate"].values())
    result["tool_errors"] = errors
    result["tools"] = {**TOOLS, "pytest": "pytest==9.1.1", "pytest-cov": "pytest-cov==7.1.0", "coverage": "coverage==7.16.2",
                       "jscpd": JSCPD, "node": NODE}
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tool-measured quality of one solution")
    parser.add_argument("solution", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("--package", default="ledgerlite")
    parser.add_argument("--follow-up", nargs=3, metavar=("REPO", "BASE", "HEAD"),
                        help="also report the edit radius of the follow-up change BASE..HEAD in REPO")
    args = parser.parse_args(argv)
    result = measure(args.solution.resolve(), args.baseline.resolve(), args.package)
    if args.follow_up:
        repo, base, head = args.follow_up
        result["edit_radius"], err = _measure(edit_radius, Path(repo).resolve(), base, head,
                                                  args.package)
        if err:
            result["tool_errors"]["edit_radius"] = err
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
