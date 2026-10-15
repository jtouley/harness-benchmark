"""grader.pyz as the runner uses it: copied into a fresh directory, run on a delivered repository.

The candidate's `make` runs while the grader is running, as the same user unless the runner drops
privileges (golden/pipeline/README.md, runner changes). So the key must never be a file the build can
find: the grader reads it from its own archive into memory.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

from pipetask import bundle
from test_pipeline_trial import _free_port, delivered, key  # noqa: F401 - key is a fixture


def test_grader_pyz_grades_from_a_clean_directory_and_never_puts_the_key_on_disk(key, tmp_path):  # noqa: F811
    dist = tmp_path / "dist"
    bundle.bundle(dist)
    probe, found = tmp_path / "probe", tmp_path / "found.txt"
    probe.mkdir()
    looks_for_the_key = f'find "{probe}" -name answer_key.json > "{found}"'
    port = _free_port()
    repo = delivered(tmp_path, key, port,
                     build=f"{looks_for_the_key} && mkdir -p out/marts && cp -R fixture/marts/. out/marts/")
    env = dict(os.environ, TMPDIR=str(probe))
    proc = subprocess.run([sys.executable, str(dist / "grader.pyz"), str(repo), "--port", str(port),
                           "--speed", "6000", "--durations", "1,1", "--logs", str(tmp_path / "logs")],
                          cwd=dist, env=env, capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, proc.stderr[-2000:]
    result = json.loads(proc.stdout)
    assert result["seed"] == key["stream"]["seed"] and result["reward"] == 1.0
    assert found.exists() and found.read_text() == ""  # the build ran and found no key
    assert list(probe.iterdir()) == []  # and the grader left no temporary directory behind


def test_grader_pyz_installs_the_pins_the_tests_run_with():
    pyproject = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    assert sorted(bundle.GRADER_DEPS) == sorted(pyproject["dependency-groups"]["pipeline"])
