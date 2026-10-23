"""The pinned one-shot baselines (baselines.json): the gate's bars and every time ratio's one-shot basis.

The owner, 2026-10-23: the baselines are fixed and only Cadence is re-run. The bar is the 15 October
one-shots (the postmortems' Decisions since 22 October: beat the Sonnet one-shot, more than 3/7, and match
the Opus one-shot, 5 to 6/7). The file names those runs per task and model with the checks they passed and
their agent session; nothing here reads the newest batch, so a one-shot record of a later batch is history
and moves no bar and no ratio. loop.check holds each entry to its run's record and latest score (problems).
"""

from __future__ import annotations

import json
from pathlib import Path

from loop import record

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "baselines.json"
ONE_SHOT_ARMS = ("baseline", "one-shot")


def load(path: Path = PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def entries(task: str | None, model: str | None, path: Path = PATH) -> list[dict]:
    """The pinned runs of `task` and `model`, or [] when none is pinned."""
    return list(load(path)["cells"].get(task or "", {}).get(model or "", []))


def bar(task: str, model: str, path: Path = PATH) -> dict | None:
    """{"mean", "best", "worst", "n"} of the checks the pinned one-shots passed, or None."""
    passed = [e["passed"] for e in entries(task, model, path)]
    if not passed:
        return None
    return {"mean": sum(passed) / len(passed), "best": max(passed), "worst": min(passed), "n": len(passed)}


def seconds(task: str | None, model: str | None, path: Path = PATH) -> tuple[float | None, str]:
    """(the mean agent session of the pinned one-shots, the basis naming them); None without one."""
    found = [e for e in entries(task, model, path) if e["agent_wall_seconds"] is not None]
    if not found:
        return None, "no pinned one-shot of this task and model"
    mean = round(sum(e["agent_wall_seconds"] for e in found) / len(found), 3)
    return mean, "pinned " + ", ".join(e["run_id"] for e in found)


def problems(runs: Path, path: Path = PATH) -> list[str]:
    """Pinned entries that are not what their run's record and latest score say."""
    out = []
    for task, models in load(path)["cells"].items():
        for model, pinned in models.items():
            for e in pinned:
                where = f"{path.name}: {task} {model} {e['run_id']}"
                run = runs / e["run_id"]
                if not (run / "record.json").exists():
                    out.append(f"{where}: no such run")
                    continue
                rec, scores = record.load(run), record.scores(run)
                if rec["arm"] not in ONE_SHOT_ARMS or not rec["counts"]["counts"]:
                    out.append(f"{where}: not a counted one-shot")
                if (rec["task"], rec["model_requested"]) != (task, model):
                    out.append(f"{where}: the record is {rec['task']} {rec['model_requested']}")
                if not scores or (scores[-1].get("passed"), scores[-1].get("total")) != (e["passed"], e["total"]):
                    out.append(f"{where}: passed {e['passed']}/{e['total']} is not the run's latest score")
                if rec["timing"]["agent_wall_seconds"] != e["agent_wall_seconds"]:
                    out.append(f"{where}: agent_wall_seconds is not the record's")
    return out
