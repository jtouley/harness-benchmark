"""Records for the pipeline runs made before the driver existed, from the evidence committed for them.

    python -m loop.backfill [--runs runs]     # writes the records and scores that are not there yet

Every field comes from a file in git at a pinned commit (EVIDENCE), except the stop point and the
counting decision, which come from the round's write-up and are listed in RUNS with the section they
cite. Nothing here was self-graded: every score is the harness-benchmark grader's grade.json (or the
row the round's summary script built from it). What was not kept says so in the record (transcripts,
delivered trees, grader commits).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from loop import record, store
from loop.driver import transcript_facts

ROOT = Path(__file__).resolve().parents[1]

# Where each round's evidence is: (commit, folder). The Oct 19 and Oct 21 rounds are on unmerged branches.
OCT15 = ("ec54dbc928d4b7ebf10cbef94812b6ebc3ba8c9a", "docs/evidence/2026-10-15-pipeline-trials.json")
OCT19 = ("d4f9b00d9414b5686a4f462d5abb9bc10dd989fd", "docs/evidence/2026-10-19-pipeline-cadence-core")
OCT21 = ("d8b96111ecca4367ce42c1c0feb7c85b4e1f27a7", "docs/evidence/2026-10-21-pipeline-cadence-core-subscription")
WRITEUP = {
    "15": "docs/evidence/2026-10-15-pipeline-trials.md",
    "19": f"{OCT19[0][:7]}:docs/evidence/2026-10-19-pipeline-cadence-core.md",
    "21": f"{OCT21[0][:7]}:docs/evidence/2026-10-21-pipeline-cadence-core-subscription.md",
}
# The grader tree golden/pipeline/pipetask had from 7ad10ec (18 Oct 18:04 UTC) to ec54dbc (main before #49).
GRADER_TREE_OCT18 = "423b34ad3cd426bc35c0d820a10db2424966c8d3"
GRADER_COMMIT_OCT18 = "7ad10ec"
INFERRED = (f"inferred, not recorded: the round graded with the host's checkout of this repository, and "
            f"golden/pipeline/pipetask was at tree {GRADER_TREE_OCT18[:7]} in every commit from {GRADER_COMMIT_OCT18} "
            f"(18 Oct) to ec54dbc, the round's branch included; local edits to the checkout are not ruled out")
UNKNOWN15 = ("not recorded: the 15 October grades were made on the laptop before the grader commit was recorded; "
             "the regrades used the grader with the fixes the write-up lists")

# name in the round → (stop block, stop reason, counts, why). Each line cites its write-up section.
RUNS21 = {
    "P1-cadence-core-haiku-0-killed": ("E1", "infrastructure loss: the cloud container was reclaimed while idle", False,
                                       "infrastructure loss, not scored (21 Oct write-up, Results; criteria v2 §5.3)"),
    "P1-cadence-core-haiku-1": ("P4", "stopped to ask: the P4 handoff refused four times", True, "scored run (21 Oct, Results)"),
    "P1-cadence-core-haiku-2": ("P4", "retries hard stop: P4 drops the plan's RUN_BY_COMMAND marker", True,
                                "scored run (21 Oct, Results)"),
    "P1-cadence-core-haiku-3": ("E4", "credentials hard stop: no GitHub PR URL under adapter none", True,
                                "scored run (21 Oct, Results)"),
    "P2-cadence-core-haiku-1": ("P7", "retries hard stop: P7 failed three times", True, "scored run (21 Oct, Results)"),
    "P2-cadence-core-haiku-2": ("E4", "credentials hard stop: no GitHub PR URL under adapter none", True,
                                "scored run (21 Oct, Results)"),
    "P2-cadence-core-haiku-2a-killed": ("E1", "infrastructure loss: the worker restarted", False,
                                        "infrastructure loss, not scored (21 Oct write-up, Results; criteria v2 §5.3)"),
    "P2-cadence-core-haiku-3": ("P7", "retries hard stop: P7 failed three times after a replan from E1", True,
                                "scored run (21 Oct, Results)"),
}
RUNS19 = {
    "P1-cadence-core-1": ("P1", "the session ended while the plan-create peer ran in the background "
                          "(CLAUDE_AUTO_BACKGROUND_TASKS=true on the host)", False,
                          "a host defect ended it, not the arm (19 Oct, 'P1-cadence-core-1 (Opus, no delivery)')"),
    "P1-cadence-core-opus-2-interrupted": ("P1", "interrupted by the owner, who switched the arm to Haiku", False,
                                           "interrupted, not scored (19 Oct, Results)"),
    "P1-cadence-core-haiku-1": ("E4", "credentials hard stop: no GitHub remote and no PR number", True,
                                "scored run (19 Oct, 'P1-cadence-core-haiku-1')"),
    "P1-cadence-core-haiku-2": ("P9", "retries hard stop at the P9 entry invariant", True,
                                "scored run (19 Oct, 'P1-cadence-core-haiku-2 (hard stop at P9, no code)')"),
    "P1-cadence-core-haiku-3": ("R7", "completed every block; the answers were never published", True,
                                "scored run (19 Oct, 'P1-cadence-core-haiku-3')"),
    "P1-cadence-core-haiku-4": ("R1", "cut off by the operator's two-hour shell limit during the R1 fix round", False,
                                "cut off from outside: recorded, not scored (19 Oct, 'P1-cadence-core-haiku-4'; #48)"),
    "P2-cadence-core-haiku-1": ("E1", "cut off by the host's 7,200 s guard before phase 10", False,
                                "cut off from outside: recorded, not scored (19 Oct, 'P2-cadence-core-haiku-1')"),
}
CADENCE19 = "https://github.com/jtouley/cadence"
CADENCE21 = "https://github.com/jtouley/cadence-core"


def _show(commit: str, path: str) -> str | None:
    proc = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, capture_output=True, text=True)
    return proc.stdout if proc.returncode == 0 else None


def _json(commit: str, path: str):
    text = _show(commit, path)
    return json.loads(text) if text else None


def available() -> bool:
    return all(subprocess.run(["git", "cat-file", "-e", f"{c}^{{commit}}"], cwd=ROOT, capture_output=True).returncode == 0
               for c, _ in (OCT15, OCT19, OCT21))


def _base(run_id, batch, evidence, task, arm, model, cadence, **over) -> dict:
    rec = {
        "schema": 1, "run_id": run_id, "kind": "benchmark", "batch": batch,
        "provenance": {"source": "backfill", "evidence": evidence}, "task": task, "request_id": None, "arm": arm,
        "cadence": cadence, "model_requested": model, "models_served": None, "session_id": None,
        "claude_version": None, "command": None, "started_at": None, "ended_at": None, "exit_code": None,
        "cost": {"list_usd": None, "reported_usd": None}, "stop_point": {"block": None, "reason": None},
        "transcript": store.missing("not kept in git or in the store"),
        "tree": store.missing("not kept in git or in the store"),
        "counts": {"counts": False, "why": ""},
    }
    rec.update(over)
    return rec


def _score(run_id, grade: dict, grader: dict, note: str | None = None) -> dict:
    checks = grade.get("checks")
    passed, total = grade.get("passed"), grade.get("total")
    if isinstance(checks, str) and "/" in checks:  # a summary row: "3/7"
        passed, total = (int(x) for x in checks.split("/"))
    s = {"run_id": run_id, "grader": grader, "reward": float(grade.get("reward") or 0.0), "passed": passed,
         "total": total, "idempotent": grade.get("idempotent"), "stream_ok": grade.get("stream_ok"),
         "error": grade.get("error"), "source": "backfill", "graded_at": None}
    if note:
        s["note"] = note
    return s


def oct15() -> list[tuple[dict, list[dict]]]:
    rows = _json(*OCT15)
    by_run = {r["run"]: r for r in rows}
    grader = {"repo": "jtouley/harness-benchmark", "commit": None, "tree": None, "basis": UNKNOWN15}
    out = []
    for r in rows:
        if r["mode"] != "agent" or r["run"].endswith("-regrade"):
            continue
        name = r["run"]
        run_id = f"20261015-{name}"
        evidence = [f"{OCT15[0][:7]}:{OCT15[1]}#{name}", WRITEUP["15"]]
        regrade = by_run.get(f"{name}-regrade")
        if r.get("void"):
            counts = {"counts": False, "why": f"void: {r['void']}"}
        elif regrade:
            counts = {"counts": True, "why": "scored by its counted regrade (15 Oct write-up)"}
        else:
            counts = {"counts": bool(r["counted"]), "why": "scored run (15 Oct write-up)" if r["counted"]
                      else "not counted in the 15 Oct summary"}
        note = None
        if name == "P2-haiku-1":
            note = ("P2-haiku-1-flatmap-regrade (3/7) is a diagnostic regrade of an edited map, not a grade "
                    "of the delivered run, so it is not a score here")
        rec = _base(run_id, "2026-10-15-pipeline-trials", evidence, r["task"], "baseline", r["model"], None,
                    cost={"list_usd": r["cost_usd"], "reported_usd": None, "tokens": r["tokens"]},
                    exit_code=r.get("agent_exit"), counts=counts,
                    transcript=store.missing("kept outside git on the operator's laptop (results/runs/, gitignored); "
                                             "no sha256 was recorded"),
                    tree=store.missing("the saved tree is on the operator's laptop (results/runs/, gitignored)"))
        if note:
            rec["provenance"]["note"] = note
        scores = []
        if r["outcome"] == "graded":
            scores.append(_score(run_id, r, grader, "first grade, before the grader fixes" if regrade else None))
        if regrade:
            scores.append(_score(run_id, regrade, grader, "counted regrade with the fixed grader"))
        out.append((rec, scores))
    return out


def _cadence(repo: str, sha: str | None, branch: str | None) -> dict | None:
    if not sha:
        return None
    c = {"repo": repo, "sha": sha, "tree_clean": None}
    if branch:
        c["published_in"] = [f"origin/{branch}"]
    return c


def _facts(commit: str, folder: str) -> dict:
    text = _show(commit, f"{folder}/result.json")
    if not text:
        return {}
    try:  # one result object (some rounds saved it pretty-printed, without its "type")
        lines = [json.dumps({"type": "result", **json.loads(text)})]
    except ValueError:  # result lines, one per wake-up
        lines = text.splitlines()
    facts = transcript_facts(lines)
    return {k: v for k, v in facts.items() if v is not None}


def oct19() -> list[tuple[dict, list[dict]]]:
    commit, folder = OCT19
    grader = {"repo": "jtouley/harness-benchmark", "commit": GRADER_COMMIT_OCT18, "tree": GRADER_TREE_OCT18,
              "basis": INFERRED}
    out = []
    for name, (block, reason, counts, why) in RUNS19.items():
        d = f"{folder}/{name}"
        prov = _json(commit, f"{d}/provenance.json") or {}
        run_id = f"20261019-{name}"
        facts = _facts(commit, d)
        cost = _json(commit, f"{d}/cost.json")
        rec = _base(run_id, "2026-10-19-pipeline-cadence-core", [f"{commit[:7]}:{d}", WRITEUP["19"]], "P2" if
                    name.startswith("P2") else "P1", "cadence-core", prov.get("model"),
                    _cadence(CADENCE19, prov.get("cadence_sha"), prov.get("cadence_branch") or "ccr-3d2e0c73-lr6bdt"),
                    request_id="gh-1", claude_version=prov.get("claude_version"),
                    stop_point={"block": block, "reason": reason}, counts={"counts": counts, "why": why},
                    transcript=store.missing("not committed (19 Oct write-up, amended per #55)"),
                    tree=store.missing("not kept; the host container is gone"))
        rec.update({k: v for k, v in facts.items() if k in ("models_served", "session_id")})
        rec["cost"] = facts.get("cost", rec["cost"])
        if cost:
            rec["cost"]["list_usd"] = cost["usd_total"]
            rec["cost"]["reported_usd"] = cost.get("host_reported_usd")
        grade = _json(commit, f"{d}/grade.json")
        scores = [_score(run_id, grade, grader, None if counts else "what the grader read of the tree the run left; "
                         "the run is not scored")] if grade else []
        out.append((rec, scores))
    return out


def _log_times(log: str | None) -> tuple[str | None, str | None]:
    stamps = [line.split(" ", 1)[0] for line in (log or "").splitlines() if line[:4].isdigit()]
    return (stamps[0], stamps[-1]) if stamps else (None, None)


def oct21() -> list[tuple[dict, list[dict]]]:
    commit, folder = OCT21
    rows = {r["run"]: r for r in _json(commit, f"{folder}/rows.json")}
    grader = {"repo": "jtouley/harness-benchmark", "commit": GRADER_COMMIT_OCT18, "tree": GRADER_TREE_OCT18,
              "basis": INFERRED}
    out = []
    for name, (block, reason, counts, why) in RUNS21.items():
        d = f"{folder}/{name}"
        prov = _json(commit, f"{d}/provenance.json") or {}
        trial = _json(commit, f"{d}/trial.json") or {}
        started = trial.get("started_at")
        _, ended = _log_times(_show(commit, f"{d}/driver.log"))
        run_id = f"{started[:10].replace('-', '')}-{name}"
        row = rows[name]
        facts = _facts(commit, d)
        rec = _base(run_id, "2026-10-21-cadence-core-subscription", [f"{commit[:7]}:{d}", WRITEUP["21"]], row["task"],
                    "cadence-core", prov.get("model"), _cadence(CADENCE21, prov.get("cadence_sha"), None),
                    request_id="gh-1", claude_version=prov.get("claude_version"),
                    command=[f"{folder}/host_trial.sh", row["task"], name], started_at=started, ended_at=ended,
                    exit_code=row.get("agent_exit"), stop_point={"block": block, "reason": reason},
                    counts={"counts": counts, "why": why},
                    transcript=store.missing("not committed (5 to 9 MB each, host paths); the host container is gone"),
                    tree=store.missing("not committed; the host container is gone"))
        rec["provenance"]["note"] = ("plugin tree: cadence-core at the commit above via --plugin-dir; whether the "
                                     "tree was clean was not recorded, and peers also read a second copy at "
                                     "/home/user/cadence-core (same commit) (21 Oct, Findings 5)")
        rec.update({k: v for k, v in facts.items() if k in ("models_served", "session_id")})
        rec["cost"] = {"list_usd": row["cost_usd"] if row["outcome"] != "infra_error" else None,
                       "reported_usd": row.get("host_cost_usd"), **({"tokens": row["tokens"]} if counts else {})}
        grade = _json(commit, f"{d}/grade.json")
        out.append((rec, [_score(run_id, grade, grader)] if grade else []))
    return out


def build() -> list[tuple[dict, list[dict]]]:
    return oct15() + oct19() + oct21()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.backfill", description=__doc__.split("\n\n")[0])
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    args = ap.parse_args(argv)
    if not available():
        print("the evidence commits are not here: git fetch origin ccr-3d2e0c73-lr6bdt ccr-35b43d50-uw8iyb",
              file=sys.stderr)
        return 2
    written = 0
    for rec, scores in build():
        if (args.runs / rec["run_id"] / "record.json").exists():
            continue
        record.write_record(args.runs, rec)
        for s in scores:
            record.append_score(args.runs, s)
        written += 1
    print(f"{written} record(s) written to {args.runs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
