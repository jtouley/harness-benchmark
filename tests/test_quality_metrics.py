"""scripts/quality_metrics.py: the pure parts that decide what counts as new."""

from __future__ import annotations

import importlib.util
from pathlib import Path

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
