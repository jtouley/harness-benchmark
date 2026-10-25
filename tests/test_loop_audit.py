"""Auditability (loop/audit.py): each component is computed by code from the stored bundle and transcript."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from loop import audit, check, graded, record, store
from test_loop_record import _drive, plugin  # noqa: F401  (plugin is a fixture)

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "20261024-P1-cadence-haiku-core-9"
CWD = "/w/repo"


def _git(repo: Path, *args: str, author: str = "Claude") -> str:
    return subprocess.run(["git", "-c", f"user.name={author}", "-c", "user.email=a@b", *args], cwd=repo, check=True,
                          capture_output=True, text=True).stdout.strip()


def _bundle(tmp: Path, agent_files: dict[str, str] | None, graded_ref: bool) -> Path:
    """A repository with the starting commit and, when `agent_files`, one agent commit; bundled with every ref and,
    when `graded_ref`, refs/graded/<RUN_ID> at a snapshot commit (as loop.graded.bundle writes it)."""
    repo = tmp / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("skeleton\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "skeleton", author="harness-benchmark")
    for name, text in (agent_files or {}).items():
        (repo / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / name).write_text(text)
    if agent_files:
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "phase 1")
    if graded_ref:
        (repo / "uncommitted.py").write_text("x = 1\n")
        _git(repo, "add", "-A")
        snap = _git(repo, "commit-tree", _git(repo, "write-tree"), "-p", "HEAD", "-m", "snapshot", author="pipetask")
        _git(repo, "update-ref", graded.ref(RUN_ID), snap)
        _git(repo, "reset", "-q", "HEAD")
    out = tmp / "tree.bundle"
    _git(repo, "bundle", "create", "-q", str(out), "--all")
    return out


def _use(i: int, name: str, **args) -> dict:
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": f"t{i}", "name": name, "input": args}]}}


def _result(i: int, text: str, error: bool = False) -> dict:
    return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": f"t{i}", "content": text,
                                                     "is_error": error}]}}


CADENCE_EVENTS = [
    {"type": "system", "subtype": "init", "cwd": CWD},
    _use(1, "Write", file_path=f"{CWD}/.context/plans/spec.plan.md", content="# Plan\n\n## Assumptions\n\n- A-1: UTC.\n"),
    _result(1, "File created"),
    _use(2, "Bash", command="python3 $CADENCE_HOME/scripts/plan_create_gate.py --check"),
    _result(2, "OK  plan-create-gate\nexit=0"),
    _use(3, "Bash", command="python3 $CADENCE_HOME/scripts/test_benchmark_gate.py --code"),
    _result(3, "FAIL  test-benchmark-gate-code: mean 6.33 (floor 7)", error=True),
    _use(4, "Bash", command="git push -u origin HEAD && mkdir -p .context/prs && "
                            "cat > .context/prs/PR-1.md <<'EOF'\n# Phases 1 to 6\n\n## Summary\n\nThe batch lake.\nEOF"),
    _result(4, "pushed"),
]


def _store(tmp: Path, events: list[dict], agent_files, graded_ref: bool) -> tuple[dict, dict]:
    root = tmp / "store"
    transcript = tmp / "transcript.jsonl"
    transcript.write_text("".join(json.dumps(e) + "\n" for e in events))
    rec = {"run_id": RUN_ID, "transcript": store.put(transcript, root),
           "tree": store.put(_bundle(tmp, agent_files, graded_ref), root)}
    return rec, {store.STORE: root}


def test_a_cadence_run_that_did_everything_has_all_five(tmp_path):
    rec, roots = _store(tmp_path, CADENCE_EVENTS, {"DECISIONS.md": "# Decisions\n\n- Lake layout: one folder.\n"}, True)
    got = audit.compute(rec, roots)
    assert got["present"] == 5 and got["unread"] == 0
    comp = got["components"]
    assert comp["committed_history"]["commits"] == 1  # not the skeleton, not the graded snapshot
    assert comp["pr_description"]["local"] == [".context/prs/PR-1.md"]
    assert comp["decisions"]["committed"] == ["DECISIONS.md"]
    assert comp["decisions"]["written"] == [".context/plans/spec.plan.md"]
    assert comp["gate_evidence"] == {"present": True, "gates": ["plan-create-gate", "test-benchmark-gate-code"],
                                     "verdicts": 2, "pass": 1, "fail": 1}
    assert comp["regradable"]["ref"] == graded.ref(RUN_ID)


def test_a_one_shot_that_never_committed_has_only_what_it_wrote(tmp_path):
    events = [{"type": "system", "subtype": "init", "cwd": CWD},
              _use(1, "Write", file_path=f"{CWD}/DECISIONS.md", content="# Decisions\n\nMoney is exact.\n"),
              _result(1, "File created"),
              _use(2, "Bash", command="uv run pytest -q"), _result(2, "3 passed")]
    rec, roots = _store(tmp_path, events, None, False)
    got = audit.compute(rec, roots)
    comp = got["components"]
    assert [c for c in audit.COMPONENTS if comp[c]["present"]] == ["decisions"]
    assert comp["decisions"] == {"present": True, "committed": [], "written": ["DECISIONS.md"]}
    assert "only the starting repository" in comp["committed_history"]["why"]
    assert got["present"] == 1


@pytest.mark.parametrize("events", [
    # a title with no body
    [_use(1, "Write", file_path=f"{CWD}/.context/prs/PR-1.md", content="# Title only\n"), _result(1, "ok")],
    # a write that failed
    [_use(1, "Write", file_path=f"{CWD}/.context/prs/PR-1.md", content="# T\n\nBody.\n"), _result(1, "denied", True)],
    # gh pr create with no body, or with a body that returned no pull URL
    [_use(1, "Bash", command="gh pr create --fill"), _result(1, "https://github.com/o/r/pull/3")],
    [_use(1, "Bash", command="gh pr create --title T --body B"), _result(1, "gh: not logged in", True)],
])
def test_a_pr_needs_a_description_and_a_call_that_worked(tmp_path, events):
    rec, roots = _store(tmp_path, events, None, False)
    assert audit.compute(rec, roots)["components"]["pr_description"]["present"] is False


def test_a_hosted_pr_with_a_body_counts(tmp_path):
    events = [_use(1, "Bash", command="gh pr create --draft --title T --body-file .context/prs/body.md"),
              _result(1, "https://github.com/o/r/pull/12\n")]
    rec, roots = _store(tmp_path, events, None, False)
    assert audit.compute(rec, roots)["components"]["pr_description"]["hosted"] == ["https://github.com/o/r/pull/12"]


def test_a_gate_verdict_quoted_in_a_read_is_not_evidence(tmp_path):
    events = [_use(1, "Read", file_path="/p/references/gates.md"), _result(1, "OK  plan-create-gate\n")]
    rec, roots = _store(tmp_path, events, None, False)
    assert audit.compute(rec, roots)["components"]["gate_evidence"]["present"] is False


def test_heredocs_are_read_in_either_order_and_appended():
    cmd = ("cat > a.md <<'EOF'\n# A\nEOF\ncat <<EOF >> a.md\nmore\nEOF\n"
           "cat >> DECISIONS.md <<'X'\n## Phase 2\n- why\nX")
    assert audit.heredoc_writes(cmd) == [("a.md", "# A", False), ("a.md", "more", True),
                                         ("DECISIONS.md", "## Phase 2\n- why", True)]


def test_a_blob_in_another_store_is_unread_and_one_never_kept_is_absent(tmp_path):
    rec = {"run_id": RUN_ID, "transcript": {"sha256": "a" * 64, "bytes": 1, "path": "t.gz", "store": "git:o/other@1"},
           "tree": store.missing("--tree not given")}
    got = audit.compute(rec, {store.STORE: tmp_path})
    comp = got["components"]
    assert comp["pr_description"]["present"] is None and comp["gate_evidence"]["present"] is None
    assert comp["committed_history"]["present"] is False and comp["regradable"]["present"] is False
    assert got["unread"] == 3 and got["present"] == 0
    assert audit.score_text(got) == "0/5 (3 unread)"


def test_every_committed_record_has_its_audit():
    assert audit.problems(ROOT / "runs") == []


def test_check_refuses_a_missing_or_tampered_audit(tmp_path):
    run = tmp_path / RUN_ID
    run.mkdir()
    rec = {"run_id": RUN_ID, "transcript": store.missing("x"), "tree": store.missing("x")}
    (run / "record.json").write_text(json.dumps(rec))
    assert any("no audit.json" in p for p in audit.problems(tmp_path))
    got = audit.compute(rec, {})
    got["present"] = 4
    audit.write(run, got)
    assert any("does not match" in p for p in audit.problems(tmp_path))
    got = audit.compute(rec, {})
    got["inputs"]["tree"] = "b" * 64
    audit.write(run, got)
    assert any("inputs" in p for p in audit.problems(tmp_path))


@pytest.mark.skipif(not (ROOT.parent / "runs-store" / "blobs").is_dir(), reason="no runs-store checkout beside the "
                    "repository (git worktree add ../runs-store runs-store)")
def test_the_committed_audits_are_what_the_code_computes_from_the_store():
    roots = {store.STORE: ROOT.parent / "runs-store"}
    for run in sorted(p for p in (ROOT / "runs").iterdir() if (p / "record.json").is_file()):
        assert audit.load(run) == json.loads(audit.dump(audit.compute(record.load(run), roots))), run.name


def test_the_driver_writes_the_audit_with_the_record(tmp_path, plugin):  # noqa: F811
    rc, run = _drive(tmp_path, plugin)
    assert rc == 0
    got = audit.load(run)
    assert got is not None and got["inputs"]["transcript"] == record.load(run)["transcript"]["sha256"]
    assert audit.problems(tmp_path / "runs") == []
    assert check.validate_tree(tmp_path / "runs") == []
