"""The scoreboard: score per cadence commit over time, per task and model, next to the one-shot baselines.
The release gate reads it.

    python -m loop.scoreboard [--out scoreboard.md]
    python -m loop.scoreboard gate --model claude-haiku-5-5 --sha <cadence sha> [--n 3]
    python -m loop.scoreboard done [--n 3]

A cell takes the counted runs of one (arm, cadence commit, model, task) that have a score, and each run's
latest score. A bar is the mean checks passed of the pinned one-shots of the same task and model
(baselines.json, loop.baselines; owner, 2026-10-23: the baselines are fixed and only Cadence is re-run), so a
one-shot record of a later batch is history and moves no bar. The gate passes for a cadence commit and model when, on every task in TASKS, it has at least --n
scored runs whose mean is at least GOOD_FLOOR (4/7: it beats the pinned Sonnet 3/7); a mean of IDEAL_FLOOR
(5/7) or more is ideal, and each line prints the tier, GOOD or IDEAL (MISS below the floor). Each line prints
best and worst beside the mean for Cadence and both one-shots, so a single lucky run shows.

Done (the owner's Done line, docs/rules.md: P1 and P2 means meet the bar on two consecutive batches, at no
more than 1.25x the one-shot time) is `done`: each batch of counted Cadence-on-Haiku runs passes when, on
every task in TASKS, it has at least --n scored runs whose mean is GOOD or better (tier_of) and whose mean
time ratio (time_ratio, against the pinned basis) is at most STRETCH_RATIO; Done is two passing batches in
a row, batches ordered by the date in their id, then their earliest started_at, then their id.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from loop import baselines, record

ROOT = Path(__file__).resolve().parents[1]
TASKS = ("P1", "P2")
SONNET, OPUS = "claude-sonnet-5-5", "claude-opus-5-5"
ONE_SHOT_ARMS = frozenset({"baseline", "one-shot"})  # the backfill says baseline, the driver one-shot
# The owner's bar (docs/rules.md, Owner's goals; Oct 23): "Original 3/7 of sonnet, must beat and match opus - so 4
# is good, 5 or better is ideal." A Cadence mean per task at n=3, in checks passed of 7.
GOOD_FLOOR = 4
IDEAL_FLOOR = 5
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


def _spread(values: list[int]) -> dict:
    return {"mean": sum(values) / len(values), "best": max(values), "worst": min(values), "n": len(values)}


def bar(task: str, model: str, pinned: Path = baselines.PATH) -> dict | None:
    """{"mean", "best", "worst", "n"} of the checks passed by the pinned one-shots of `model` on `task`
    (loop.baselines.bar); None without one."""
    return baselines.bar(task, model, pinned)


def baseline(task: str, model: str, pinned: Path = baselines.PATH) -> float | None:
    """The bar's mean (see bar), or None."""
    found = bar(task, model, pinned)
    return None if found is None else found["mean"]


def _show(name: str, spread: dict) -> str:
    return (f"{name} mean {spread['mean']:.2f}/7 (best {spread['best']}, worst {spread['worst']}, "
            f"n={spread['n']})")


def latest_tree(run: Path) -> str | None:
    """The grader tree of the run's latest score, or None."""
    scores = record.scores(run)
    return _tree(scores[-1]) if scores else None


def oneshot_seconds(task: str | None, model: str | None, pinned: Path = baselines.PATH) -> float | None:
    """The mean agent session (seconds) of the pinned one-shots of `model` on `task`: loop.speed.oneshot_mean,
    the one basis the gate, the findings and the postmortem read; None without a pinned one-shot."""
    return baselines.seconds(task, model, pinned)[0]


def reached_end(runs: Path, rec: dict) -> bool:
    """The run went through the pipeline (no stop block, or R7) or its latest score passed a check. A run that
    stopped early with nothing passed would make a broken pipeline look fast, so it has no time ratio."""
    if rec["stop_point"]["block"] in (None, "R7"):
        return True
    scores = record.scores(runs / rec["run_id"])
    return bool(scores) and (scores[-1].get("passed") or 0) >= 1


def time_ratio(runs: Path, rec: dict, pinned: Path = baselines.PATH) -> float | None:
    """A run's agent session over the pinned one-shots' of the same task and model (oneshot_seconds, the basis
    loop.speed shows). None when either is
    unknown, or for a Cadence run that did not reach the end (reached_end): the gate's early-stop rule, which
    loop.speed does not apply."""
    if rec["arm"] not in ONE_SHOT_ARMS and not reached_end(runs, rec):
        return None  # a stop with nothing passed would make a broken pipeline look fast
    seconds = rec["timing"]["agent_wall_seconds"]
    base = oneshot_seconds(rec["task"], rec["model_requested"], pinned)
    return round(seconds / base, 4) if seconds is not None and base else None


def _ratio_text(values: list[float], stopped_early: int = 0) -> str:
    text = f"{sum(values) / len(values):.2f}x" if values else "—"
    return text + (f" ({stopped_early} stopped early)" if stopped_early else "")


def _ratios(runs: Path, recs: list[dict], pinned: Path = baselines.PATH) -> tuple[list[float], int]:
    """(the time ratios of the runs that reached the end, how many stopped early)."""
    early = sum(1 for r in recs if not reached_end(runs, r))
    return [x for x in (time_ratio(runs, r, pinned) for r in recs) if x is not None], early


def tier_of(mean: float) -> str:
    """IDEAL at IDEAL_FLOOR or more, GOOD at GOOD_FLOOR or more (the gate passes), else MISS."""
    return "IDEAL" if mean >= IDEAL_FLOOR else "GOOD" if mean >= GOOD_FLOOR else "MISS"


