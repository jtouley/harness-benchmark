"""scripts/quality_metrics.py: what counts as new, duplication, coupling and edit radius."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("quality_metrics", ROOT / "scripts" / "quality_metrics.py")
qm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qm)

DIFF = """diff --git a/ledgerlite/cli.py b/ledgerlite/cli.py
--- a/ledgerlite/cli.py
+++ b/ledgerlite/cli.py
@@ -10,3 +10,5 @@ def run():
     a = 1
+    b = 2
+    c = 3
     d = 4
-    e = 5
diff --git a/tests/test_x.py b/tests/test_x.py
--- /dev/null
+++ b/tests/test_x.py
@@ -0,0 +1,1 @@
+def test_x(): pass
"""


def test_added_lines_are_read_for_package_files_only():
    assert qm.added_lines(DIFF, "ledgerlite") == {"ledgerlite/cli.py": {11, 12}}


def test_only_findings_on_added_lines_count():
    added = {"ledgerlite/cli.py": {11, 12}}
    findings = [{"file": "ledgerlite/cli.py", "line": 11}, {"file": "ledgerlite/cli.py", "line": 13},
                {"file": "ledgerlite/models.py", "line": 11}]
    assert qm._on_added(findings, added) == [{"file": "ledgerlite/cli.py", "line": 11}]


def test_a_failing_tool_raises_instead_of_reading_as_no_findings(tmp_path):
    try:
        qm._run(["python3", "-c", "import sys; sys.exit(2)"], tmp_path, ok=(0, 1))
    except qm.ToolError:
        return
    raise AssertionError("exit code 2 must raise ToolError")


def test_output_that_is_not_json_raises():
    try:
        qm._json("not json", "ruff")
    except qm.ToolError:
        return
    raise AssertionError("bad JSON must raise ToolError")


def test_a_no_newline_marker_does_not_shift_added_lines():
    """N4 on PR #8: the marker was counted as a context line."""
    diff = ("--- a/ledgerlite/x.py\n+++ b/ledgerlite/x.py\n@@ -1,2 +1,3 @@\n a = 1\n-b = 2\n"
            "\\ No newline at end of file\n+b = 2\n+c = 3\n")
    assert qm.added_lines(diff, "ledgerlite") == {"ledgerlite/x.py": {2, 3}}


def test_one_complexity_rule_flags_a_function_only_when_the_change_takes_it_over_the_threshold():
    """R4 on PR #8: cyclomatic flagged any changed function over 10, cognitive only a newly-over one."""
    before = [{"file": "p/a.py", "name": "run", "value": 7}, {"file": "p/a.py", "name": "old", "value": 12}]
    after = [{"file": "p/a.py", "name": "run", "value": 11}, {"file": "p/a.py", "name": "old", "value": 14},
             {"file": "p/b.py", "name": "new", "value": 16}, {"file": "p/b.py", "name": "small", "value": 3}]
    assert qm.newly_over(after, before, 10) == ["p/a.py:run=11", "p/b.py:new=16"]


def test_new_code_coverage_counts_executable_added_lines_only():
    data = {"files": {"p/a.py": {"executed_lines": [1, 2, 5], "missing_lines": [3]}}}
    assert qm.new_line_coverage(data, {"p/a.py": {2, 3, 4}}) == (1, 2)


def test_only_likely_bugs_count_as_bug_findings():
    """N1 on PR #8: unused imports and f-strings without placeholders are smells, not bugs."""
    assert [c for c in ("F401", "F541", "F841", "F821", "F811", "F632", "F701", "E999", "B006", "PLE0101")
            if qm.is_bug(c)] == ["F821", "F811", "F632", "F701", "E999", "B006", "PLE0101"]


def test_the_committed_gate_results_record_the_reference_calibration():
    """R3 on PR #8: a gate result means little unless the task author's own solution is measured too."""
    import json
    data = json.loads((ROOT / "docs/experiments/2026-10-12-iteration-4/quality_metrics.json").read_text())
    for task in ("multicurrency", "budgets", "audit-undo"):
        assert "gate_passed" in data[f"{task}/reference"]
    assert all("cyclomatic_newly_over_10" in row for row in data.values())


# --- Duplication on new code (jscpd) --------------------------------------------------

SQL_YAML_DIFF = """diff --git a/ledgerlite/q.sql b/ledgerlite/q.sql
--- /dev/null
+++ b/ledgerlite/q.sql
@@ -0,0 +1,2 @@
+select 1
+from t
diff --git a/ledgerlite/c.yaml b/ledgerlite/c.yaml
--- /dev/null
+++ b/ledgerlite/c.yaml
@@ -0,0 +1,1 @@
+a: 1
"""


def test_added_lines_read_other_languages_when_asked():
    assert qm.added_lines(SQL_YAML_DIFF, "ledgerlite") == {}
    assert qm.added_lines(SQL_YAML_DIFF, "ledgerlite", qm.DUPLICATION_SUFFIXES) == {
        "ledgerlite/q.sql": {1, 2}, "ledgerlite/c.yaml": {1}}


