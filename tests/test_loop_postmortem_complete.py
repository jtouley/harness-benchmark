"""Every run is documented the way the owner's postmortem documents it, as a property the loop enforces:
loop.driver writes the batch's postmortem and the scoreboard when it records a run, `loop.postmortem --all`
writes every committed postmortem again from its notes, and loop.check refuses a counted or cited run that
no committed postmortem holds, a postmortem that is not the generator's output, and a stale scoreboard."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from loop import check, driver, findings, postmortem, record, scoreboard

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
POSTMORTEMS = ROOT / "postmortems"
BASELINES = "2026-10-15-pipeline-trials"


def _copy_batch(dest: Path, batch: str) -> list[str]:
    ids = []
    for run in sorted(RUNS.iterdir()):
        if (run / "record.json").exists() and record.load(run)["batch"] == batch:
            shutil.copytree(run, dest / run.name)
            ids.append(run.name)
    return ids


def _no_findings(tmp_path: Path) -> Path:
    path = tmp_path / "findings.jsonl"
    path.write_text("")
    return path


# --- the check rule (written first: a counted run in no postmortem is a problem)

def test_a_counted_run_in_no_committed_postmortem_is_a_problem(tmp_path):
    runs, pms = tmp_path / "runs", tmp_path / "postmortems"
    ids = _copy_batch(runs, BASELINES)
    pms.mkdir()
    problems = check.postmortem_problems(runs, pms, _no_findings(tmp_path))
    counted = [i for i in ids if record.load(runs / i)["counts"]["counts"]]
    assert counted and len(problems) == len(counted)
    assert all(f"counted, and its batch {BASELINES} is in no committed postmortem" in p for p in problems)
    assert f"python -m loop.postmortem {BASELINES}" in problems[0]
    postmortem.refresh(BASELINES, runs, pms, _no_findings(tmp_path))
    assert (pms / f"{BASELINES}.md").exists()
    assert check.postmortem_problems(runs, pms, _no_findings(tmp_path)) == []


def test_a_run_cited_by_a_finding_needs_a_postmortem_even_when_it_does_not_count(tmp_path):
    runs, pms = tmp_path / "runs", tmp_path / "postmortems"
    _copy_batch(runs, "2026-10-21-cadence-core-subscription")
    pms.mkdir()
    cited = "20261021-P1-cadence-core-haiku-0-killed"  # not counted
    assert not record.load(runs / cited)["counts"]["counts"]
    path = tmp_path / "findings.jsonl"
    path.write_text(json.dumps({"id": "F-1", "title": "t", "run_ids": [cited], "root_cause": "r", "component": "cadence",
                                "gone_when": {"min_passed": 1}, "status": "open"}) + "\n")
    problems = check.postmortem_problems(runs, pms, path)
    assert any(p.startswith(f"{cited}: cited by a finding") for p in problems)


def test_a_postmortem_that_is_not_the_generators_output_is_a_problem(tmp_path):
    runs, pms = tmp_path / "runs", tmp_path / "postmortems"
    _copy_batch(runs, BASELINES)
    postmortem.refresh(BASELINES, runs, pms, _no_findings(tmp_path))
    text = (pms / f"{BASELINES}.md").read_text(encoding="utf-8")
    (pms / f"{BASELINES}.md").write_text(text.replace("## Summary", "## Summary\n\nedited by hand"), encoding="utf-8")
    problems = check.postmortem_problems(runs, pms, _no_findings(tmp_path))
    assert problems == [f"postmortems/{BASELINES}.md: not what the generator writes (python -m loop.postmortem --all)"]


def test_a_stale_scoreboard_is_a_problem(tmp_path):
    runs, pms = tmp_path / "runs", tmp_path / "postmortems"
    _copy_batch(runs, BASELINES)
    postmortem.refresh(BASELINES, runs, pms, _no_findings(tmp_path))
    board = tmp_path / "scoreboard.md"
    assert check.postmortem_problems(runs, pms, _no_findings(tmp_path), board) == [
        "scoreboard.md: not what the scoreboard writes (python -m loop.scoreboard --out scoreboard.md)"]
    board.write_text(scoreboard.table(runs), encoding="utf-8")
    assert check.postmortem_problems(runs, pms, _no_findings(tmp_path), board) == []


def test_a_notes_line_that_cites_a_run_of_another_batch_does_not_cover_that_run(tmp_path):
    """Coverage is by batch: a decision in one postmortem's notes that names a run of a batch with no
    postmortem of its own leaves that run undocumented, and the rule still says so."""
    runs, pms = tmp_path / "runs", tmp_path / "postmortems"
    other = "2026-10-21-cadence-core-subscription"
    ids = _copy_batch(runs, BASELINES) + _copy_batch(runs, other)
    counted_baselines = [i for i in ids if i.startswith("20261015") and record.load(runs / i)["counts"]["counts"]]
    pms.mkdir()
    (pms / f"{other}.notes.json").write_text(json.dumps(
        {"decisions": [{"text": "the baselines are these one-shots", "run_ids": counted_baselines}]}), encoding="utf-8")
    postmortem.refresh(other, runs, pms, _no_findings(tmp_path))
    text = (pms / f"{other}.md").read_text(encoding="utf-8")
    assert all(f"`{i}`" in text for i in counted_baselines)  # every baseline id is in the text, cited
    problems = check.postmortem_problems(runs, pms, _no_findings(tmp_path))
    assert len(problems) == len(counted_baselines)
    assert all(f"its batch {BASELINES} is in no committed postmortem" in p for p in problems)


def test_a_notes_file_that_names_a_batch_with_no_run_is_a_problem(tmp_path):
    runs, pms = tmp_path / "runs", tmp_path / "postmortems"
    _copy_batch(runs, BASELINES)
    pms.mkdir()
    (pms / "2026-10-30-nowhere.notes.json").write_text(json.dumps({"batches": [BASELINES, "2026-10-30-nowhere"]}), encoding="utf-8")
    (pms / "2026-10-30-nowhere.md").write_text("stale\n", encoding="utf-8")
    problems = check.postmortem_problems(runs, pms, _no_findings(tmp_path))
    assert any(p.startswith("postmortems/2026-10-30-nowhere.notes.json: names batch '2026-10-30-nowhere'") for p in problems)


# --- names, batches, --all

def test_a_postmortem_covers_the_batches_its_notes_list_else_its_own_name():
    covered = postmortem.covering(POSTMORTEMS)
    assert covered["2026-10-21-cadence-core-subscription"] == ["2026-10-21-cadence-core-subscription"]
    assert covered["2026-10-22-batch-0"] == ["2026-10-19-pipeline-cadence-core", "2026-10-21-cadence-core-subscription"]


def test_all_writes_every_committed_postmortem_again_from_its_notes(tmp_path):
    pms = tmp_path / "postmortems"
    shutil.copytree(POSTMORTEMS, pms)
    for path in pms.glob("*.md"):
        path.write_text("stale\n", encoding="utf-8")
    assert postmortem.main(["--all", "--postmortems", str(pms)]) == 0
    for path in POSTMORTEMS.glob("*.md"):
        assert (pms / path.name).read_text(encoding="utf-8") == path.read_text(encoding="utf-8"), path.name


def test_a_refresh_of_a_batch_rewrites_every_postmortem_that_covers_it(tmp_path):
    pms = tmp_path / "postmortems"
    shutil.copytree(POSTMORTEMS, pms)
    for path in pms.glob("*.md"):
        path.write_text("stale\n", encoding="utf-8")
    written = postmortem.refresh("2026-10-21-cadence-core-subscription", RUNS, pms)
    assert sorted(p.name for p in written) == ["2026-10-21-cadence-core-subscription.md", "2026-10-22-batch-0.md"]
    assert (pms / "2026-10-22-batch-0.md").read_text(encoding="utf-8") == (POSTMORTEMS / "2026-10-22-batch-0.md").read_text(encoding="utf-8")


# --- the driver

def test_the_driver_writes_the_batchs_postmortem_and_the_scoreboard_beside_the_records(tmp_path):
    (tmp_path / "store").mkdir()
    (tmp_path / "work").mkdir()
    argv = ["--run-id", "20261023-P1-baseline-haiku-1", "--kind", "stub", "--batch", "2026-10-23-stub",
            "--task", "P1", "--arm", "baseline", "--model", "claude-haiku-5-5", "--runs", str(tmp_path / "runs"),
            "--store", str(tmp_path / "store"), "--transcript", str(tmp_path / "t.jsonl"), "--cwd", str(tmp_path / "work"),
            "--", "true"]
    assert driver.main(argv) == 0
    text = (tmp_path / "postmortems" / "2026-10-23-stub.md").read_text(encoding="utf-8")
    assert text.startswith("# Postmortem: 2026-10-23-stub") and "`20261023-P1-baseline-haiku-1`" in text
    assert (tmp_path / "scoreboard.md").read_text(encoding="utf-8") == scoreboard.table(tmp_path / "runs")
    assert check.postmortem_problems(tmp_path / "runs", tmp_path / "postmortems", _no_findings(tmp_path),
                                     tmp_path / "scoreboard.md") == []


# --- the committed repository holds the property

def test_every_counted_or_cited_run_is_in_a_committed_postmortem_and_each_is_current():
    assert check.postmortem_problems(RUNS, POSTMORTEMS, findings.FINDINGS, ROOT / "scoreboard.md") == []
    assert check.main([]) == 0
