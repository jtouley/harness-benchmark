"""scripts/commit_replay.py: the same final code, reached in one commit or in reviewable steps."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("commit_replay", ROOT / "scripts" / "commit_replay.py")
cr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cr)

needs_uv = pytest.mark.skipif(shutil.which("uvx") is None, reason="needs uv to run the pinned radon")

BASE = "def total(xs):\n    return sum(xs)\n"
PARSE = '''
def parse(text):
    if not text:
        raise ValueError("empty")
    if text.startswith("-"):
        return -int(text[1:])
    if text.startswith("+"):
        return int(text[1:])
    return int(text)
'''
# A first, branchier version of label(), then the shape it is cleaned up to.
LABEL_DRAFT = '''
def label(n):
    if n < 0:
        return "negative"
    elif n == 0:
        return "zero"
    elif n < 10:
        return "small"
    elif n < 100:
        return "medium"
    elif n < 1000:
        return "large"
    elif n < 10000:
        return "huge"
    elif n < 100000:
        return "vast"
    elif n < 1000000:
        return "immense"
    elif n < 10000000:
        return "enormous"
    elif n < 100000000:
        return "gigantic"
    else:
        return "colossal"
'''
LABEL_FINAL = '''
BANDS = [(0, "zero"), (10, "small"), (100, "medium"), (1000, "large"), (10000, "huge"),
         (100000, "vast"), (1000000, "immense"), (10000000, "enormous")]


def label(n):
    if n < 0:
        return "negative"
    for limit, name in BANDS:
        if n <= limit if limit == 0 else n < limit:
            return name
    return "colossal"
'''
TEST = "python3 -c 'import app; assert app.parse(\"-3\") == -3'"


def _commit(repo: Path, text: str, message: str, when: int) -> None:
    (repo / "app.py").write_text(text)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    env = {"GIT_AUTHOR_DATE": f"@{when} +0000", "GIT_COMMITTER_DATE": f"@{when} +0000", "PATH": "/usr/bin:/bin"}
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", message],
                   check=True, env=env)


def _repo(tmp_path: Path, name: str, steps: list[tuple[str, str]]) -> Path:
    repo = tmp_path / name
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    # No background gc or maintenance: it writes into .git while a test deletes or copies it.
    for key, value in (("gc.auto", "0"), ("maintenance.auto", "false")):
        subprocess.run(["git", "-C", str(repo), "config", key, value], check=True)
    _commit(repo, BASE, "base", 1_000_000)
    for i, (text, message) in enumerate(steps, 1):
        _commit(repo, text, message, 1_000_000 + 60 * i)
    return repo


@needs_uv
def test_same_final_code_one_commit_against_steps(tmp_path):
    oneshot = _repo(tmp_path, "oneshot", [(BASE + PARSE + LABEL_FINAL, "feature")])
    harness = _repo(tmp_path, "harness", [
        (BASE + PARSE, "parse"),
        (BASE + PARSE + LABEL_DRAFT, "label"),
        ("BROKEN = (\n" + BASE + PARSE + LABEL_DRAFT, "wip"),
        (BASE + PARSE + LABEL_FINAL, "simplify label"),
    ])
    one = cr.replay(oneshot, "HEAD~1", "HEAD", test_cmd=TEST)["summary"]
    steps = cr.replay(harness, "HEAD~4", "HEAD", test_cmd=TEST)
    many = steps["summary"]

    assert one["final"] == many["final"]  # what ships is the same
    assert one["commits"] == 1 and many["commits"] == 4
    assert many["median_commit_lines"] < one["largest_commit_lines"]
    assert many["green_share"] == 0.75  # the wip commit does not parse
    assert many["cleanup_commits"] == 1
    # Drafting and cleaning up costs churn: more lines and complexity pass through review.
    assert many["total_lines_changed"] > one["total_lines_changed"]
    assert many["complexity_added_total"] > one["complexity_added_total"]
    assert many["seconds_base_to_head"] == 240
    assert many["unparsed_commits"] == 1 and steps["commits"][2]["unparsed"] == ["app.py"]
    assert steps["commits"][2]["complexity_added"] is None
    simplify = steps["commits"][-1]  # compared with "label", the last commit that parsed
    assert simplify["complexity_removed"] > simplify["complexity_added"]
    assert simplify["seconds_since_previous"] == 60


@needs_uv
def test_a_commit_that_takes_a_function_over_10_is_named(tmp_path):
    repo = _repo(tmp_path, "r", [(BASE + LABEL_DRAFT, "label")])
    row = cr.replay(repo, "HEAD~1", "HEAD")["commits"][0]
    assert row["newly_over_10"] == ["app.py:label=11"]
    assert row["green"] is None


@needs_uv
def test_no_commits_is_reported_not_scored_and_uncommitted_work_is_flagged(tmp_path):
    repo = _repo(tmp_path, "r", [])
    (repo / "app.py").write_text(BASE + PARSE)
    result = cr.replay(repo, "HEAD", "HEAD")
    assert result["summary"]["commits"] == 0 and result["summary"]["measurable"] is False
    assert result["uncommitted_changes"] is True


def test_complexity_delta_counts_new_and_deleted_functions():
    before = {("a.py", "f"): 3, ("a.py", "gone"): 4}
    after = {("a.py", "f"): 5, ("a.py", "new"): 12}
    delta = cr.complexity_delta(before, after)
    assert delta == {"complexity_added": 2 + 12, "complexity_removed": 4, "newly_over_10": ["a.py:new=12"]}


@needs_uv
def test_main_prints_json(tmp_path, capsys):
    repo = _repo(tmp_path, "r", [(BASE + PARSE, "parse")])
    assert cr.main([str(repo), "HEAD~1", "HEAD"]) == 0
    assert json.loads(capsys.readouterr().out)["summary"]["commits"] == 1


@needs_uv
def test_a_head_that_does_not_parse_has_no_final_state(tmp_path):
    repo = _repo(tmp_path, "r", [(BASE + PARSE, "parse"), ("BROKEN = (\n" + BASE + PARSE, "wip")])
    assert cr.replay(repo, "HEAD~2", "HEAD")["summary"]["final"] is None


def test_a_hanging_test_command_is_not_green(tmp_path):
    assert cr.green(tmp_path, "sleep 5", timeout=0.2) is False
