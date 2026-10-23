"""P4 on the isolated runner path: grader-p4.pyz, and scripts/pipeline_trial.py behind --holdout."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import types
from pathlib import Path

import pytest

from pipetask import assemble, bundle
from scripts import pipeline_trial as pt

ROOT = Path(__file__).resolve().parents[1]
CAPS = json.loads((ROOT / "runner" / "pipeline" / "caps.json").read_text(encoding="utf-8"))
needs_uv = pytest.mark.skipif(not all(map(__import__("shutil").which, ("uv", "make"))), reason="needs uv and make")


@needs_uv
def test_grader_p4_pyz_grades_the_reference_from_a_clean_directory_and_never_puts_the_key_on_disk(tmp_path):
    dist = tmp_path / "dist"
    assert [p.name for p in bundle.bundle_holdout(dist)] == ["grader-p4.pyz"]
    probe, found = tmp_path / "probe", tmp_path / "found.txt"
    probe.mkdir()
    repo = assemble.assemble("P4", tmp_path / "repo", with_reference=True)
    makefile = repo / "Makefile"
    makefile.write_text(makefile.read_text(encoding="utf-8").replace(
        "build:\n", f'build:\n\tfind "{probe}" -name answer_key.json > "{found}"\n'), encoding="utf-8")
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "probe"], cwd=repo, check=True)
    proc = subprocess.run([sys.executable, str(dist / "grader-p4.pyz"), str(repo), "--logs", str(tmp_path / "logs")],
                          cwd=dist, env=dict(os.environ, TMPDIR=str(probe)), capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stderr[-2000:]
    result = json.loads(proc.stdout)
    assert result["task"] == "P4" and result["idempotent"] and result["passed"] == 7 and result["reward"] == 1.0
    assert found.exists() and found.read_text() == ""  # the build ran and found no key
    assert [p.name for p in probe.iterdir() if not p.name.startswith("uv-")] == []  # uv's own lock file aside


def _run(tmp_path, monkeypatch, task, holdout, caps=CAPS):
    def fake_assemble(t, dest, with_reference=False):
        dest.mkdir(parents=True)
        return dest
    built = []
    pipetask = types.ModuleType("pipetask")
    pipetask.assemble = types.SimpleNamespace(assemble=fake_assemble)
    pipetask.bundle = types.SimpleNamespace(bundle=lambda dist: built.append("bundle"),
                                            bundle_holdout=lambda dist: built.append("bundle_holdout"))
    monkeypatch.setitem(sys.modules, "pipetask", pipetask)
    calls = []
    monkeypatch.setattr(pt.subprocess, "call", lambda cmd, env=None: calls.append(cmd) or 0)
    out = tmp_path / "out"
    rc = pt.run_trial(task, out, mode="reference", model=None, plugin_dir=None, replay_seed=0, caps=caps, holdout=holdout)
    return rc, calls, built, json.loads((out / "trial.json").read_text())


def test_the_trial_script_refuses_p4_without_holdout_before_building_anything(tmp_path, monkeypatch):
    with pytest.raises(pt.HoldoutError, match="hold-out"):
        _run(tmp_path, monkeypatch, "P4", holdout=False)
    assert not (tmp_path / "out").exists()


def test_with_holdout_p4_runs_with_its_own_grader_and_no_replay(tmp_path, monkeypatch):
    rc, calls, built, meta = _run(tmp_path, monkeypatch, "P4", holdout=True)
    assert rc == 0 and built == ["bundle_holdout"]
    cmd = calls[0]
    assert cmd[cmd.index("--grader") + 1].endswith("grader-p4.pyz") and "--replay" not in cmd
    assert cmd[cmd.index("--prompt") + 1].endswith("golden/pipeline/P4/prompt.md")
    assert cmd[cmd.index("--image") + 1] == CAPS["tasks"]["P4"]["image"] == CAPS["tasks"]["P1"]["image"]
    assert "--deadline" not in cmd  # P4 is not measured yet, so caps.json gives it no grader_deadline
    assert meta["holdout"] is True and meta["task"] == "P4" and meta["replay_seed"] is None


def test_holdout_changes_nothing_for_the_other_tasks(tmp_path, monkeypatch):
    rc, calls, built, meta = _run(tmp_path, monkeypatch, "P1", holdout=True)
    assert rc == 0 and built == ["bundle"] and "--replay" in calls[0] and meta["holdout"] is False


def test_the_command_line_refuses_p4_without_holdout(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(pt, "run_trial", lambda *a, **kw: (_ for _ in ()).throw(pt.HoldoutError("P4 is the hold-out")))
    assert pt.main(["run", "P4", "--mode", "reference", "--out", str(tmp_path / "out")]) == 2
    assert "hold-out" in capsys.readouterr().err


def test_caps_name_p4_as_the_hold_out_and_the_image_build_warms_its_lock():
    note = CAPS["tasks"]["P4"]["note"]
    assert "hold-out" in note and "--holdout" in note and "reference" in note and "grader_deadline" not in CAPS["tasks"]["P4"]
    assert "P4" in (ROOT / "runner" / "pipeline" / "build.sh").read_text(encoding="utf-8")
    dockerfile = (ROOT / "runner" / "pipeline" / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY P4/skeleton /tmp/warm/P4" in dockerfile and "subset of P1's and P2's" in dockerfile


def test_p4_pins_are_a_subset_of_the_shared_images_locks():
    """The py image warms one uv cache for P1, P2 and P4. A package only P4 pins would sit in that cache and
    tell a P1 or P2 arm that another task exists, so P4's lock must add nothing to theirs."""
    def pins(task):
        lock = (ROOT / "golden" / "pipeline" / task / "skeleton" / "uv.lock").read_text(encoding="utf-8")
        return set(re.findall(r'^name = "([^"]+)"\nversion = "([^"]+)"', lock, re.M))
    assert pins("P4") <= pins("P1") | pins("P2"), pins("P4") - (pins("P1") | pins("P2"))
