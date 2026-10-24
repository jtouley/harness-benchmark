"""The one-line summary of a finished run: what scripts/run_one.sh prints as its last line (the line --wait
reports), puts in the record commit's message and in the pull request body ($WORK/pr.md), and what
scripts/correct_record_text.py writes again for a record published with the old text.

    python -m loop.run_summary <runs/<run-id> directory>

The headline is the benchmark score, the scoreboard's own: round(reward x total)/total (scoreboard._passed),
so a run whose checks the grader voids (stream_ok or idempotent false: reward 0) reads 0/7 here as it does on
the scoreboard. Run 20261024-P1-cadence-haiku-core-4 (passed 2, reward 0.0, stream_ok false) printed "2/7",
its passed count, in all three places while the scoreboard showed 0.00 MISS. The grader's own fields follow.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loop import record, scoreboard


def _flag(value) -> str:
    return "?" if value is None else str(value).lower()


def score_text(score: dict | None) -> str:
    """`score S/T; passed P/T, reward R, stream_ok S, idempotent I` for one scores.jsonl line."""
    if not score:
        return "score none (no scores.jsonl line)"
    total = score.get("total")
    return (f"score {scoreboard._passed(score)}/{total}; passed {score.get('passed')}/{total}, "
            f"reward {score.get('reward')}, stream_ok {_flag(score.get('stream_ok'))}, "
            f"idempotent {_flag(score.get('idempotent'))}")


def summary(run: Path) -> str:
    """The run's summary line from its record.json and the latest line of its scores.jsonl."""
    rec = record.load(run)
    scores = record.scores(run)
    stop = rec.get("stop_point") or {}
    timing = rec.get("timing") or {}
    counts = rec.get("counts") or {}
    cadence = rec.get("cadence") or {}
    return (f"{rec['run_id']}: {score_text(scores[-1] if scores else None)}; stop {stop.get('block')}"
            f" ({(stop.get('reason') or '')[:80]}), agent {timing.get('agent_wall_seconds')} s,"
            f" counts {counts.get('counts')} ({counts.get('why')}),"
            f" cadence {(cadence.get('sha') or '?')[:7]} tree {(cadence.get('tree') or '?')[:7]}")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m loop.run_summary <runs/<run-id> directory>", file=sys.stderr)
        return 2
    print(summary(Path(args[0])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