def test_both_sides_of_a_clone_count_as_duplicated_lines():
    report = {"duplicates": [{"firstFile": {"name": "a.py", "start": 1, "end": 5},
                              "secondFile": {"name": "sub/b.py", "start": 10, "end": 14}}]}
    assert qm.duplicated_lines(report, "ledgerlite") == {
        "ledgerlite/a.py": {1, 2, 3, 4, 5}, "ledgerlite/sub/b.py": {10, 11, 12, 13, 14}}


def test_new_code_duplication_is_the_share_of_added_lines_inside_a_clone():
    added = {"ledgerlite/b.py": set(range(1, 21)), "ledgerlite/c.py": set(range(1, 21))}
    dup = {"ledgerlite/b.py": set(range(1, 7)), "ledgerlite/a.py": set(range(1, 100))}
    assert qm.new_code_duplication(dup, added) == {"new_duplicated_lines": 6, "new_lines": 40,
                                                   "new_code_duplication": 15.0}


def test_no_added_lines_measure_as_no_duplication():
    assert qm.new_code_duplication({"ledgerlite/a.py": {1}}, {})["new_code_duplication"] == 0.0


def _write(root, files: dict[str, str]):
    for name, text in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)


BLOCK = "".join(f"    total = total + values[{i}] * {i}\n" for i in range(8))


@pytest.mark.skipif(shutil.which("uvx") is None, reason="needs uv to run the pinned jscpd")
def test_jscpd_finds_a_copied_function_in_new_code(tmp_path):
    _write(tmp_path, {"pkg/a.py": f"def f(values):\n    total = 0\n{BLOCK}    return total\n",
                      "pkg/b.py": f"def g(values):\n    total = 0\n{BLOCK}    return total\n"})
    added = {"pkg/b.py": set(range(1, 12))}
    found = qm.duplication(tmp_path, "pkg", added)
    assert found["new_code_duplication"] == 100.0
    assert found["duplicated_lines_total"] > 0


@pytest.mark.skipif(shutil.which("uvx") is None, reason="needs uv to run the pinned jscpd")
def test_jscpd_ignores_a_config_that_the_measured_solution_ships(tmp_path):
    ignore_all = '{"ignore": ["**/*"], "minLines": 500}'
    _write(tmp_path, {"pkg/a.py": f"def f(values):\n    total = 0\n{BLOCK}    return total\n",
                      "pkg/b.py": f"def g(values):\n    total = 0\n{BLOCK}    return total\n",
                      ".jscpd.json": ignore_all, "pkg/.jscpd.json": ignore_all,
                      "package.json": f'{{"name": "x", "jscpd": {ignore_all}}}',
                      ".gitignore": "pkg/\n"})
    _git(tmp_path, "init", "-q")
    found = qm.duplication(tmp_path, "pkg", {"pkg/b.py": set(range(1, 12))})
    assert found["new_code_duplication"] == 100.0


@pytest.mark.skipif(shutil.which("uvx") is None, reason="needs uv to run the pinned jscpd")
def test_jscpd_on_a_missing_package_raises(tmp_path):
    with pytest.raises(qm.ToolError):
        qm.duplication(tmp_path, "nope", {})


# --- Module coupling (Martin 2002) ----------------------------------------------------


def test_python_import_graph_resolves_absolute_and_relative_imports(tmp_path):
    _write(tmp_path, {"pkg/__init__.py": "",
                      "pkg/a.py": "import os\nimport pkg.b\n",
                      "pkg/b.py": "from . import c\nfrom .sub import d\n",
                      "pkg/c.py": "from pkg.sub.d import X\n",
                      "pkg/sub/__init__.py": "",
                      "pkg/sub/d.py": "from .. import a as _a\nX = 1\n"})
    assert qm.python_import_graph(tmp_path, "pkg") == {
        "pkg": set(), "pkg.a": {"pkg.b"}, "pkg.b": {"pkg.c", "pkg.sub.d"},
        "pkg.c": {"pkg.sub.d"}, "pkg.sub": set(), "pkg.sub.d": {"pkg.a"}}


def test_coupling_counts_afferent_efferent_and_instability():
    graph = {"a": {"b"}, "b": {"c"}, "c": set(), "lone": set()}
    assert qm.coupling(graph) == {
        "a": {"afferent": 0, "efferent": 1, "instability": 1.0},
        "b": {"afferent": 1, "efferent": 1, "instability": 0.5},
        "c": {"afferent": 1, "efferent": 0, "instability": 0.0},
        "lone": {"afferent": 0, "efferent": 0, "instability": None}}


def test_module_coupling_dispatches_by_language(tmp_path):
    _write(tmp_path, {"pkg/__init__.py": "", "pkg/a.py": "from pkg import b\n", "pkg/b.py": ""})
    assert qm.module_coupling(tmp_path, "pkg", "python")["pkg.b"]["afferent"] == 1
    with pytest.raises(qm.ToolError):
        qm.module_coupling(tmp_path, "pkg", "sql")


def test_a_module_that_does_not_parse_raises(tmp_path):
    _write(tmp_path, {"pkg/a.py": "def (:\n"})
    with pytest.raises(qm.ToolError):
        qm.python_import_graph(tmp_path, "pkg")


