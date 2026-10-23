"""Speed: each Cadence run's agent time against the one-shot's, per task and model, on every run.

    python -m loop.speed [--batch <id>] [--runs runs]

The owner's stretch goal: a Cadence run takes at most 120 to 125 percent of a one-shot's time
(STRETCH_RATIO, from loop.scoreboard). The one-shot time takes the rule of the gate's bars: the mean
agent session of the counted one-shots (arm `baseline` or `one-shot`) of the task and model in the
newest batch that has one, on the Cadence run's grader tree; when no batch has one on that tree, the
newest batch on any tree, and the row says so. "Newest" stops at the run's own batch (batch_order:
batches sort by the date in their id, then by the earliest started_at of their records, then by id):
a later batch's one-shots never move an earlier run's ratio, so a committed postmortem keeps its numbers
when the next batch lands. Every caller names the batch it reads for. The Basis column names
the batch and the tree. For each Cadence run: its agent session, the
ratio, whether it hit its cap (`timing.hit_cap`, from the trial's timing.json), whether it reached the
end of the pipeline, and its time per block (loop.blocks) with the three slowest blocks named. A run
whose ratio is above the stretch goal is flagged. The postmortem's Speed section reads these rows, so
the two never disagree, and loop.scoreboard.time_ratio (the gate, the scoreboard table and the findings'
`max_time_ratio`) takes its one-shot mean from oneshot_mean here, so every ratio in the loop has one basis.

The runs below the ratio or above it are shown alike; a run that stopped early keeps its ratio here
(a slow stop is still slow) and says it stopped early. loop.scoreboard.time_ratio keeps its own rule
(no ratio for an early stop).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loop import record, scoreboard

ROOT = Path(__file__).resolve().parents[1]
ONESHOT_ARMS = ("baseline", "one-shot")
STRETCH_RATIO = scoreboard.STRETCH_RATIO
SLOWEST = 3


def _records(runs: Path) -> list[tuple[Path, dict]]:
    return [(p, record.load(p)) for p in sorted(runs.iterdir()) if (p / "record.json").exists()]


def batch_order(records: list[tuple[Path, dict]]) -> dict[str, tuple[str, str, str]]:
    """Each batch's sort key: the date in its id, the earliest started_at of its records ("" when none has
    one), then the id. Two batches of one day order by when they began, not by their names."""
    starts: dict[str, str] = {}
    for _, rec in records:
        batch, started = rec["batch"], rec["started_at"] or ""
        starts.setdefault(batch, "")
        if started:  # a record with no started_at does not reset the batch's start, in any read order
            starts[batch] = min(starts[batch] or started, started)
    return {batch: (batch[:10], started, batch) for batch, started in starts.items()}


def _newest_batch_mean(found: list[tuple[str, float]], order: dict) -> tuple[float, str]:
    """(the mean of the (batch, seconds) pairs in the newest batch by `order`, that batch)."""
    newest = max((batch for batch, _ in found), key=order.__getitem__)
    values = [seconds for batch, seconds in found if batch == newest]
    return round(sum(values) / len(values), 3), newest


def oneshot_mean(runs: Path, task: str | None, model: str | None, tree: str | None,
                 batch: str) -> tuple[float | None, str]:
    """(the mean agent session of the counted one-shots of `task` and `model`, the basis). The one-shots are
    those of the newest batch no later than `batch` (batch_order) on grader tree `tree`, else of the newest
    such batch on any tree, labelled so; None with no counted one-shot. `batch` is required: a read with no
    batch would follow the newest batch wherever it lands, and so would any number built on it."""
    records = _records(runs)
    order = batch_order(records)
    upto = order.get(batch, (batch[:10], "", batch))
    same, any_tree = [], []
    for run, rec in records:
        seconds = rec["timing"]["agent_wall_seconds"]
        if (rec["arm"] in ONESHOT_ARMS and rec["counts"]["counts"] and rec["task"] == task
                and rec["model_requested"] == model and seconds is not None and order[rec["batch"]] <= upto):
            any_tree.append((rec["batch"], seconds))
            if tree is not None and scoreboard.latest_tree(run) == tree:
                same.append((rec["batch"], seconds))
    if same:
        mean, newest = _newest_batch_mean(same, order)
        return mean, f"batch {newest}, same grader tree {tree[:7]}"
    if any_tree:
        mean, newest = _newest_batch_mean(any_tree, order)
        label = f"any grader tree (no counted one-shot on {tree[:7]})" if tree else "any grader tree"
        return mean, f"batch {newest}, {label}"
    return None, "no counted one-shot of this task and model"


def slowest_blocks(blocks: dict | None, n: int = SLOWEST) -> list[tuple[str, float]]:
    if not blocks:
        return []
    return sorted(((stage, t["seconds"]) for stage, t in blocks.items()), key=lambda kv: (-kv[1], kv[0]))[:n]


def row(runs: Path, run: Path, rec: dict) -> dict:
    """One Cadence run's speed row."""
    seconds = rec["timing"]["agent_wall_seconds"]
    base, basis = oneshot_mean(runs, rec["task"], rec["model_requested"], scoreboard.latest_tree(run), rec["batch"])
    ratio = round(seconds / base, 4) if seconds is not None and base else None
    blocks = record.blocks(run, rec)
    return {"run_id": rec["run_id"], "task": rec["task"], "model": rec["model_requested"], "arm": rec["arm"],
            "counts": rec["counts"]["counts"], "agent_wall_seconds": seconds, "oneshot_seconds": base, "basis": basis,
            "ratio": ratio, "flagged": ratio is not None and ratio > STRETCH_RATIO,
            "hit_cap": rec["timing"].get("hit_cap"), "reached_end": scoreboard.reached_end(runs, rec),
            "stop_block": rec["stop_point"]["block"], "blocks": blocks, "slowest": slowest_blocks(blocks)}


