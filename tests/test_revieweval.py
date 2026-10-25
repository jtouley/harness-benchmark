"""The review eval (revieweval/): its known answers, its prompts and the owner's comparison rule."""

from __future__ import annotations

import json
from pathlib import Path

from revieweval import compare

OWNER_REVIEW = ("do an antagonistic code review, verify things for yourself you'd be tempted to pass back to the "
                "author, anything we can offload in terms of effort for the author that can do ourselves, the better, "
                "save findings on findings-<pr-number>-<letter>.txt")


def test_every_case_has_a_grader_verified_answer() -> None:
    cases = compare.cases()
    assert len(cases) == 11 and len({c["name"] for c in cases}) == 11
    for c in cases:
        assert c["name"].startswith("review-") and c["run_id"] not in c["name"]
        ids = {a["id"] for a in c["answers"]}
        stream = "no-stream-trap-failure" if c["grader"]["stream_ok"] else "stream-consumer-does-not-survive-invalid-frame"
        assert stream in ids  # the grader's own stream_ok decides the stream answer
        assert all(a["verified_by"] for a in c["answers"])
    assert sum(not c["grader"]["stream_ok"] for c in cases) == 6
    pilot = [a for c in cases for a in c["answers"] if "pilot_id" in a]
    assert {a["pilot_id"] for a in pilot} == {"H1", "H2", "M1", "M2", "M3", "M4", "M5", "M6", "M7"}


def test_assertions_are_tagged_recall_or_control() -> None:
    for c in compare.cases():
        for text in compare.assertions(c):
            assert text.startswith(("[recall:", "[control:"))


def test_fenced_blocks_are_read_in_order() -> None:
    text = f"x\n```\n{OWNER_REVIEW}\n```\ny\n```\nsecond\n```\n"
    assert compare.fenced(text) == [OWNER_REVIEW, "second"]


def test_critical_path_overlaps_parallel_reviewers(tmp_path: Path) -> None:
    steps = [{"id": x, "after": []} for x in "ABC"] + [{"id": "consolidate", "after": ["A", "B", "C"]},
                                                      {"id": "explain", "after": ["consolidate"]}]
    (tmp_path / "steps.json").write_text(json.dumps({"steps": steps}))
    timing = {"A": 100_000, "B": 300_000, "C": 200_000, "consolidate": 50_000, "explain": 10_000}
    got = compare.critical_path(tmp_path, {k: {"duration_ms": v, "total_tokens": 10} for k, v in timing.items()})
    assert got == {"total_duration_seconds": 360.0, "total_tokens": 50}


def _summary(recalls: list[float], falses: list[float], secs: float, toks: float) -> dict:
    return {"recall": compare.stats(recalls), "false_findings": compare.stats(falses),
            "seconds_per_review": compare.stats([secs]), "tokens_per_review": compare.stats([toks])}


def test_better_only_by_more_than_the_variance_and_within_the_speed_slo() -> None:
    old = _summary([0.5, 0.5, 0.5], [1, 1, 1], 100, 1000)
    assert compare.verdict(_summary([0.9, 0.8, 0.85], [1, 1, 1], 120, 1200), old)["measurably_better"] is True
    noisy = compare.verdict(_summary([0.9, 0.3, 0.6], [1, 1, 1], 100, 1000), old)
    assert noisy["measurably_better"] is False and noisy["does_not_regress"] is True
    slow = compare.verdict(_summary([0.9, 0.9, 0.9], [1, 1, 1], 130, 1000), old)
    assert slow["measurably_better"] is False and slow["checks"]["time_within_speed_slo"] is False
    more_false = compare.verdict(_summary([0.9, 0.9, 0.9], [3, 3, 3], 100, 1000), old)
    assert more_false["checks"]["false_findings_not_worse_beyond_variance"] is False


def test_compare_reads_a_workspace(tmp_path: Path) -> None:
    root = tmp_path / "it"
    (root).mkdir()
    (root / "configs.json").write_text(json.dumps({"configs": {"new_skill": "x", "old_skill": "y"},
                                                   "baselines": ["old_skill"], "runs": 2}))
    case = root / "review-01"
    case.mkdir()
    (case / "eval_metadata.json").write_text("{}")
    for config, hits in (("new_skill", [True, True]), ("old_skill", [False, True])):
        for k, hit in enumerate(hits, 1):
            run = case / config / f"run-{k}"
            run.mkdir(parents=True)
            (run / "grading.json").write_text(json.dumps({"expectations": [
                {"text": "[recall:a] x", "passed": hit, "evidence": ""},
                {"text": "[control:b] y", "passed": True, "evidence": ""}], "claims": []}))
            (run / "timing.json").write_text(json.dumps({"total_duration_seconds": 10, "total_tokens": 5}))
    got = compare.compare(root)
    assert got["summary"]["new_skill"]["recall"]["mean"] == 1.0
    assert got["summary"]["old_skill"]["recall"]["mean"] == 0.5
    assert set(got["verdicts"]["new_skill"]) == {"old_skill"}


def _layout(work: Path, cadence: Path, *cases: str) -> list[str]:
    import argparse
    args = argparse.Namespace(work=work, iteration="it", cadence=cadence, config=["builtin=code-review"],
                              baseline=["builtin"], runs=1, cases=list(cases))
    compare.layout(args)
    return (work / "it" / "dispatch.jsonl").read_text().splitlines()


def test_subset_layout_never_replaces_a_run_list_and_setup_replaces_a_clone_without_base(tmp_path: Path) -> None:
    import subprocess
    import pytest
    names = [c["name"] for c in compare.cases()]
    for n in names[:2]:
        repo = tmp_path / "trees" / n / "repo"
        repo.mkdir(parents=True)
        g = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(g[:3] + ["init", "-q", "-b", "base"], check=True)
        subprocess.run(g + ["commit", "-q", "--allow-empty", "-m", "b"], check=True)
        subprocess.run(g + ["checkout", "-q", "-b", "review"], check=True)
        subprocess.run(g + ["commit", "-q", "--allow-empty", "-m", "r"], check=True)
    built = tmp_path / "built" / names[0]
    built.mkdir(parents=True)
    subprocess.run(["git", "clone", "-q", "-b", "review", str(tmp_path / "trees" / names[0] / "repo"),
                    str(built / "repo")], check=True)
    (built / "build.log").write_text("log\n")
    full = _layout(tmp_path, tmp_path)
    assert len(full) == 2 * len(names)
    with pytest.raises(SystemExit, match="exists"):
        _layout(tmp_path, tmp_path, names[0])
    with pytest.raises(SystemExit, match="unknown cases: review-1"):
        _layout(tmp_path, tmp_path, "review-1")
    assert (tmp_path / "it" / "dispatch.jsonl").read_text().splitlines() == full
    run = tmp_path / "it" / names[0] / "builtin" / "run-1"
    assert (run / "source").read_text().strip() == str(tmp_path / "trees" / names[0] / "repo")
    subprocess.run(["git", "clone", "-q", str(built / "repo"), str(run / "repo")], check=True)  # #130's clone
    compare.setup(run)
    out = subprocess.run(["git", "-C", str(run / "repo"), "branch"], capture_output=True, text=True).stdout
    assert "base" in out and "review" in out