# --- Edit radius ----------------------------------------------------------------------


def _git(repo, *args) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo,
                          capture_output=True, text=True, check=True).stdout.strip()


def _follow_up(repo, before: dict[str, str], after: dict[str, str], removed: tuple[str, ...] = ()) -> str:
    """Commit `before`, then a follow-up commit with `after` and `removed`; return the base sha."""
    _git(repo, "init", "-q")
    _write(repo, before)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")
    _write(repo, after)
    for name in removed:
        (repo / name).unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "follow-up")
    return base


def test_edit_radius_separates_existing_files_from_new_ones_in_the_package_and_the_repo(tmp_path):
    base = _follow_up(tmp_path,
                      {"pkg/a.py": "one\ntwo\nthree\n", "pkg/b.py": "gone\n", "pkg/keep.py": "same\n",
                       "tests/test_a.py": "x\n", "README.md": "r\n"},
                      {"pkg/a.py": "one\nTWO\nthree\nfour\n", "pkg/c.py": "new\nfile\n",
                       "tests/test_a.py": "y\n", "docs/plan.md": "p\n"},
                      removed=("pkg/b.py",))
    radius = qm.edit_radius(tmp_path, base, "HEAD", "pkg")
    assert radius["package"] == {
        "existing_files_changed": 2,
        "existing_lines_changed": 4,
        "existing": [{"file": "pkg/a.py", "added": 2, "removed": 1}, {"file": "pkg/b.py", "added": 0, "removed": 1}],
        "new_files": [{"file": "pkg/c.py", "added": 2}],
    }
    assert radius["repo"]["existing_files_changed"] == 3
    assert radius["repo"]["existing_lines_changed"] == 6
    assert [n["file"] for n in radius["repo"]["new_files"]] == ["docs/plan.md", "pkg/c.py"]


def test_edit_radius_reports_unusual_file_names_unquoted(tmp_path):
    name = "pkg/caf\u00e9 \t\"q\".py"
    base = _follow_up(tmp_path, {name: "a\n"}, {name: "b\n"})
    assert qm.edit_radius(tmp_path, base, "HEAD", "pkg")["package"]["existing"] == [
        {"file": name, "added": 1, "removed": 1}]


def test_edit_radius_on_an_unknown_commit_raises(tmp_path):
    _git(tmp_path, "init", "-q")
    with pytest.raises(qm.ToolError):
        qm.edit_radius(tmp_path, "deadbeef", "HEAD", "pkg")


# --- Wiring through measure() and main() ----------------------------------------------


def _fail(*_args):
    raise qm.ToolError("tool down")


@pytest.fixture
def passing_tools(monkeypatch, tmp_path):
    """Every tool stubbed to a passing result; the solution holds an empty CHANGE.diff."""
    monkeypatch.setattr(qm, "coverage", lambda *_: {"tests_passed": 1, "tests_failed": 0, "new_code_coverage": 100.0})
    for name in ("cyclomatic", "cognitive", "lint", "type_errors"):
        monkeypatch.setattr(qm, name, lambda *_: [])
    monkeypatch.setattr(qm, "maintainability", lambda *_: 100.0)
    monkeypatch.setattr(qm, "duplication", lambda *_: {"new_code_duplication": 0.0})
    monkeypatch.setattr(qm, "module_coupling", lambda *_: {})
    (tmp_path / "CHANGE.diff").write_text("")
    return tmp_path


@pytest.mark.parametrize(("tool", "gate", "error_key"), [
    ("duplication", "new_code_duplication_at_most_3", "duplication"),
    ("module_coupling", None, "module_coupling"),
])
def test_a_design_tool_error_is_recorded_and_fails_its_gate(passing_tools, monkeypatch, tool, gate, error_key):
    assert qm.measure(passing_tools, passing_tools, "pkg")["gate_passed"] is True
    monkeypatch.setattr(qm, tool, _fail)
    result = qm.measure(passing_tools, passing_tools, "pkg")
    assert result["tool_errors"] == {error_key: "tool down"}
    if gate:
        assert result["gate"][gate] is False
        assert result["gate_passed"] is False


def test_follow_up_reports_the_edit_radius_and_routes_its_errors(monkeypatch, capsys, tmp_path):
    calls = []
    monkeypatch.setattr(qm, "measure", lambda *_: {"tool_errors": {}})
    monkeypatch.setattr(qm, "edit_radius", lambda *args: calls.append(args) or {"repo": {}})
    argv = [str(tmp_path), str(tmp_path), "--package", "pkg", "--follow-up", str(tmp_path), "b", "h"]
    assert qm.main(argv) == 0
    assert json.loads(capsys.readouterr().out)["edit_radius"] == {"repo": {}}
    assert calls == [(tmp_path.resolve(), "b", "h", "pkg")]

    monkeypatch.setattr(qm, "edit_radius", _fail)
    qm.main(argv)
    out = json.loads(capsys.readouterr().out)
    assert out["edit_radius"] is None
    assert out["tool_errors"] == {"edit_radius": "tool down"}
