# Postmortem: the first cadence-core round, and how it was reported (19 October 2026)

Status: blameless review, written the same day. It covers four Cadence-core runs on Haiku 5.5 (the
round itself is on branch `ccr-3d2e0c73-lr6bdt`, commit `abb8c07`,
[write-up](https://github.com/jtouley/harness-benchmark/blob/abb8c07/docs/evidence/2026-10-19-pipeline-cadence-core.md))
and the status messages about that round that the owner received from this session. Each finding names the
file that shows it. Where a finding rests on another session's report rather than a file checked here, it
says so.

*Disclosure: the owner of this benchmark wrote Cadence.*

## Summary

The round ran four Cadence-core trials on the pipeline family (P1, P2) on a host, not in the isolated
runner. Scores: 5 of 7, 1 of 7, 0 of 7, 0 of 7. Most of the lost checks are the delivered pipeline's fault
(the model working inside Cadence), one run was lost to a Cadence defect, and one to a time cap that the
pre-registered criteria do not allow for harness arms.

Checking the run records against the code found four defects in this benchmark that the round's write-up
and the status messages did not report:

1. The runner caps every arm at 7,200 s, but criteria v2 says a harness run is never cut off.
2. The grader is inconsistent about marts published as single files: the checks read them, the
   run-twice (idempotence) check does not.
3. Coverage cannot be measured on any pipeline task, and the quality gate counts "not measured" as a
   failure.
4. The cost code ignores Haiku 5.5's higher price for prompts over 100K tokens, so every Haiku cost in this
   repository is at best a lower bound.

None of them changed a score in this round, but 1, 3 and 4 change how results are read, and 2 can
change a score in a future run.

The status messages sent to the owner contained three wrong or conflicting statements: a proposed
criteria change that contradicts the criteria, a cause relayed from another session without checking it,
and a claim that the grader was right in every case before its code had been read. They are corrected
below.

## Impact

- **On main:** nothing published from this round yet. The cost defect affects published numbers: the 15
  October pipeline round on main gives Haiku 5.5 one-shot costs of $0.28 to $0.38 at base prices
  ([pipeline trials](2026-10-15-pipeline-trials.md)).
- **On the round's branch:** the write-up gives one wrong cause (the third P1 run), one unsupported
  claim (its audit trail), a next step that conflicts with criteria v2 (tell the agent its time budget),
  and costs that are lower bounds.
- **On the owner:** three status messages to correct, and a decision (whether to change the criteria)
  that was put to them on a wrong premise.

## What happened

All times UTC, 19 October 2026.

| Time | Event |
|---|---|
| 04:46 to 06:46 | P2 run. Planning, nine phases committed, then the orchestrator started a one-hour acceptance run of its own. The host's 7,200 s guard killed the session 14 minutes before that run would have ended. The export step never ran. Graded 1 of 7 |
| 06:49 to 07:13 | P1 rerun. Stopped at the P9 gate after three plan updates: the gate counted applied must-fix ids as open. No code. 0 of 7. Cadence fixed the gate in `f6011df` (reported by the other session; Cadence's code was not checked here) |
| After the rerun | The other session reported the first three runs. This session relayed them and proposed a criteria change: a run killed by a time cap should count as an attempted run that was not delivered |
| Later (102 minutes; phase commits at 08:28) | P1, third run, on `f6011df`. Every Cadence block ran: plan, five plan reviews, nine phases, the local PR record, five review rounds with fix commits, closure, summary. Graded 0 of 7 |
| 09:20 | The other session reported the third run: "published its marts as top-level .parquet files … where pipetask reads folders", and "every declared path … exists … except the findings ledger" |
| After | This session relayed both claims as facts |
| After | The owner asked whose failure each run was. This session read the grader and found that it does read single-file marts, which contradicted the relayed cause |
| After | The owner pointed out the conflict and asked for this postmortem |

## Findings

### A. This benchmark's defects (confirmed in code on main)

**A1. The runner cuts off harness runs, which criteria v2 forbids.**
[Criteria v2 §5.3](../method/criteria-v2.md#53-caps-and-the-run-set-budget) says "Harness arms have no
per-trial time cap … A harness run is never cut off"; only one-shots keep a guard cap.
`runner/pipeline/caps.json:3` sets `agent_timeout: 7200` and calls it "the one-shot guard cap", but
`runner/entrypoint.sh:77,90` applies it to every arm. `scripts/pipeline_trial.py:116,141` then
records a capped run as `guard_cap` and counts it as a model failure, whatever the arm. The P2 run ran on a host
with the same 7,200 s guard. Under v2 this run could not happen. Had it happened anyway, it would be an
infrastructure loss and run again (§5.3), not a scored run.

The lockfile row for cadence-core says "The exit status of the host is not a signal", so under M3's
wording a session killed from outside "ends as completed" and would count as a false success. The
criteria need one sentence: a session ended from outside the agent (a timeout, a signal, a lost
container) is an infrastructure error under §5.3, not a run that ended as completed. That is the
correct version of the change proposed to the owner earlier (see D1).

**A2. The grader reads single-file marts for the checks but not for the run-twice check.**
`golden/pipeline/pipetask/oracle.py:119` registers a Parquet file at the top of `out/marts/` as a mart,
so the checks read it. `golden/pipeline/pipetask/trial.py:124` digests only folders, and
`trial.py:243` sets `idempotent` to false when there are no folders, which zeroes the reward
(`trial.py:185`). As a result:

- A pipeline that publishes every mart as a single file gets 0, even if all seven checks pass.
- A pipeline that mixes folders and files has its file marts graded but never checked for
  idempotence. That bypasses traps B7 and D2.

This did not change the third P1 run's score, whose answer map named views that were not published at
all (C1). It may have affected earlier pipeline runs. That needs a regrade to rule out.

**A3. Coverage cannot be measured on the pipeline tasks, and "not measured" counts as a failure.**
`scripts/quality_metrics.py:133` runs pytest with `uv run --no-project` and only pytest and coverage
installed, so a task whose tests import its own dependencies (duckdb, dlt) fails at collection. All
three runs that delivered code show this error in `quality_metrics.json` (`tool_errors.coverage`).
The third run's own record says its 30 unit tests pass in its own environment. `quality_metrics.py:417`
then sets the `tests_pass` gate to false. This affects every arm, one-shots included, on any task with
third-party dependencies.

**A4. Haiku 5.5 costs ignore the long-prompt price.**
Haiku 5.5 costs $0.10 / $0.50 per million tokens for prompts up to 100K tokens and $0.50 / $2.50
beyond (Anthropic's model table; `pricing.json` notes this). `scripts/pipeline_trial.py:59-80` prices
every token at the base rate. These sessions read about 240K to 290K cached tokens per turn on average
(34.1M over 140 turns, 46.8M over 159), so many requests were probably above 100K. Claude Code's own
figure is 3.3 times ours on two runs ($2.24 against $0.67, $3.00 against $0.90). On the third it is
about equal ($0.32 against $0.30), so the long-prompt price alone does not explain the gap. The 15 October round put
its host figure down to the host not recognising the model; that explanation was never tested. Until
each request is priced from its own usage, Haiku costs here are lower bounds, and any "cheap model with
a harness" cost comparison is unsettled. The P2 cost was summed from the transcript, which reports
only 2,518 output tokens for a two-hour session; that total also needs checking.

**A5. Commit replay can be gamed, and it does not read SQL.**
In the third P1 run, phases 1 to 8 were committed 0 to 1 s apart from a finished tree
(`commit_replay.json`, `seconds_since_previous`), so the per-commit numbers describe a split made after the fact,
not steps taken. `scripts/commit_replay.py` measures Python only, so the dbt phases show as 0 lines.

**A6. The spec's "(or SQL view)" can be read as a view inside the warehouse.**
[Pipeline spec](../plans/tasks/pipeline-spec.md) line 56 lets `oracle_map.yml` name "the table and
column (or SQL view)", while line 42 says downstream reads only `out/marts/`. The grader follows line
42. To be logged as an open reading. Do not change the spec mid-family: that would break comparison with the
one-shot rows.

### B. Cadence's defects (reported by the other session, checked only against its evidence files)

- **B1.** The P9 gate counted applied must-fix ids as open, so no plan update could satisfy it. Fixed
  in `f6011df`.
- **B2.** The plan-review loop ended at its cycle limit in all three Haiku runs, each cycle finding new
  must-fix items in text the previous cycle added.
- **B3.** The local PR review (R1) walked the code, not the delivered files. Four rounds hardened the
  stream consumer against odd input and raised its cognitive complexity to 34, while the answers were
  never published. No round compared `out/marts/` with the spec.
- **B4.** On P2, the orchestrator chose a one-hour acceptance run that the plan did not require.
- **B5.** Without a PR the first P1 run hit a hard stop (no PR URL for R1). A local PR record was added in
  `f734888`.
- **B6.** The audit trail does not match the lockfile's declaration. The other session reported that
  every declared path exists except the findings ledger. The committed evidence for the third P1 run
  (`context/`) does not support that:
  - no entry-invariant marker for its run id (`c3e98618…`);
  - no attestation file;
  - a PR record at `prs/draft-pr-<id>.md`, where the lockfile declares `prs/PR-<id>.md`;
  - no findings ledger.

  Either the evidence copy is incomplete or the declaration does not match what Cadence writes. M10
  cannot be scored until that is settled.

### C. The delivered pipelines (the model working inside Cadence)

- **C1. Third P1 run, 0 of 7.** `oracle_map.yml` names seven `chk_*` dbt views that exist only in
  `out/warehouse.duckdb`. The spec says downstream reads only `out/marts/`. The grader's message for
  every check: "no published mart named 'chk_…' under out/marts/". The cause is not "single files instead of folders", as the
  round's write-up says: the checks would read single files (A2). The logic was largely right: by
  its own acceptance record, checks 1 to 3 match the answer key exactly ($1,442,017,216.67 in total;
  District of Columbia at $129.07; 1,122 awards). Its stream figures came from its own 60-second run and
  cannot be compared with the key.
- **C2. First P1 run, 5 of 7.** Check 4: the map exposed a table of differences, not the totals the
  check reads. Check 5: about twenty stream events were lost across 40 reconnects.
- **C3. P2, 1 of 7.** Six answer views were built but never exported (B4, A1). They are unread, not
  wrong.

Every run that delivered code built twice without error, and both of the grader's stream runs read the
replay to the end (`grade.json`: `build`, `stream`, `stream_ok`). The pipelines ran; what failed was
publishing and two real defects.

### D. Reporting errors in this session's status messages

| Statement | What is true | Why it was wrong |
|---|---|---|
| "The P2 run exposes a gap in the criteria … a run killed by a time cap … counts as an attempted run that wasn't delivered, as §8.1 already says for one-shots" | Criteria v2 forbids the cap for harness arms (§5.3). The gap is in the runner (A1). The criteria need only a sentence saying an outside kill is an infrastructure error | §5.3 was not re-read before proposing a change to the pre-registered rules |
| "It wrote the output tables as loose .parquet files, but the grader only reads folders … The run-twice check also failed, for the same reason" | The checks read single files. They failed because the map named unpublished views (C1). The run-twice check did fail because it reads only folders (A2) | Relayed from the other session without opening the grader |
| "Every file path Cadence declares for the audit exists except the findings ledger … a missing ledger is a real miss" | The committed evidence lacks three more declared items and has one under another name (B6) | Relayed without listing the evidence folder |
| "In each of the four Haiku runs the grader read what was there and scored it correctly" | Every score this round stands, but the grader is inconsistent (A2), and P2 should not have been capped (A1) | Stated before reading `trial.py` |
| "Killed the run during a stream step" next to "both stream runs read the replay to the end" | The first is the agent's own one-hour run during its session. The second is the grader's two runs afterwards. Both are true | One phrase used for two different things |
| Costs quoted as exact ($0.67, $0.65, $0.30, $0.90) | Lower bounds (A4) | The price table's own note about the long-prompt price was not checked against the cost code |

The common cause: claims from another session were treated as checked data and passed on in this
session's voice. The other session's message was a summary; the files it summarised were on a branch this session
could read and did not read until asked.

### E. The task design: the pipeline family grades its own interface more than the pipeline

Sections A to D look at this round. The pattern across both pipeline rounds points at the task
design itself.

| Lost checks | Cause | Runs |
|---|---|---|
| Most of Haiku's | The map names warehouse tables or dbt views that were never published | All four Haiku deliveries: one-shot P1, P2, P3 (15 October), cadence-core third P1 run |
| 6, one per run | Check 4 answered as a reconciliation; the key grades rows (an open reading) | All six Sonnet and Opus one-shots |
| 4 | Check 2's county reading (an open reading) | Four of the six Sonnet and Opus one-shots |
| 15 lost by the three cadence-core runs that delivered code | 7 publish or map, 6 never exported (time cap, A1), 1 check-4 reading, 1 pipeline defect | 19 October |

Two diagnostics show the computation was often right when the score said otherwise. On P2 (15
October), Haiku's map edited by hand scored 3 of 7 instead of 0. The cadence-core third run's own
record has checks 1 to 3 matching the key exactly; it scored 0.

**Why.** The pipeline tasks are greenfield from a prose spec, and the interface between grader and
delivery (`oracle_map.yml`, one folder per mart under `out/marts/`, "or SQL view") exists only in that
prose. Nothing in the repository shows the convention, and no tool the agent has can check it before it
delivers. In a real team the convention lives in the repository (where marts go, model contracts,
tests), and `dbt build`, `dbt test` and CI check it. So the family measures "followed a contract it
could not see, and guessed two readings" about as much as "built a correct pipeline". That holds for
every arm, so comparisons are not void. But at one run per cell, the noise is larger than any difference.

**What follows.** Keep P1 to P3 as they are; changing the spec mid-family would break comparison. Add a
brownfield family on an existing public dbt project, where the conventions are in the repository and
the grader reads the model the task names, with no oracle map:

- `dbt-labs/jaffle_shop_duckdb` is Apache-2.0, self-contained on DuckDB, with a `uv.lock`. Its seeds
  are about 100 rows each.
- `dbt-labs/jaffle-shop-generator` (`jafgen`, Apache-2.0) generates years of data. No seed option was
  found, so generate once, freeze the files and record their hashes.
- `dbt-labs/jaffle-shop` has no LICENSE file at `5beb145`, requires dbt 2.0 and targets dbt Cloud. Do
  not use it unless the license is clarified.
- Risk: jaffle shop is in every model's training data, so tasks must be new work with hidden checks.

The grader also needs fixtures for every delivery shape it has met, so that a gap like A2 fails CI. A
second correct solution per task is already an open item of criteria v2.

## What went well

- The grader's answer key made the third run's failure precise: the computed answers can be compared
  with the key even though the checks never read them.
- The other session committed the full evidence for every run (grade logs, oracle maps, session
  records, cost files), which is what made every correction here possible.
- The Cadence defects found by the runs were fixed and re-pinned the same day.
- The host reproduced the reference solutions' 7 of 7 before any harness run was scored.

## Action items

Logged on 19 October after checking every open and closed issue (#3, #11, #28, #41 and #44 read in full)
for duplicates.

| # | Action | Owner | Issue |
|---|---|---|---|
| 1 | Runner: no time cap on harness arms; an outside kill is an infrastructure error; one sentence in criteria v2 §4.1 and §5.3 | Benchmark | [#48](https://github.com/jtouley/harness-benchmark/issues/48) |
| 2 | Grader: single-file marts read the same way by the checks and the run-twice check; regrade | Benchmark (choice: owner) | [#49](https://github.com/jtouley/harness-benchmark/issues/49) |
| 3 | Coverage in the task's own environment; "not measured" is not a failed gate | Benchmark | [#50](https://github.com/jtouley/harness-benchmark/issues/50) |
| 4 | Cost: per-request pricing with Haiku's long-prompt rate; explain the host figures | Benchmark | [#51](https://github.com/jtouley/harness-benchmark/issues/51) |
| 5 | Commit replay: flag commits split after the fact; name files not measured | Benchmark | [#52](https://github.com/jtouley/harness-benchmark/issues/52) |
| 6 | Brownfield dbt family on jaffle shop; log "(or SQL view)" as an open reading | Owner decision, then benchmark | [#53](https://github.com/jtouley/harness-benchmark/issues/53) |
| 7 | Golden grader fixtures for every delivery shape met so far | Benchmark | [#54](https://github.com/jtouley/harness-benchmark/issues/54) |
| 8 | Correct the round's write-up before it merges | Other session | [#55](https://github.com/jtouley/harness-benchmark/issues/55) |
| 9 | Cadence: review from the delivered files; audit paths against the lockfile; the plan-review loop that always reaches its limit | Cadence | Drafted in [cadence issue drafts](2026-10-19-cadence-issue-drafts.md); not filed, as this session has no access to `jtouley/cadence` |
| 10 | Status messages: check a restated claim against its file first, or label it "reported, not checked" | This session | — |

Already tracked, not filed again: the second correct solution per task (#41), computing each check
under every reading the spec allows (#28, from #18), cache-write pricing as a lower bound (#28, from #19).

## Limits of this review

One run per cell, on a host without isolation. Cadence's code was not read; B1 to B5 rest on the
other session's report and the evidence files it committed. The cost gap (A4) is not explained, only
bounded.
