# Run records

One folder per run: `runs/<run_id>/`. This is the learning loop's record of every Cadence run (benchmark,
live or stub). A run that has no folder here is not evidence.

| File | Written by | Rule |
|---|---|---|
| `record.json` | `python -m loop.driver` (new runs), the backfill (old runs) | written once, never changed ([schema](../loop/schema/record.schema.json)) |
| `scores.jsonl` | the driver with `--grade`, a regrade | one line per grading, appended, never edited ([schema](../loop/schema/score.schema.json)) |

`python -m loop.check --base origin/main` validates every record and score and refuses a change that
edits or deletes a record or rewrites a score. Run it before pushing a change to `runs/`.

## Run ids

`YYYYMMDD-words`: the run's start date (UTC), then dash-separated letters and digits, for example
`20261021-P1-cadence-core-haiku-3`. The pattern is in the schema (`run_id`). A commit message, ADR or
write-up that cites a run gives this id, and the id must have a folder here.

## What counts

`record.json` → `counts` says whether the run may count as evidence at all; `scores.jsonl` says what it
scored. A run counts only if both hold:

- `counts.counts` is true. It is false for a run graded by anything but the harness-benchmark grader
  (a session's own probe), a run whose plugin tree was not a clean published commit, and an
  infrastructure loss.
- It has a score from the harness-benchmark grader. Each score names the grader commit and the git tree
  of `golden/pipeline/pipetask`. When the grader tree changes, every run is regraded and a new line is
  appended; the latest grader tree's line is the run's score.

## The blob store

Transcripts and delivered trees are too large for this branch. They go to the orphan branch
`runs-store` of this repository, as `blobs/<sha256>.gz`, where the sha256 is that of the original
(uncompressed) file. The record keeps `sha256`, `bytes`, `store` and `path`. To check a blob:

```sh
git fetch origin runs-store && git worktree add ../runs-store runs-store
python -c "import json,sys; from pathlib import Path; from loop import store; \
  print(store.verify(json.load(open(sys.argv[1]))['transcript'], Path('../runs-store')))" runs/<run_id>/record.json
```

The delivered tree is a `git bundle` of every ref of the repository the agent left, so the grader can run
on it again (`git clone <bundle>`). A record whose blob was never kept says why in `missing`.

## Starting a run

```sh
python -m loop.driver --run-id 20261022-P1-cadence-haiku-1 --kind benchmark --batch 2026-10-22-p1p2 \
  --task P1 --request-id gh-1 --arm cadence --model claude-haiku-5-5 --plugin-dir ../cadence \
  --transcript OUT/transcript.jsonl --tree OUT/repo-as-left --grade OUT/grade.json \
  --store ../runs-store -- <the trial command, e.g. runner/run_trial.sh ...>
```

The driver refuses (exit 2, before anything runs):

- a run id that exists;
- a `--plugin-dir` that is not a clean checkout of a commit on a remote branch (no modified, untracked or
  ignored file);
- a run that could read another Cadence checkout: it searches `--cwd` and HOME (five levels) and refuses
  any copy other than the plugin. Use `--fresh-home <new folder>` and a `--cwd` that holds only the task.

The command runs with `PYTHONDONTWRITEBYTECODE=1`. After it, the plugin must still be at its commit with
no source change; Python bytecode does not count. Otherwise the record says `tree_clean: false` and the
run does not count.

`timing` has the same fields for a one-shot and a Cadence run: `agent_wall_seconds` (the agent session,
from `--timing`, the figure the speed ratio uses), `run_wall_seconds` (the whole command),
`agent_active_seconds` (the transcript's result durations) and `blocks`: with `--context <the run's
.context>`, the peer seconds, peer calls and unfinished peers of each Cadence stage, from its attest logs
(`loop/blocks.py`). Calls above one are repeat rounds. A resumed peer's start/stop pairs are summed (a
duplicate stop counts once); a start left open is `unfinished`. Parallel peers are each counted in full, so
stage times can add up to more than the wall time they overlap. Orchestrator time between peers is in no
stage.
