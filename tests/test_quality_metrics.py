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