def gate(runs: Path, model: str, sha: str, n: int = 3, pinned: Path = baselines.PATH) -> tuple[bool, list[str]]:
    lines, ok = [], True
    grouped = cells(runs)
    for task in TASKS:
        rows = [r for (arm, s, m, t), rs in grouped.items() if s and s.startswith(sha) and m == model and t == task
                for r in rs]
        sonnet, opus = bar(task, SONNET, pinned), bar(task, OPUS, pinned)
        if len(rows) < n:
            ok = False
            lines.append(f"{task}: {len(rows)} scored run(s) at {sha[:7]} on {model}, the gate needs {n}")
            continue
        cadence = _spread([_passed(s) for _, s in rows])
        if sonnet is None or opus is None:
            ok = False
            lines.append(f"{task}: no pinned Sonnet or Opus one-shot baseline")
            continue
        tier = tier_of(cadence["mean"])
        passed = tier != "MISS"
        ok = ok and passed
        lines.append(f"{task}: {_show(model, cadence)}; {_show('Sonnet one-shot', sonnet)}; "
                     f"{_show('Opus one-shot', opus)}: good at {GOOD_FLOOR}/7, ideal at {IDEAL_FLOOR}/7: "
                     f"{tier}: {'PASS' if passed else 'FAIL'}")
        ratios, early = _ratios(runs, [rec for rec, _ in rows], pinned)
        lines.append(f"{task}: agent time {_ratio_text(ratios, early)} the {model} one-shot (stretch goal <= "
                     f"{STRETCH_RATIO}; reported, not gated)")
    return ok, lines


DONE_MODEL = "claude-haiku-5-5"


def _batch_key(recs: list[dict]) -> tuple[str, str, str]:
    batch = recs[0]["batch"]
    return batch[:10], min((r["started_at"] or "" for r in recs), default=""), batch


def done(runs: Path, n: int = 3, pinned: Path = baselines.PATH) -> tuple[bool, list[str]]:
    """(Done, one line per batch of counted Cadence-on-Haiku runs then the verdict): see the module doc."""
    batches: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    for (arm, _, model, task), rows in cells(runs).items():
        if arm not in ONE_SHOT_ARMS and model == DONE_MODEL and task in TASKS:
            for rec, score in rows:
                batches[rec["batch"]].append((rec, score))
    order = sorted(batches, key=lambda b: _batch_key([rec for rec, _ in batches[b]]))
    lines, passing = [], []
    for batch in order:
        parts, missed, untimed, slow, ok = [], [], [], [], True
        for task in TASKS:
            rows = [(rec, s) for rec, s in batches[batch] if rec["task"] == task]
            if len(rows) < n:
                ok = False
                parts.append(f"{task} {len(rows)} run(s), needs {n}")
                continue
            mean = sum(_passed(s) for _, s in rows) / len(rows)
            ratios, _ = _ratios(runs, [rec for rec, _ in rows], pinned)
            ratio = sum(ratios) / len(ratios) if ratios else None
            if tier_of(mean) == "MISS":
                missed.append(task)
            if ratio is None:  # no run with a time ratio: Done needs the time, so the batch fails
                untimed.append(task)
            elif ratio > STRETCH_RATIO:
                slow.append(task)
            parts.append(f"{task} mean {mean:.2f}/7 {tier_of(mean)}, time {_ratio_text(ratios)}")
        ok = ok and not missed and not untimed and not slow
        why = [f"below {GOOD_FLOOR}/7 on {', '.join(missed)}"] * bool(missed) + \
              [f"no time on {', '.join(untimed)}"] * bool(untimed) + \
              [f"time above {STRETCH_RATIO}x on {', '.join(slow)}"] * bool(slow)
        lines.append(f"{batch}: {'; '.join(parts)}: {'PASS' if ok else 'FAIL'}" + (f" ({'; '.join(why)})" if why else ""))
        passing.append(ok)
    pair = next((i for i in range(1, len(order)) if passing[i - 1] and passing[i]), None)
    if pair is None:
        return False, lines + ["NOT DONE: no two consecutive batches pass"]
    return True, lines + [f"DONE: {order[pair - 1]} and {order[pair]} pass in a row"]


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
            ratios, early = ([], 0) if arm in ONE_SHOT_ARMS else _ratios(runs, [r for r, _ in rows])
            lines.append(f"| {first[:4]}-{first[4:6]}-{first[6:]} | {arm} | {commit} | {model} | {len(rows)} | "
                         f"{', '.join(f'{p}/7' for p in passed)} | {sum(passed) / len(passed):.2f} | "
                         f"{', '.join(f'{m:.0f}' for m in minutes) or '—'} | {'—' if arm in ONE_SHOT_ARMS else _ratio_text(ratios, early)} | {', '.join(trees)} |")
        lines.append("")
    _, done_lines = done(runs)
    lines += ["## Done", "",
              f"The owner's Done line: P1 and P2 means meet the bar on two consecutive batches of Cadence on Haiku, "
              f"at no more than {STRETCH_RATIO}x the pinned one-shot time (`python -m loop.scoreboard done`).", ""]
    lines += [f"- {line}" for line in done_lines] + [""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.scoreboard", description=__doc__.split("\n\n")[0])
    ap.add_argument("action", nargs="?", choices=["table", "gate", "done"], default="table")
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    ap.add_argument("--out", type=Path, help="write the table here (default: print it)")
    ap.add_argument("--model")
    ap.add_argument("--sha")
    ap.add_argument("--n", type=int, default=3)
    args = ap.parse_args(argv)
    if args.action == "done":
        ok, lines = done(args.runs, args.n)
        print("\n".join(lines))
        return 0 if ok else 1
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
