# Dispatch item 8: per-check grade and which block produced each answer

Date: 2026-10-25. Read only, no network, no agents. Tags: **[V]** checked with my own tool calls, **[I]** inferred.

## Sources, and their limits

- **Official records have no per-check grade [V].** `hb-audit/runs/<run>/scores.jsonl` holds only `passed`, `reward` and `stream_ok`. `record.json` has no grade log. None of the graded trees has a `refs/graded` ref (`git show-ref`, 13 trees).
- **The per-check source is the regrade** in `scratchpad/v3work/<run>/pin/grade.json` (grader c344bea, the same commit as the official shapes-r2 grading). I read all 13 grade.json files and the git history of each `pin/repo` tree.
  - **That directory was deleted by another process partway through my task.** Everything below comes from tool output I captured before that happened. Re-running this check needs the regrade again.
- **How well the regrade agrees with the official grade [V]:** passed counts match in 12 of 13 runs. The exception is P2 full-6: 3 in the regrade against 2 official, and no official per-check record exists to say which check differs.
- **Scores.** Score is round(reward×7), as the front matter requires. A "pass" below is a check pass, not points: wherever `stream_ok=false`, the reward is 0 no matter how many checks pass.

## Per-check grid (P = pass) [V]

| Run | 1 | 2 | 3 | 4 | 5 | 6 | 7 | passed | stream_ok | Score |
|---|---|---|---|---|---|---|---|---|---|---|
| Oct23 one-shot Haiku | P | . | P | . | P | P | P | 5 | true | 5 |
| Oct23 one-shot Sonnet r2 | P | . | P | . | P | P | P | 5 | true | 5 |
| P1 core-4 | P | P | . | . | . | . | . | 2 | false | 0 |
| P1 core-5 | P | . | . | . | . | . | . | 1 | false | 0 |
| P1 core-6 | P | . | . | . | P | P | P | 4 | true | 4 |
| P1 full-4 | P | P | P | . | . | . | . | 3 | false | 0 |
| P1 full-6 | P | . | . | . | . | . | P | 2 | true | 2 |
| P2 core-4 | P | P | . | . | . | . | . | 2 | false | 0 |
| P2 core-5 | P | P | P | . | . | . | . | 3 | false | 0 |
| P2 core-6 | P | . | . | . | . | P | . | 2 | true | 2 |
| P2 full-4 | P | . | . | . | . | . | . | 1 | false | 0 |
| P2 full-5 | . | . | . | . | . | . | . | 0 | true | 0 |
| P2 full-6 (regrade) | P | . | P | . | . | . | P | 3 (official 2) | true | 2 |

### Failure patterns [V], with causes [I]

- **Check 4 fails in all 13 runs.**
  - In 7 runs `counties` is `{}`.
  - In 4 runs the error is "no month column".
  - In 2 runs (P2 core-6, P2 full-6) the oracle map entry is unusable.
- **Check 3** gets 7918 or 9820 against an expected 1122 in 6 Cadence runs. That looks like counting rows or awards, not awards that are net negative **[I]**.
- **Check 2** fails 9 times. Most fail on "no county column and per-person column": the mart or the oracle map does not expose the column.
- **Stream checks 5 to 7 pass only where stream_ok=true.** Even there, check 5 passes only in P1 core-6 and the one-shots. P2 core-6 and P2 full-6 return values that look like swapped columns **[I]**.
- **P2 full-5** fails all seven checks because its oracle map gives paths where the grader expects mart names.

## Which block produced each passing answer [V]

Method:
1. Resolve each passing check's table through the oracle map and the grade `source`.
2. Walk the dbt `ref()` lineage.
3. Run `git log` on every model in that lineage.
4. Diff every commit made after E1 that touches the lineage.

For stream checks I also ran `git blame` on the consumer lines that handle the cut frame (F5).

- **One-shots:** everything is in a single "working tree" commit. There are no blocks to attribute.
- **Batch checks 1 to 3, all 15 Cadence passes:** the models come from E1 "phase N" commits.
  - Three later commits touch the lineage, and none changes the graded value:
    - P1 core-5 b6ca11f: county names.
    - P1 core-6 2e59ca4 (MF-3): census fallback, in a population path that agency totals do not use.
    - P2 full-4 090fea3: the rounding of per-person values, which check 1 does not read.
- **Stream checks 5 to 7, 7 passes:** E1 phase commits wrote both the marts and the skip for the cut frame.
  - P1 core-6: 210b362.
  - P1 full-6: a65549b.
  - P2 core-6: c3c211c.
  - P2 full-6: 3fbc249, which already caught JSONDecodeError. R1's 677fd15 only widened it to UTF-8 and wrongly shaped payloads.
- **Post-E1 commits in a stream lineage:**
  - P1 core-6 MF-4 (5417b8a): a UTC conversion. It has no effect because the grader container runs in UTC.
  - P1 full-6 cb9e3fc (R1 MF-1): `coalesce(server_name,'UNKNOWN')` in `int_edit_events`. `late_events` filters only on `is_late`, so the check 7 count is probably unchanged **[I]**.
- **No graded pass in any of the 11 runs traces to P3, P4, R1, R2, R3 or deslop.** I cannot tell from the trees whether each phase commit was written by the `/spec-driven` subagent or by the main thread.

## Answer

- **Every passing check in all 11 Cadence runs was produced by E1 phase commits.**
  - The decisions behind them came through A5 or P1, as the postmortem traced for core-6. Note that A5 is outside the core shape the front matter sets.
- **The review blocks changed no graded answer in any run.** The commits I could find after E1 touched graded lineage without changing the graded value.
- **What decides the score is stream_ok.** That comes from E1's handling of the cut frame, and it was right in 5 of 11 runs, each time from E1 alone.
- **This extends the core-6 split to the whole batch.** The correctness-bearing work is E1 (plus the data-model choices it carries). Every other block is cost with respect to the grade.
