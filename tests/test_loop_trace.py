"""The trace: per run, the findings that cite it and the cadence commits and pull requests that cite it
(loop/trace.py), and the postmortem's Trace section (loop/postmortem.py)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from loop import findings, postmortem, record, trace

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
CITED = "20261021-P2-cadence-core-haiku-2"      # cited by F-1, F-5, F-6 and by cadence commits
UNCITED = "20261015-P1-opus-1"                 # a counted one-shot, cited by nothing
NOT_COUNTED = "20261021-P1-cadence-core-haiku-0-killed"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
                          cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _commit(repo: Path, message: str) -> str:
    (repo / "f").write_text(message)
    _git(repo, "add", "f")
    _git(repo, "commit", "-qm", message)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def cadence(tmp_path) -> dict:
    """A cadence history: a squash-merged fix on main, a fix merged by a pull-request merge commit, a fix on
    an unmerged branch whose pull-request ref is fetched, and a commit whose evidence is not a run id."""
    repo = tmp_path / "cadence"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, "base")
    squash = _commit(repo, f"fix: a squash-merged fix (#5)\n\nFinding: F-1\nEvidence: {CITED}")
    _git(repo, "checkout", "-qb", "feat")
    merged = _commit(repo, f"fix: merged by a merge commit\n\nFinding: F-6\nEvidence: {CITED}\nEvidence: {UNCITED}")
    _git(repo, "checkout", "-q", "main")
    _git(repo, "merge", "--no-ff", "-q", "-m", "Merge pull request #7 from jtouley/feat", "feat")
    merge_sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "checkout", "-qb", "fix/open")
    unmerged = _commit(repo, f"fix: not merged yet\n\nFinding: F-3\nEvidence: {CITED}")
    _git(repo, "update-ref", "refs/remotes/origin/pr/9", unmerged)
    _git(repo, "checkout", "-qb", "other", "main")
    _commit(repo, "test: no run cited\n\nFinding: F-10\nEvidence: review of #202 at 8c78bbf")
    _git(repo, "checkout", "-qb", "fix/unfiled", "main")
    unfiled = _commit(repo, f"fix: a finding with no row yet\n\nFinding: F-99\nEvidence: {UNCITED}")
    _git(repo, "update-ref", "refs/remotes/origin/fix/unfiled", unfiled)
    _git(repo, "checkout", "-qb", "local-only", "main")
    _commit(repo, f"fix: on a local branch only, never walked\n\nFinding: F-1\nEvidence: {NOT_COUNTED}")
    _git(repo, "checkout", "-q", "main")
    return {"repo": repo, "squash": squash, "merged": merged, "merge_sha": merge_sha, "unmerged": unmerged,
            "unfiled": unfiled}


# --- trailers and the snapshot

def test_evidence_trailers_keep_run_ids_only():
    body = f"fix: x\n\nFinding: F-1\nEvidence: {CITED}\nEvidence: review of #202 at 8c78bbf\nEvidence:{UNCITED}\n"
    assert trace.evidence_trailers(body) == [CITED, UNCITED]
    assert trace.finding_trailers(body) == ["F-1"]
    assert trace.evidence_trailers("no trailer\n" + CITED) == []


@pytest.mark.parametrize(("subject", "number"), [
    ("Merge pull request #199 from jtouley/local-pr-adapter-none", 199),
    ("Contract test: the plugin tree holds no benchmark reference text (#204)", 204),
    ("fix: no pull request named", None),
])
def test_the_pull_request_number_comes_from_the_merge_subject(subject, number):
    assert trace.pr_number(subject) == number


def test_the_snapshot_names_each_citing_commit_its_status_and_no_text(cadence):
    snap = trace.snapshot(cadence["repo"], main="main")
    assert snap["schema"] == 1 and snap["main"] == _git(cadence["repo"], "rev-parse", "main")
    assert sorted(snap["citations"]) == [UNCITED, CITED]  # NOT_COUNTED is cited on a local branch only: not walked
    assert snap["refs"][0] == {"name": "main", "sha": snap["main"]}
    assert {r["name"] for r in snap["refs"]} == {"main", "origin/pr/9", "origin/fix/unfiled"}
    assert all(len(r["sha"]) == 40 for r in snap["refs"])
    by_sha = {c["sha"]: c for c in snap["citations"][CITED]}
    assert by_sha[cadence["squash"]] == {"sha": cadence["squash"], "findings": ["F-1"], "status": "merged", "pr": 5,
                                         "merge_sha": cadence["squash"]}
    assert by_sha[cadence["merged"]] == {"sha": cadence["merged"], "findings": ["F-6"], "status": "merged", "pr": 7,
                                         "merge_sha": cadence["merge_sha"]}
    assert by_sha[cadence["unmerged"]] == {"sha": cadence["unmerged"], "findings": ["F-3"], "status": "unmerged",
                                           "pr": 9, "branches": ["origin/pr/9"]}
    assert [c["sha"] for c in snap["citations"][UNCITED]] == [cadence["merged"], cadence["unfiled"]]
    assert snap["citations"][UNCITED][1]["findings"] == ["F-99"]  # kept, though no row files it yet
    text = json.dumps(snap)
    assert "squash-merged" not in text and "not merged yet" not in text  # shas and ids, no commit text


# --- the rows and the table

def test_the_rows_cover_counted_runs_and_every_cited_run(cadence):
    snap = trace.snapshot(cadence["repo"], main="main")
    rows = trace.rows(RUNS, findings.FINDINGS, snap)
    ids = [r["run_id"] for r in rows]
    assert ids == sorted(ids)
    counted = {p.name for p in RUNS.iterdir() if (p / "record.json").exists() and record.load(p)["counts"]["counts"]}
    assert counted <= set(ids)
    assert all(rid in ids for row in findings.load() for rid in row["run_ids"])
    assert NOT_COUNTED not in ids  # not counted and cited by nothing
    cited = next(r for r in rows if r["run_id"] == CITED)
    assert cited["findings"] == ["F-1", "F-5", "F-6", "F-7"] and cited["counts"] is True
    assert [c["status"] for c in cited["commits"]] == ["merged", "merged", "unmerged"]


def test_a_row_can_be_asked_for_one_run_and_an_unknown_run_is_refused():
    rows = trace.rows(RUNS, findings.FINDINGS, {"citations": {}}, run_ids=[NOT_COUNTED])
    assert [r["run_id"] for r in rows] == [NOT_COUNTED]
    assert rows[0]["findings"] == [] and rows[0]["commits"] == [] and rows[0]["counts"] is False
    with pytest.raises(trace.TraceError, match="no record"):
        trace.rows(RUNS, findings.FINDINGS, {"citations": {}}, run_ids=["20261020-P1-nowhere"])


def test_the_table_shows_findings_pull_requests_and_shas(cadence):
    snap = trace.snapshot(cadence["repo"], main="main")
    text = trace.table(trace.rows(RUNS, findings.FINDINGS, snap, run_ids=[CITED, UNCITED]))
    lines = text.splitlines()
    assert lines[0] == "| Run | Counts | Findings | Cadence commits (finding, pull request, status) |"
    row = next(line for line in lines if line.startswith(f"| `{CITED}`"))
    assert "| yes | F-1, F-5, F-6, F-7 |" in row
    assert f"`{cadence['squash'][:7]}` (F-1) merged in #5 at `{cadence['squash'][:7]}`" in row
    assert f"`{cadence['merged'][:7]}` (F-6) merged in #7 at `{cadence['merge_sha'][:7]}`" in row
    assert f"`{cadence['unmerged'][:7]}` (F-3) unmerged, #9 open or closed, on origin/pr/9" in row
    uncited = next(line for line in lines if line.startswith(f"| `{UNCITED}`"))
    assert "| yes | — |" in uncited and "(F-6) merged in #7" in uncited
    assert f"`{cadence['unfiled'][:7]}` (F-99 (unfiled)) unmerged, no pull request named, on origin/fix/unfiled" in uncited


def test_the_cli_prints_the_table_and_refreshes_the_snapshot(tmp_path, cadence):
    out = tmp_path / "citations.json"
    assert trace.main(["snapshot", "--cadence", str(cadence["repo"]), "--main", "main", "--citations", str(out)]) == 0
    assert json.loads(out.read_text())["citations"][CITED]
    assert trace.main(["--citations", str(out), "--run", CITED]) == 0
    assert trace.main(["--citations", str(out), "--run", "20261020-P1-nowhere"]) == 2


# --- the committed snapshot

def test_the_committed_snapshot_cites_only_runs_with_records_and_marks_unfiled_findings():
    snap = trace.load_citations(trace.CITATIONS)
    known = {row["id"] for row in findings.load()}
    assert snap["schema"] == 1 and snap["source"] == "jtouley/cadence" and len(snap["main"]) == 40
    assert snap["citations"]
    assert snap["refs"][0]["name"] == "origin/main" and snap["refs"][0]["sha"] == snap["main"]
    assert all(r["name"] == "origin/main" or r["name"].startswith("origin/") for r in snap["refs"])
    text = trace.table(trace.rows(RUNS, findings.FINDINGS, snap))
    for run_id, commits in snap["citations"].items():
        assert (RUNS / run_id / "record.json").exists(), run_id
        for c in commits:
            for f in c["findings"]:  # an id with no row is shown as unfiled, never asserted away
                assert (f"{f} (unfiled)" in text) == (f not in known), (run_id, f)
            assert c["status"] in ("merged", "unmerged")
            assert set(c) == ({"sha", "findings", "status", "pr", "merge_sha"} if c["status"] == "merged"
                              else {"sha", "findings", "status", "pr", "branches"})


def test_a_missing_snapshot_is_an_empty_one(tmp_path):
    assert trace.load_citations(tmp_path / "none.json") == {"citations": {}}


# --- the postmortem

def test_the_postmortem_has_a_trace_section_after_the_diagnosis():
    assert postmortem.SECTIONS.index("Trace") == postmortem.SECTIONS.index("Diagnosis") + 1
    text = postmortem.generate("2026-10-21-cadence-core-subscription", RUNS, {})
    section = text.split("## Trace", 1)[1].split("\n## ", 1)[0]
    row = next(line for line in section.splitlines() if line.startswith(f"| `{CITED}`"))
    assert "F-1, F-5, F-6" in row and "merged in #199" in row and "merged in #200" in row
    killed = next(line for line in section.splitlines() if line.startswith(f"| `{NOT_COUNTED}`"))
    assert "| no | — | — |" in killed


def test_the_postmortem_of_one_run_is_its_trace(capsys):
    assert postmortem.main(["--run", CITED]) == 0
    out = capsys.readouterr().out
    assert out.startswith("| Run |") and f"| `{CITED}` |" in out and "F-1, F-5, F-6" in out
    assert postmortem.main(["--run", "20261020-P1-nowhere"]) == 2
