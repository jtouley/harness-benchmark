# Run records

One folder per run: `runs/<run_id>/`. This is the learning loop's record of every Cadence run (benchmark,
live or stub). A run that has no folder here is not evidence.

| File | Written by | Rule |
|---|---|---|
| `record.json` | `python -m loop.driver` (new runs), `loop.backfill` and `loop.backfill_live` (old runs) | written once, never changed ([schema](../loop/schema/record.schema.json)) |
| `scores.jsonl` | the driver with `--grade`, a regrade | one line per grading, appended, never edited ([schema](../loop/schema/score.schema.json)) |

`citations.json` (root) is the trace of these runs into Cadence: per cited run, the cadence commits
whose `Evidence: <run id>` trailer names it, with each commit's finding, pull request and status. `python
-m loop.trace snapshot --cadence <checkout>` refreshes it; `python -m loop.trace` prints the table for
every counted run and every cited run, and `python -m loop.postmortem --run <run id>` prints one run's row.

`python -m loop.check --base origin/main` validates every record and score and refuses a change that
edits or deletes a record or rewrites a score. Run it before pushing a change to `runs/`.

## After a merge

Two green pull requests can make a red main: #71 added findings while #72 changed the postmortem
generator, each was green on its own base, and main was red on the committed postmortems once both
were in. So two rules hold for this repository:

- After every merge, the reviewer runs `scripts/ci_local.sh` on `origin/main`, and a red main is fixed
  before the next merge.
- A pull request that touches `findings.jsonl`, `citations.json`, `runs/` or the generators under
  `loop/` regenerates `postmortems/` (`python -m loop.postmortem --all`) and `scoreboard.md`
  (`python -m loop.scoreboard --out scoreboard.md`) in the same commit, so the committed files are
  what the generators write at that commit.

The loop enforces this. `python -m loop.driver` writes the batch's postmortem (every committed postmortem
that covers the batch, or a new `postmortems/<batch>.md`) and `scoreboard.md` when it records a run, so
they go in the record's commit. `python -m loop.check` refuses a counted run, or a run a finding cites,
that is in no committed postmortem; a committed postmortem that is not what the generator writes from
its notes; and a `scoreboard.md` that is not what the scoreboard writes. A postmortem named `<name>`
covers the batches its `<name>.notes.json` lists under `batches`, else the one batch `<name>`.

## Run ids

`YYYYMMDD-words`: the run's start date (UTC), then dash-separated letters and digits, for example
`20261021-P1-cadence-core-haiku-3`. The pattern is in the schema (`run_id`). A commit message, ADR or
write-up that cites a run gives this id, and the id must have a folder here.

## What counts

`record.json` → `counts` says whether the run may count as evidence at all; `scores.jsonl` says what it
scored. A run counts only if both hold:

- `counts.counts` is true. It is false for a run graded by anything but the harness-benchmark grader
  (a session's own probe), a run whose plugin tree was not a clean published commit, and an
  infrastructure loss. The live runs of 21 and 22 October (`kind` `live`, `loop.backfill_live`) were
  graded by the sessions that made them, so each says `self-graded, no outside grader, pre-driver` in
  `counts.why` and has no `scores.jsonl`.
- It has a score from the harness-benchmark grader. A backfilled record counts only with one (`loop.check` refuses it otherwise). The
  15 October one-shots, the gate's Sonnet and Opus baselines, count: their scores are from this grader, with
  `grader.commit` null and `basis` "not recorded" (the laptop grades were made before the grader commit was
  recorded). Each score names the grader commit and the git tree
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
- `--task P4`, the hold-out, unless `--holdout` says the run is the owner's final check;
- a `--plugin-dir` that is not a clean checkout of a commit on a remote branch (no modified, untracked or
  ignored file);
- a run that could read another Cadence checkout: it searches `--cwd` and HOME (five levels) and refuses
  any copy other than the plugin. Use `--fresh-home <new folder>` and a `--cwd` that holds only the task.
- a Cadence benchmark or live run without `--spec` or without `--agent-argv`;
- a command with a `claude` call that carries any prompt text other than the one prompt: a bare `-p`, a
  positional argument, input piped into it, or a flag outside the list in `loop/driver.py`
  (`CLAUDE_VALUE_FLAGS`, `CLAUDE_BARE_FLAGS`).

## The entry and what a run may reach

The only prompt a Cadence run gets is `/cadence <the spec's absolute path>` (owner, 2026-10-22); a one-shot gets
the spec's text. The driver passes it to the command as `HB_AGENT_PROMPT` and keeps the spec's path, sha256 and
the prompt in `spec`. `--agent-argv` is the argv the command started the agent with: if it gives the agent more
than that prompt, the run does not count. What the entry does is the result: an exit 1 at activation (F-9) is
recorded as it is.

After the run, every tool-call input in the transcript is scanned for the benchmark (`harness-benchmark`, this
repository's path, `golden/`, `answer_key`, `pipetask`, `grader.pyz`) and for any other Cadence checkout (a
`/cadence*/` path segment; the plugin's own path is masked). A hit is in `isolation.contact`, and the run does
not count. `golden/` also matches a task path that happens to contain it; that errs on the safe side.

`isolation.auth` is how the agent authenticated (`scripts/host_trial.py --auth`, the driver's `--auth`):

- `proxy`: the cloud host. Outbound HTTPS goes through a proxy that adds the operator's credentials, so the fresh
  HOME gets no credential file.
- `oauth-file`: the owner's machine. Claude Code's OAuth credential, `~/.claude/.credentials.json`, is copied into
  the fresh HOME and nothing else from the operator's HOME is.

In both, `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` are not in the agent's environment. Records written
before 2026-10-23 18:45 UTC (the first batch F run included) have no `auth`; they ran by the proxy route.

The command runs with `PYTHONDONTWRITEBYTECODE=1`. After it, the plugin must still be at its commit with
no source change; Python bytecode does not count. Otherwise the record says `tree_clean: false` and the
run does not count.

`timing` has the same fields for a one-shot and a Cadence run: `agent_wall_seconds` (the agent session,
from `--timing`'s `agent_seconds`, the figure the speed ratio uses), `run_wall_seconds` (the whole command),
`agent_active_seconds` (the transcript's result durations), `blocks` (peer seconds per block from the run's
`.context`, `--context`), and, when the trial's timing.json says them (`scripts/host_trial.py` writes
`hit_cap` and `agent_cap_seconds`), `hit_cap` and `cap_seconds`.

`python -m loop.speed [--batch <id>]` prints each Cadence run's agent session against the mean one-shot
session of the same task and model (counted one-shots on the run's grader tree, else every counted
one-shot, labelled so), its ratio to the owner's stretch goal of 1.25, whether it hit its cap, and its three
slowest blocks; the postmortem's Speed section reads the same rows. `loop.check` refuses a counted Cadence
run with no agent session time or no time per block.