def rows(runs: Path, batch: str | None = None, run_ids: list[str] | None = None) -> list[dict]:
    """The speed rows of every Cadence run (of `batch`, or of `run_ids`), in run-id order."""
    out = []
    for run, rec in _records(runs):
        if rec["arm"] in ONESHOT_ARMS:
            continue
        if batch is not None and rec["batch"] != batch:
            continue
        if run_ids is not None and rec["run_id"] not in run_ids:
            continue
        out.append(row(runs, run, rec))
    return out


def _minutes(seconds: float | None) -> str:
    return f"{seconds / 60:.1f}" if seconds is not None else "—"


def ratio_text(r: dict) -> str:
    if r["ratio"] is None:
        return "—"
    text = f"{r['ratio']:.2f}"
    if r["flagged"]:
        text += f" (above {STRETCH_RATIO})"
    if not r["reached_end"]:
        text += " (stopped early)"
    return text


def cap_text(r: dict) -> str:
    return {True: "hit", False: "no", None: "?"}[r["hit_cap"]]


def slowest_text(r: dict) -> str:
    return ", ".join(f"{stage} {seconds / 60:.1f} min" for stage, seconds in r["slowest"]) or "—"


HEADER = ("| Run | Task | Model | Agent min | One-shot min | Basis | Ratio | Cap | Stop | Slowest blocks |",
          "|---|---|---|---|---|---|---|---|---|---|")


def line(r: dict) -> str:
    return (f"| `{r['run_id']}` | {r['task']} | {r['model']} | {_minutes(r['agent_wall_seconds'])} | "
            f"{_minutes(r['oneshot_seconds'])} | {r['basis']} | {ratio_text(r)} | {cap_text(r)} | "
            f"{r['stop_block'] or '—'} | {slowest_text(r)} |")


def table(runs: Path, batch: str | None = None) -> str:
    found = rows(runs, batch)
    out = [f"# Speed{' of batch ' + batch if batch else ''}", "",
           f"Each Cadence run's agent session against the mean one-shot session of the same task and model, "
           f"from the newest batch no later than the run's with a counted one-shot on the run's grader tree, "
           f"else on any tree (Basis; stretch goal: at most {STRETCH_RATIO}). Cap: whether the run hit its guard "
           f"cap or backstop. "
           f"Slowest blocks: peer time per block from the run's attest logs (loop.blocks).", ""]
    groups: dict[tuple, list[dict]] = {}
    for r in found:
        groups.setdefault((r["task"] or "", r["model"] or ""), []).append(r)
    for (task, model), group in sorted(groups.items()):
        out += [f"## {task or 'no task'}, {model or 'no model'}", "", *HEADER]
        out += [line(r) for r in group]
        flagged = [r["run_id"] for r in group if r["flagged"]]
        out += ["", f"Above the stretch goal: {', '.join(f'`{i}`' for i in flagged) or 'none'}.", ""]
    if not groups:
        out += ["No Cadence run" + (f" in batch {batch}" if batch else "") + ".", ""]
    return "\n".join(out)


def problems(runs: Path) -> list[str]:
    """Counted Cadence runs the loop cannot time: no agent session, or no time per block."""
    out = []
    for run, rec in _records(runs):
        if rec["arm"] in ONESHOT_ARMS or not rec["counts"]["counts"]:
            continue
        if rec["timing"]["agent_wall_seconds"] is None:
            out.append(f"{rec['run_id']}: counted Cadence run with no agent session time (timing.json's agent_seconds)")
        if record.blocks(run, rec) is None:
            out.append(f"{rec['run_id']}: counted Cadence run with no time per block (loop.blocks from its .context)")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.speed", description=__doc__.split("\n\n")[0])
    ap.add_argument("--batch")
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    args = ap.parse_args(argv)
    print(table(args.runs, args.batch))
    return 0


if __name__ == "__main__":
    sys.exit(main())
