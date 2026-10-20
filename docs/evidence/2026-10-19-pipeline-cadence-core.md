# Pipeline family: the first harness arm (cadence-core on Haiku 5.5), 2026-10-19

Status: exploratory, one run per cell, run outside the isolated runner. Corrected on 19 October after
the owner's review ([#55](https://github.com/jtouley/harness-benchmark/issues/55)): the third P1
run's cause, the P2 run's status, the cost label, the audit-trail claim, and the missing transcripts
are all amended below. Data:
[`2026-10-19-pipeline-cadence-core/`](2026-10-19-pipeline-cadence-core/). The one-shot rows it is
compared with are from [the 15 October trials](2026-10-15-pipeline-trials.md).

*Disclosure: the owner of this benchmark wrote Cadence.*

## Question

Does a harness let a cheap model deliver a long pipeline task that the same model working alone
did not? On 15 October, Haiku 5.5 alone scored 0 of 7 on P1, P2 and P3. This round runs the ten-block
core of Cadence (`cadence-core`, [ADR-0008](https://github.com/jtouley/cadence/blob/ccr-3d2e0c73-lr6bdt/docs/adr/0008-ten-block-core.md))
with Haiku 5.5 as orchestrator and as every peer.

## Setup

- **Host, not the isolated runner.** The machine (4 CPUs, 15 GB, x86-64 Linux) has no Docker daemon,
  so the runner images and P3 could not run. Each trial ran on the host: a clean, empty `HOME`; the
  dev replay (seed 0) on `localhost:8099` during the agent's session; the grader, with its own replay
  on seed 1, after it. No clean room: the file system was not isolated, and the agent's environment
  came from the host's shell with `HOME`, `CADENCE_HOME` and the two variables below overridden.
- **Arm.** Cadence on branch `ccr-3d2e0c73-lr6bdt` (`4935e83` for the Opus runs, `b1bbdcd` for the
  first two Haiku runs, `f734888` for the P1 rerun, `f6011df` for the third P1 run, `4af76ac` for the
  fourth; each run's `provenance.json` names its sha),
  loaded with `--plugin-dir` for the session only. Config: `adapter: none`, `peer_models: {"default": "haiku"}`. The task repository got
  a `.cadence.json` that gates `pipeline/`, `engine/`, `pipelines/`, `transform/` and the `Makefile`,
  so the edit guard applies to the task's code. Prompt: the lockfile's Cadence drive prompt around the
  task prompt word for word, plus the pilot's environment note (no GitHub, PR text to `outputs/PR.md`,
  nobody answers, task id gh-1). Claude Code 2.1.303, permission mode `auto`, guard cap 7,200 s.
- **Grading.** `pipetask.trial` on the committed working tree (the runner's `--snapshot-worktree`
  step done by hand: `git add -A && git commit`), deadline 600 s. Then the code-based measures of the
  quality model: `quality_metrics.py` (package `pipeline` for P1, `engine` for P2),
  `commit_replay.py`, `clean_room_check.py`, and cost from token counts at `pricing.json` list prices.

## The host reproduces the references

| Run | Task | Repository | Reward | Checks | Grading s |
|---|---|---|---|---|---|
| P1-ref-host-1 | P1 | reference | 1.0 | 7/7 | 170 |
| P1-skel-host-1 | P1 | skeleton unchanged | 0.0 | 0/7 | 5 |
| P2-ref-host-1 | P2 | reference | 1.0 | 7/7 | 166 (the four `make` runs) |
| P2-skel-host-1 | P2 | skeleton unchanged | 0.0 | 0/7 | 2 |

Same results as on the laptop (15 October), on a different architecture and OS.

## Results

| Run | Task | Arm | Model | Reward | Checks | Idempotent | Stream ok | Commits | Agent s | Cost (list) | Host-reported cost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1-cadence-core-1 | P1 | cadence-core | Opus 5.5 | 0.0 | 0/7 | no | no | 0 | 1,029 | $1.96 | $2.17 |
| P1-cadence-core-opus-2 | P1 | cadence-core | Opus 5.5 | interrupted at P1 (owner switched the arm to Haiku) | | | | | | | |
| **P1-cadence-core-haiku-1** | P1 | cadence-core | **Haiku 5.5** | **0.7143** | **5/7** | yes | yes | 9 | 3,062 | **$0.67** | $2.24 |
| P2-cadence-core-haiku-1 | P2 | cadence-core | Haiku 5.5 | cut off: not a scored run (grader read 1/7 of the tree it left) | | yes | yes | 9 | 7,203 (host guard) | $0.65 | none (killed) |
| P1-cadence-core-haiku-2 | P1 | cadence-core | Haiku 5.5 | 0.0 | 0/7 | no | no | 0 | 1,496 | $0.30 | $0.32 |
| P1-cadence-core-haiku-3 | P1 | cadence-core | Haiku 5.5 | 0.0 | 0/7 | no (grader bug #49) | yes | 14 | 6,117 | $0.90 | $3.00 |
| P1-cadence-core-haiku-4 | P1 | cadence-core | Haiku 5.5 | cut off: not a scored run (grader read 0/7 of the tree it left) | | yes | yes | 8 | 7,108 (operator's shell limit) | $0.72 | none (killed) |

For comparison, the 15 October one-shots on P1 (isolated runner, Claude Code 2.1.287, regraded):

| Run | Model | Reward | Checks | Agent s | Cost (list) |
|---|---|---|---|---|---|
| P1-haiku-1 | Haiku 5.5 | 0.0 | 0/7 | 1,883 | $0.30 |
| P1-sonnet-1 | Sonnet 5.5 | 0.4286 | 3/7 | 1,349 | $2.06 |
| P1-opus-1 | Opus 5.5 | 0.8571 | 6/7 | 1,689 | $5.82 |

And on P2:

| Run | Model | Reward | Checks | Agent s | Cost (list) |
|---|---|---|---|---|---|
| P2-haiku-1 | Haiku 5.5 | 0.0 | 0/7 | 1,597 | $0.28 |
| P2-sonnet-1 | Sonnet 5.5 | 0.4286 | 3/7 | 1,716 | $4.56 |
| P2-opus-1 | Opus 5.5 | 0.7143 | 5/7 | 2,465 | $7.84 |

The cost column uses `pricing.json` list prices from the token counts, as the other rounds do. **Every
Haiku figure in it is a lower bound**: the cost code prices every token at the base rate, and Haiku
5.5 charges five times more for a prompt over 100K tokens, which these sessions reach early (the
sessions read 240K to 290K cached tokens per turn on average). Per-request pricing is
[#51](https://github.com/jtouley/harness-benchmark/issues/51). Claude Code's own figure (the last
column) is kept for the record; it is 3.3 times the list figure on two runs and equal on the third,
so the long-prompt rate alone does not explain it. The P2 run has no host figure: the host's guard
killed the session before it wrote its result, so its cost is summed from the transcript
(`cost.json`, `source`).

### P1-cadence-core-haiku-1

What it delivered: dlt batch ingestion to a Parquet lake, a dbt project with staging, core and mart
models, a dlt stream consumer with resume, seven published marts, an `oracle_map.yml`, a
`DECISIONS.md` with 18 decisions, three test files. Both builds gave the same outputs; both stream runs
read the replay to the end over 40 connections.

The two failed checks, from `grade.json`:

- **Check 4** (one month's county totals add up to state totals and to the source total). The oracle
  map answered with a reconciliation table (`county_diff`, `state_diff`) for September, and the grader
  reads the county, state and source totals of the month it names. The answer came back empty
  (`counties: {}`, `total: 0.00`). The marts hold the figures; the map does not expose them in the
  shape the check reads. No seeded trap matches (`unexplained`).
- **Check 5** (edits and net bytes per wiki and actor type). Three wikis are short by a few events:
  en.wikipedia bot 3,213 against 3,218, human 6,426 against 6,435; es.wikipedia human 569 against
  573; fr.wikipedia bot 934 against 936. The other wikis match. The consumer deduplicates on `meta.id`
  across its 40 reconnects; about twenty distinct events were dropped or never landed. No seeded trap
  matches.

The process record (`context/`): a nine-phase plan, five plan-review cycles that ended at the cycle limit
with `READY WITH CHANGES` and the open findings carried into the plan, the entry-invariant marker,
nine phase commits in plan order, `outputs/PR.md` and `outputs/summary.md`. Then the run recorded a
hard stop of class `credentials`: "No GitHub remote and no PR number. R1 (pr-review-local) and the
draft-PR record need a PR URL." So R1, R5 and R7 did not run, and the delivered code had no review.

Tool measures (`quality_metrics.json`, `commit_replay.json`):

| Measure | Value |
|---|---|
| Lines added in `pipeline/` | 341 |
| Cyclomatic complexity, functions newly over 10 | `stream.py:consume` 14, `stream.py:_sse_events` 12 |
| Cognitive complexity, functions newly over 15 | `consume` 26, `_sse_events` 23 |
| New bug-class findings / new type errors | 0 / 2 |
| Code smells per 100 new lines | 2.3 |
| Duplicated lines on new code | 0% |
| Maintainability index | 70 |
| New-code coverage | not measured: the run's three test files fail to import under the measurer's environment |
| Commits | 9; largest 224 lines and +49 complexity (phase 6, the stream consumer); median 0 lines (the dbt phases add SQL, which the Python measures do not read) |

The quality gate fails on complexity (two stream functions) and on the unmeasured coverage. The
clean-room check reports ten "contacts"; all are shell variable names, Cadence's own text
(`.cursor/plans`), or tokens such as `/` and `2>/dev/null`. None is a real contact, as in the pilot.

### P2-cadence-core-haiku-1 (cut off by the host: an infrastructure loss, not a scored run)

This run is recorded, not scored. The host ran the arm under the runner's 7,200 s guard, and
[criteria v2 §5.3](../method/criteria-v2.md#53-caps-and-the-run-set-budget) gives harness arms no
time cap: "a harness run is never cut off". A session ended from outside is an infrastructure loss
under §5.3 and is run again ([#48](https://github.com/jtouley/harness-benchmark/issues/48)). The grade
below is what the grader read of the tree the agent left, kept for the record.

The timeline, from the transcript and the commit dates (UTC):

| Time | Step |
|---|---|
| 04:46 | Activation, local ticket, plan-create |
| 04:50 to 05:07 | Five plan-review cycles. Each returned `READY WITH CHANGES` with three to five new must-fix items. The loop ended at the cycle limit with the open findings carried into the plan (682 lines, five plan updates). $0.15 of the run's $0.65 |
| 05:07 to 05:22 | Phases 1 to 8 committed: engine, batch ingestion, dbt foundation, star schema, batch checks, stream source and sink, event time and lateness |
| 05:22 to 05:59 | Phase 9 (stream dbt models), with a clean 90-second stream run and a rebuild of the batch side |
| 06:00 | The orchestrator started the plan's acceptance step as `make stream DURATION=3600` under one run id, killed the consumer after a minute, restarted it for the remaining 3,540 s, and waited in 110-second slices |
| 06:46 | The guard cap (7,200 s from the start) killed the session, 14 minutes before the run would have ended |

Phase 10 never ran. It would have exported the six check views to `out/marts/`, written
`outputs/summary.md` and `outputs/PR.md`, and started E4 and R1. The plan did not fix the acceptance
run at one hour: it says `DURATION=<s>` and notes that a shorter run covers a shorter window. The hour
was the orchestrator's own reading of "the replayed hour" in the issue. No hard stop was recorded,
and the host wrote no result.

What the grader found, from `grade.json`: both builds gave the same outputs; both stream runs read the
replay to the end over 10 connections (21,503 positions served of 11,774 needed). Check 7 (the late
event count) passes from the `late_events` table. Checks 1 to 6 fail with the same message: "no
published mart named `v_check…` under `out/marts/`". The oracle map names six dbt views under
`transform/models/checks/`, which exist in `out/warehouse.duckdb` but were never exported.
`out/marts/` holds three marts. So the six answers are unread, not wrong or right.

Tool measures (`quality_metrics.json`, `commit_replay.json`):

| Measure | Value |
|---|---|
| Lines added in `engine/` | 696 |
| Cyclomatic complexity, functions newly over 10 | `config.py:_check_names` 15, `stream.py:StreamConsumer.run` 16, `StreamConsumer._commit` 13 |
| Cognitive complexity, functions newly over 15 | `_check_names` 22, `run` 28, `_commit` 17 |
| New bug-class findings / new type errors | 1 / 3 |
| Code smells per 100 new lines | 1.3 |
| Duplicated lines on new code | 2.2% |
| Maintainability index | 59 |
| New-code coverage | not measured: the run's seven test files fail to import under the measurer's environment, as on P1 |
| Commits | 9 phase commits and the snapshot; largest 321 lines and +83 complexity (phase 7, the stream source and sink); median 38 lines |

The quality gate fails on complexity, on the bug finding, on the type errors and on the unmeasured
coverage. The clean-room check reports 29 "contacts"; all are shell variable names, Cadence's own
paths, or the task's own folders (`data`, `transform`). None is a real contact.

### P1-cadence-core-haiku-2 (hard stop at P9, no code)

The rerun on Cadence `f734888`, the commit that adds the local PR record under `adapter: none`. The
record was never reached. Timeline (UTC): 06:49 activation; 06:50 plan-create; 06:54 to 07:09 five
plan-review cycles, each `READY WITH CHANGES` with new must-fix items (MF-1 to MF-19 over the five
reviews); 07:10 to 07:13 three plan-update runs after the fifth review, to carry the open items;
07:13 the orchestrator ran the entry invariant after each, got the same failure three times, recorded
a hard stop of class `retries`, and ended. 25 minutes, $0.30, no commit. The grader found no
`oracle_map.yml` and no build target.

The failure, from the review and the gate output: the fifth review listed three open items (MF-17 to
MF-19) under `## Must-fix items`, and named seven earlier ids elsewhere: two as applied in a status
list, two in the notes, two under "checked and found sound", one cited inside another item's text.
The P9 gate read every `MF-n` in the file as open and asked the plan to map all ten. The three plan
updates mapped the three open ones each time. The orchestrator did not write the mapping itself
("the gate needs the peer's output"), which is the rule. The defect is the gate's, not the model's.
Fixed in Cadence `f6011df`: the gate reads the open ids from the review's must-fix section,
and only the items labelled there. On this run's review the fixed gate asks for MF-17 to MF-19,
which the plan carries, so P9 would have passed.

The tool measures have nothing to read (no lines added). The clean-room check reports 19 contacts:
variable names, Cadence's own paths, `uv` cache paths, and a dlt source path the plan-create peer
read under the virtual environment. None is a real contact.

### P1-cadence-core-haiku-3 (the whole pipeline ran; the answers were never published)

The third P1 run, on the gate fix (`f6011df`). It is the first run of the core on this family that
went through every block: plan, five review cycles (limit again), the entry invariant, nine
implementation phases, the local PR record under `adapter: none`, five rounds of the local PR
review (R1) with a fix commit after each of the first four, closure (R5: `must_fix: 0`), and the
session summary (R7). No hard stop. 102 minutes, $0.90 at list price (planning $0.12,
implementation $0.23, review rounds $0.28, the rest activation and closure).

The grade is 0 of 7. The cause, corrected after the owner's review (#55): `oracle_map.yml` names
seven `chk_*` dbt views that exist only in `out/warehouse.duckdb`. The spec says downstream reads only
`out/marts/`, and the grader's message for every check is "no published mart named `chk_…` under
`out/marts/`". The two marts the run did publish are single files at the top of `out/marts/`
(`mart_obligations_monthly.parquet`, `mart_edit_windows_5min.parquet`), which the checks would have
read (`oracle.py` registers a single-file mart). So the answers were never published, not published
in the wrong shape. The run-twice check did fail on the shape: it digests folders only, and with none
it reports `idempotent: false`, a grader inconsistency logged as
[#49](https://github.com/jtouley/harness-benchmark/issues/49). The single files follow the spec's own
stack note (dbt-duckdb `external` with no location writes one file per model), which contradicts its
publish rule ([#57](https://github.com/jtouley/harness-benchmark/issues/57)). The first Haiku run
wrote seven folders and passed five checks on the same spec. By its own acceptance record, this run's
batch answers match the key (checks 1 to 3: the total, the top county, 1,122 awards); they were in
the warehouse, not under `out/marts/`. Both of the grader's stream runs read the replay to the end
over 5 connections.

What the review rounds did instead: the nine must-fix items over four rounds were all about the
stream consumer's handling of odd input (non-event JSON, a silent stream, field types, event-time
and integer ranges, a namespace that fits the staging type), each fixed with a test. The review's
end-to-end walk ran the unit suite and two probes and did not run `make build`; no round read the
spec's publish rule against `out/marts/`. The review rigor contract asks for an end-to-end walk of
each check; the reviewer walked the code paths, not the delivered files.

A process note: the nine phase commits all carry the same timestamp (08:28:00). The orchestrator did
the implementation in one 40-minute stretch and then wrote the commits in one shell command, one per
phase, from the finished tree. The commit replay therefore shows phase-sized commits (largest 638
lines, +105 complexity, the stream consumer) that were not phase-sized work.

Tool measures (`quality_metrics.json`):

| Measure | Value |
|---|---|
| Lines added in `pipeline/` | 1,348 |
| Cyclomatic complexity, functions newly over 10 | `stream_consumer.py:run` 18, `_read` 15, `_parse_event` 11 |
| Cognitive complexity, functions newly over 15 | `run` 34, `_read` 23 |
| New bug-class findings / new type errors | 1 / 16 |
| Code smells per 100 new lines | 1.3 |
| Duplicated lines on new code | 0% |
| Maintainability index | 58 |
| New-code coverage | not measured (the same import failure as the other runs) |

The consumer that four review rounds hardened is also the function that grew to 34 cognitive
complexity. The clean-room check reports 23 contacts, all variable names and Cadence's own paths.

The audit trail (criteria v2 §4.7), checked against the lockfile row, Cadence's code and the run's
full `.context/` (#55):

| Declared item | Found for run `c3e98618` | Note |
|---|---|---|
| Plan | `context/plans/open-data-pipeline_gh-1.plan.md` | |
| Spec check (P9 marker) | absent at the end; present in the transcript's listings from 08:28 to 09:05 | Session close (R7) removes this run's marker by design (`activate_session.py`, cd-76 D3). The row now says so |
| Plan review | `context/reviews/plan_open-data-pipeline_gh-1.md` (cycle 5; earlier cycles only in the transcript) | |
| PR review | `context/prs/reviews/PR_REVIEW_local.md` (round 5) | |
| PR record | `context/prs/draft-pr-c3e98618….md`; the PR text at `outputs/PR.md` | The row declared `PR-<id>.md` only; corrected to both names |
| Findings ledger | absent | R1 listed its items in the review file; the ledger exists only when findings go through `findings_io.py` |
| Closure record | `context/summaries/gh-1-session.md`, names head `c6ab925` | The delivered head is `7becba4` (phase 9 was committed after the summary) |
| Attestation | `context/attest/c3e98618….jsonl` and six siblings | Now committed for all four runs |
| Adversarial review, deferral log | not in the core (null) | |

Peer handoffs, from the four transcripts: 55 Agent calls, every one a one-line slash command (longest
165 characters, a path). The handoff logs under `context/handoff/` are committed.

### P1-cadence-core-haiku-4 (ADR-0009: two review cycles; cut off during the R1 fix round)

The fourth P1 run, on Cadence `4af76ac`, the commit that limits plan review to two cycles and routes
mechanism gaps to tests ([ADR-0009](https://github.com/jtouley/cadence/blob/ccr-3d2e0c73-lr6bdt/docs/adr/0009-edge-cases-go-to-tests-two-review-cycles.md)).
It is recorded, not scored: the operator's shell limit (two hours) ended the session at 00:49, 92
seconds before the run's own guard would have, while the orchestrator was fixing the first R1 round.
The same §5.3 rule as for the P2 run applies (#48). The grade below is what the grader read of the
tree the agent left.

The process record, which is what this run was for:

| Time (UTC) | Step |
|---|---|
| 22:51 to 23:01 | Plan, two review cycles, two updates. Ten minutes, against 19 to 20 minutes and five cycles on the earlier runs. Cycle 2 returned three must-fix items, all tagged `[requirement without a phase]`, and five `## Tests to write` lines |
| 23:01 to 23:55 | Seven implementation phases, each a commit. Plan-update had copied the review's test lines into the phases as `Tests from review`; the phase commits carry 15 tests, among them `test_marts_published.py` |
| 23:55 | E4 under adapter none: the branch pushed to the local origin, the PR text at `outputs/PR.md`, the local PR record written. R1 started as a peer |
| 23:55 to 00:49 | R1 returned `CHANGES REQUESTED` with five must-fix items, the first a real defect (the stream consumer stalls at event 15,839). The orchestrator was fixing when the session was cut |

What the grader found: both builds gave the same outputs, both stream runs read the replay to the
end, and `out/marts/` holds six published folders, among them the check views. Every check fails
with one message: `oracle_map.yml` is not valid YAML. Three `how:` lines hold an unquoted string
with a colon in it ("Singular test: transform/tests/…"), which YAML reads as a second mapping key.
The file has been in that state since the phase 6 commit at 23:46. The run's own
`test_marts_published.py` checks the six published folders by name and never reads the map, so its
15 tests passed; the R1 round caught five other things and not this one. A diagnostic regrade with those three strings quoted (not a result) is recorded below when it lands.

Tool measures: 1,063 lines added in `pipeline/`; `oracle.py:main` 19 cyclomatic and 18 cognitive,
`stream.py:consume` 16 and 33; no new bug finding, 7 new type errors; duplication 1.1%;
maintainability index 69; coverage not measured, as on every run. Commit replay: 8 commits, the
largest 337 lines, median 147; the phases were committed as the work went, two to fourteen minutes
apart. Peer calls: 6, all one-line slash commands.

### P1-cadence-core-1 (Opus, no delivery)

The orchestrator activated, wrote the local ticket and called the plan-create peer with
`run_in_background: false`. The host started it as a background task anyway: this container sets
`CLAUDE_AUTO_BACKGROUND_TASKS=true`, which the first runner inherited. The orchestrator explored the data,
then ended its turn. The stop guard answered "peer is still running; resume when it returns" and allowed
the stop, which is its design (ADR-0002). In headless mode that ended the session, and Claude Code
stopped the peer ten minutes later ("Background tasks still running 10m after the last turn"). The
runner now sets `CLAUDE_AUTO_BACKGROUND_TASKS=false` and `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`;
so does `runner/claude-agent.sh`. 17 minutes, $1.96, no plan file.

## What this round says

1. **A harness lifted the cheap model on P1.** Haiku 5.5 alone: 0 of 7 ($0.30). Haiku 5.5 with the
   ten-block core: 5 of 7 ($0.67, 51 minutes). The two misses are an oracle-map reading and about
   twenty stream events, not a missing pipeline. One run; it shows the direction, not a rate.
2. **The lift came from plan, review loop and phase commits, not from code review.** The run stopped
   before R1 because the environment has no PR. The two delivered defects are the kind R1 asks for
   (an end-to-end walk of each check, adversarial inputs on the stream).
3. **The core needs a no-PR mode for a benchmark environment.** `draft_pr_gate.py` wants a PR URL and
   R1 wants a PR number. The pilot's environment note ("continue as if it succeeded") did not get the
   orchestrator past that; it recorded a hard stop instead. A local PR record (a file path in place of a
   URL under `adapter: none`) lets the review stages run. Added in Cadence `f734888`; the rerun on it
   stopped at P9 (below), so the record is still untested on this family.
4. **Headless hosts need two environment variables** (above). Found by the first run, fixed in the
   runner and in Cadence's quickstart.
5. **The tool measures work on this task family** and show what the reviewer would have found: two
   stream functions over both complexity limits, the whole consumer in one 224-line commit.
6. **The P2 run was cut off by the host and is not a result.** Nine phases were committed in 72
   minutes, after 20 minutes and five review cycles of planning. The orchestrator then started a
   one-hour acceptance run, and the host's 7,200 s guard, which criteria v2 does not allow on a
   harness arm, killed the session 14 minutes before it ended. The export step never ran. Under §5.3
   this is an infrastructure loss to run again without a cap (#48). "The replayed hour" came from
   the task's own prompt, so the run length was not the harness's invention.
7. **The plan-review loop hit its cycle limit on all three Haiku runs.** Five cycles each time, every
   verdict `READY WITH CHANGES`, and each cycle found new must-fix items in the text the previous cycle
   added. The limit, not the reviewer, ended the loop. On P2 that cost 20 minutes and $0.15 of the
   run; on the P1 rerun, 19 minutes and most of its $0.30.
8. **Two review cycles were enough.** The fourth run, on ADR-0009, planned in ten minutes with two
   cycles, carried the reviewer's test lines into the phases, and reached R1 with the pipeline built
   and published. What it lost, it lost to one unquoted colon in the grader's interface file, which
   none of its 15 tests or its first review round read with a YAML parser, and to the operator's
   shell limit. The review loop is no longer where this arm spends its time.
9. **The P1 rerun died on a gate defect, not on the task.** The entry invariant counted every
   `MF-n` in the review as open, including the applied ones, so no plan update could satisfy it. The
   orchestrator followed the rule (three peer runs, then a hard stop) rather than writing the mapping
   itself. Found by this run, fixed in Cadence `f6011df`. The one run that reached code (P1,
   the first Haiku run) passed the same gate because its fifth review named no earlier ids.
10. **The full pipeline, with the local PR record and five review rounds, scored 0 of 7.** The third
   P1 run is the process record this round was after: every block ran, R1 found nine defects and
   each was fixed with a test. It also shows what that review did not do: hold the delivery to the
   ticket's own sentences. Four rounds hardened the stream consumer against odd input while the seven
   answers stayed as views in the warehouse, unpublished. The 5 of 7 and the 0 of 7 came from the
   same arm, model and spec; the difference is one publish decision that no gate reads. The generic
   lesson for the harness is a requirement list quoted from the ticket, traced to a phase and a proof,
   and gated at closure; a review that reads the benchmark's own paths would tune the harness to the
   test (criteria v2 §2.4), so that is not the ask.

## Limits

- One run per cell, on the host, not in the isolated runner: no clean room, no network isolation,
  Claude Code 2.1.303 (the lockfile pins 2.1.294).
- The P2 run was cut off by a host guard that criteria v2 forbids on harness arms; it is recorded, not
  scored (#48). Its cost comes from the transcript and its tree is the snapshot of what the agent
  left, with six check views built but not exported.
- Two of the three Haiku runs that reached code lost most or all of their checks to unpublished
  answers (views in the warehouse where the grader reads `out/marts/`). The spec states the rule; the
  runs did not follow it. n = 1 per cell cannot say how often it happens. The grader itself reads
  single-file marts for the checks but not for the run-twice check (#49), and the spec's stack note
  steers runs to single files (#57).
- **Prompt hygiene.** The prompts broke criteria v2 §2.3 and §2.4: the ticket was inlined in full
  (the lockfile's `{issue}`), and the pilot's environment note (host paths, "continue as if it
  succeeded", "nobody will answer") was appended to it. The environment belongs in the task image,
  and the request should reach each arm by reference ([#56](https://github.com/jtouley/harness-benchmark/issues/56)).
  Every arm in this round got the same text, so the comparison between arms stands; the comparison
  with a future v2 run set does not.
- **Costs are lower bounds** (above, #51).
- **Transcripts are not committed.** Each run's session transcript (`transcript.jsonl`, 1.8 to 4.2 MB,
  14 MB for the four runs, with the host's absolute paths throughout) stays off the repository. What
  they would show is committed in smaller form: the peer handoff logs and attestation rows under each
  run's `context/`, the per-peer records under `context/subagent-runs/`, and the counts above (55
  peer calls, all lean). The transcripts are kept on the host and can be attached to a request.
- The task repository got a `.cadence.json` (five gated prefixes) that the one-shot repositories did
  not have. It changes nothing for a one-shot.
- The Opus arm has no result: one run died on the host defect, one was interrupted.
- The host-reported cost and the list-price cost disagree by a factor of three for Haiku; the
  list-price column is the one the other rounds use.

## Next

- P3 needs the Docker image.
- Rerun P1 and P2 at n = 3 in the isolated runner, on Cadence `4af76ac` or later, with no time cap on
  the harness arm (#48) and the request handed over by reference (#56). Two of five runs here were
  cut off by a cap or a shell limit; nothing about this arm can be measured until that stops.
- In Cadence: a requirement list quoted from the ticket, traced and gated to closure (the generic
  form of what the third run missed).
- Rerun P1 in the isolated runner with the runner's new environment, n = 3, when a Docker host exists.
- Fix the no-PR mode in Cadence, then rerun so R1 and R5 run on the delivered code.
