"""The scoreboard: score per cadence commit over time, per task and model, next to the one-shot baselines.
The release gate reads it.

    python -m loop.scoreboard [--out scoreboard.md]
    python -m loop.scoreboard gate --model claude-haiku-5-5 --sha <cadence sha> [--n 3]

A cell takes the counted runs of one (arm, cadence commit, model, task) that have a score, and each run's
latest score. A bar is the best counted one-shot run (arm `baseline` or `one-shot`) of the same task and model
in the newest batch that has one, on the grader tree of the Cadence runs it is compared with (coordinator,
2026-10-23: from batch F iteration 0 on, the bars are the batch's own one-shots; older batches stay as history).
The gate passes for a cadence commit and model when, on every task in TASKS, it has at least --n scored runs,
its mean checks passed is above the Sonnet bar and at least the Opus bar.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from loop import record

ROOT = Path(__file__).resolve().parents[1]
TASKS = ("P1", "P2")
SONNET, OPUS = "claude-sonnet-5-5", "claude-opus-5-5"
ONE_SHOT_ARMS = frozenset({"baseline", "one-shot"})  # the backfill says baseline, the driver one-shot
STRETCH_RATIO = 1.25  # owner's stretch goal: a Cadence run takes at most 120-125% of the one-shot's time


def scored_runs(runs: Path) -> list[tuple[dict, dict]]:
    """(record, latest score) of every counted run that has a score."""
    out = []
    for run in sorted(p for p in runs.iterdir() if (p / "record.json").exists()):
        rec = record.load(run)
        scores = record.scores(run)
        if rec["counts"]["counts"] and scores:
            out.append((rec, scores[-1]))
    return out


def cells(runs: Path) -> dict[tuple, list[tuple[dict, dict]]]:
    grouped = defaultdict(list)
    for rec, score in scored_runs(runs):
        sha = (rec.get("cadence") or {}).get("sha")
        grouped[(rec["arm"], sha, rec["model_requested"], rec["task"])].append((rec, score))
    return grouped


def _passed(score: dict) -> int:
    return score.get("passed") or 0


def _tree(score: dict) -> str | None:
    return (score.get("grader") or {}).get("tree")


def baseline(runs: Path, task: str, model: str, tree: str | None = None) -> int | None:
    """The best checks passed of a counted one-shot of `model` on `task` in the newest batch that has one, only
    among scores of grader `tree` when given; None without one."""
    found = [(rec, s) for (arm, _, m, t), rows in cells(runs).items() if arm in ONE_SHOT_ARMS and m == model
             and t == task for rec, s in rows if tree is None or _tree(s) == tree]
    if not found:
        return None
    newest = max(found, key=lambda row: row[0]["started_at"])[0]["batch"]
    return max(_passed(s) for rec, s in found if rec["batch"] == newest)


def oneshot_seconds(runs: Path, task: str, model: str) -> float | None:
    """The mean agent session (seconds) of the counted one-shot runs of `model` on `task`, or None."""
    found = []
    for run in sorted(p for p in runs.iterdir() if (p / "record.json").exists()):
        rec = record.load(run)
        seconds = rec["timing"]["agent_wall_seconds"]
        if (rec["arm"] in ONE_SHOT_ARMS and rec["counts"]["counts"] and rec["task"] == task
                and rec["model_requested"] == model and seconds is not None):
            found.append(seconds)
    return round(sum(found) / len(found), 3) if found else None


def reached_end(runs: Path, rec: dict) -> bool:
    """The run went through the pipeline (no stop block, or R7) or its latest score passed a check. A run that
    stopped early with nothing passed would make a broken pipeline look fast, so it has no time ratio."""
    if rec["stop_point"]["block"] in (None, "R7"):
        return True
    scores = record.scores(runs / rec["run_id"])
    return bool(scores) and (scores[-1].get("passed") or 0) >= 1


def time_ratio(runs: Path, rec: dict) -> float | None:
    """A run's agent session over the one-shot's, same task and model. None when either is unknown, or for a
    Cadence run that did not reach the end (reached_end)."""
    if rec["arm"] not in ONE_SHOT_ARMS and not reached_end(runs, rec):
        return None
    seconds = rec["timing"]["agent_wall_seconds"]
    base = oneshot_seconds(runs, rec["task"], rec["model_requested"])
    return round(seconds / base, 4) if seconds is not None and base else None


def _ratio_text(values: list[float], stopped_early: int = 0) -> str:
    text = f"{sum(values) / len(values):.2f}x" if values else "—"
    return text + (f" ({stopped_early} stopped early)" if stopped_early else "")


def _ratios(runs: Path, recs: list[dict]) -> tuple[list[float], int]:
    """(the time ratios of the runs that reached the end, how many stopped early)."""
    early = sum(1 for r in recs if not reached_end(runs, r))
    return [x for x in (time_ratio(runs, r) for r in recs) if x is not None], early


def gate(runs: Path, model: str, sha: str, n: int = 3) -> tuple[bool, list[str]]:
    lines, ok = [], True
    grouped = cells(runs)
    for task in TASKS:
        rows = [r for (arm, s, m, t), rs in grouped.items() if s and s.startswith(sha) and m == model and t == task
                for r in rs]
        trees = {_tree(s) for _, s in rows}
        tree = trees.pop() if len(trees) == 1 else None  # one grader tree: compare on it
        sonnet, opus = baseline(runs, task, SONNET, tree), baseline(runs, task, OPUS, tree)
        other_tree = tree is not None and (sonnet is None or opus is None)
        if other_tree:  # no one-shot on the runs' grader tree: the newest on any tree, and the line says so
            sonnet, opus = baseline(runs, task, SONNET), baseline(runs, task, OPUS)
        if len(rows) < n:
            ok = False
            lines.append(f"{task}: {len(rows)} scored run(s) at {sha[:7]} on {model}, the gate needs {n}")
            continue
        mean = sum(_passed(s) for _, s in rows) / len(rows)
        if sonnet is None or opus is None:
            ok = False
            lines.append(f"{task}: no Sonnet or Opus one-shot baseline")
            continue
        passed = mean > sonnet and mean >= opus
        ok = ok and passed
        lines.append(f"{task}: mean {mean:.2f}/7 over {len(rows)} runs; Sonnet one-shot {sonnet}/7, Opus one-shot "
                     f"{opus}/7: {'PASS' if passed else 'FAIL'}"
                     + (f" (bars from another grader tree: no one-shot on {tree[:7]})" if other_tree else ""))
        ratios, early = _ratios(runs, [rec for rec, _ in rows])
        lines.append(f"{task}: agent time {_ratio_text(ratios, early)} the {model} one-shot (stretch goal <= "
                     f"{STRETCH_RATIO}; reported, not gated)")
    return ok, lines


def table(runs: Path) -> str:
    grouped = cells(runs)
    lines = ["# Scoreboard", "",
             "Generated by `python -m loop.scoreboard` from `runs/`. Do not edit by hand.", "",
             "Counted runs with a score from the harness-benchmark grader; each run's latest score. Agent min is "
             "each run's agent session; Time ÷ one-shot is the cell's mean of each run's session over the mean "
             f"one-shot session of the same task and model (stretch goal: at most {STRETCH_RATIO}), over the runs "
             "that reached the end of the pipeline or passed a check; runs that stopped early are left out and "
             "counted. "
             "Grader trees are listed, because a score made before a grader change is not regraded when "
             "the run's tree was not kept.", ""]
    for task in TASKS + tuple(sorted({k[3] for k in grouped} - set(TASKS) - {None})):
        lines += [f"## {task}", "",
                  "| First run | Arm | Cadence | Model | n | Checks passed | Mean | Agent min | Time ÷ one-shot | Grader trees |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        keyed = [(min(r["run_id"][:8] for r, _ in rows), key, rows) for key, rows in grouped.items() if key[3] == task]
        for first, (arm, sha, model, _), rows in sorted(keyed, key=lambda x: (x[1][0] != "baseline", x[0], x[1][2])):
            passed = [_passed(s) for _, s in rows]
            trees = sorted({(s["grader"].get("tree") or "unknown")[:7] for _, s in rows})
            repo = (rows[0][0].get("cadence") or {}).get("repo", "").rstrip("/").rsplit("/", 1)[-1]
            commit = f"{repo}@{sha[:7]}" if sha else "—"
            minutes = [r["timing"]["agent_wall_seconds"] / 60 for r, _ in rows if r["timing"]["agent_wall_seconds"]]
            ratios, early = ([], 0) if arm == "baseline" else _ratios(runs, [r for r, _ in rows])
            lines.append(f"| {first[:4]}-{first[4:6]}-{first[6:]} | {arm} | {commit} | {model} | {len(rows)} | "
                         f"{', '.join(f'{p}/7' for p in passed)} | {sum(passed) / len(passed):.2f} | "
                         f"{', '.join(f'{m:.0f}' for m in minutes) or '—'} | {'—' if arm == 'baseline' else _ratio_text(ratios, early)} | {', '.join(trees)} |")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.scoreboard", description=__doc__.split("\n\n")[0])
    ap.add_argument("action", nargs="?", choices=["table", "gate"], default="table")
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    ap.add_argument("--out", type=Path, help="write the table here (default: print it)")
    ap.add_argument("--model")
    ap.add_argument("--sha")
    ap.add_argument("--n", type=int, default=3)
    args = ap.parse_args(argv)
    if args.action == "gate":
        if not (args.model and args.sha):
            ap.error("gate needs --model and --sha")
        ok, lines = gate(args.runs, args.model, args.sha, args.n)
        print("\n".join(lines))
        print("GATE PASS" if ok else "GATE FAIL")
        return 0 if ok else 1
    text = table(args.runs)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
