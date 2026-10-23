"""Speed: each Cadence run's agent time against the one-shot's, per task and model, on every run.

    python -m loop.speed [--batch <id>] [--runs runs]

The owner's stretch goal: a Cadence run takes at most 120 to 125 percent of a one-shot's time
(STRETCH_RATIO, from loop.scoreboard). The one-shot time is the gate's bars' source: the mean agent session
of the pinned one-shots of the task and model (baselines.json, loop.baselines; owner, 2026-10-23: the
baselines are fixed and only Cadence is re-run). No batch's one-shots move a ratio, so a committed
postmortem keeps its numbers when the next batch lands. The Basis column names the pinned runs. For each
Cadence run: its agent session, the
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

from loop import baselines, record, scoreboard

ROOT = Path(__file__).resolve().parents[1]
ONESHOT_ARMS = ("baseline", "one-shot")
STRETCH_RATIO = scoreboard.STRETCH_RATIO
SLOWEST = 3


def _records(runs: Path) -> list[tuple[Path, dict]]:
    return [(p, record.load(p)) for p in sorted(runs.iterdir()) if (p / "record.json").exists()]


def oneshot_mean(task: str | None, model: str | None, pinned: Path = baselines.PATH) -> tuple[float | None, str]:
    """(the mean agent session of the pinned one-shots of `task` and `model`, the basis naming them); None
    without a pinned one-shot (loop.baselines.seconds)."""
    return baselines.seconds(task, model, pinned)


def slowest_blocks(blocks: dict | None, n: int = SLOWEST) -> list[tuple[str, float]]:
    if not blocks:
        return []
    return sorted(((stage, t["seconds"]) for stage, t in blocks.items()), key=lambda kv: (-kv[1], kv[0]))[:n]


def row(runs: Path, run: Path, rec: dict, pinned: Path = baselines.PATH) -> dict:
    """One Cadence run's speed row."""
    seconds = rec["timing"]["agent_wall_seconds"]
    base, basis = oneshot_mean(rec["task"], rec["model_requested"], pinned)
    ratio = round(seconds / base, 4) if seconds is not None and base else None
    blocks = record.blocks(run, rec)
    return {"run_id": rec["run_id"], "task": rec["task"], "model": rec["model_requested"], "arm": rec["arm"],
            "counts": rec["counts"]["counts"], "agent_wall_seconds": seconds, "oneshot_seconds": base, "basis": basis,
            "ratio": ratio, "flagged": ratio is not None and ratio > STRETCH_RATIO,
            "hit_cap": rec["timing"].get("hit_cap"), "reached_end": scoreboard.reached_end(runs, rec),
            "stop_block": rec["stop_point"]["block"], "blocks": blocks, "slowest": slowest_blocks(blocks)}


def rows(runs: Path, batch: str | None = None, run_ids: list[str] | None = None,
         pinned: Path = baselines.PATH) -> list[dict]:
    """The speed rows of every Cadence run (of `batch`, or of `run_ids`), in run-id order."""
    out = []
    for run, rec in _records(runs):
        if rec["arm"] in ONESHOT_ARMS:
            continue
        if batch is not None and rec["batch"] != batch:
            continue
        if run_ids is not None and rec["run_id"] not in run_ids:
            continue
        out.append(row(runs, run, rec, pinned))
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


def table(runs: Path, batch: str | None = None, pinned: Path = baselines.PATH) -> str:
    found = rows(runs, batch, pinned=pinned)
    out = [f"# Speed{' of batch ' + batch if batch else ''}", "",
           f"Each Cadence run's agent session against the mean session of the pinned one-shots of the same task "
           f"and model (baselines.json; Basis; stretch goal: at most {STRETCH_RATIO}). Cap: whether the run hit its guard "
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
