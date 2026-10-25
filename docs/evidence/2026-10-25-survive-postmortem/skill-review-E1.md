# Skill review E1: `commands/spec-driven.md`, `references/execution-protocol.md`

Date: 2026-10-25. Dispatch item 5 of `survive/postmortem-weaknesses.md`. Read only. No network requests, no agents.
Tags: **[V]** I checked it with my own tool calls. **[I]** I inferred it.

## Sources

- The postmortem doc front matter (WbaPy7W4Qc2EZL9R68B1oA, node 4da1cefd-e759, rev 317). The log entry from Oct 25 04:45 names cadence#231 as `fix/enforcement-gate`, head 4c437ca.
- The skills in `/home/user/cadence`, local refs only:
  - pinned `2100c6e` (origin/main);
  - #228 `fix/gate-asserts-output` @9314a61;
  - #229 `fix/speed-slo` @4d36756;
  - #231 `fix/enforcement-gate` @4c437ca.
- The 11 shapes-r2 transcripts, from `/home/user/work/runs-store/blobs` through each `record.json`. The core-6 transcript is byte-identical to `work/scratch/core6.jsonl` **[V]**.
- `survive/run2/t1/final-review-t1.md` (H2, M1, M2, M6) and `t1/PR-description.md` (the spec).

**Method.** For each subagent tool call, I took the time from its tool_use to its tool_result, and I put each Bash command in a category by regex. The minutes are measured **[V]**. The categories are a heuristic **[I]**. "Model" is the E1 time when no tool was running.

## Q1. Where did E1's 336 peer minutes go?

The 336 is the sum of the five `/spec-driven` Agent calls that finished: 152.9 + 40.6 + 34.2 + 60.2 + 48.7 = **336.6 min [V]**. They match `record.json` `timing.blocks.spec-driven`. The sixth call, P2 core-4 at line 385, took 43.0 min, but the record marks it `unfinished`. That gives the postmortem's 379.6.

| Run (line of E1 call) | Min | Waits on a running consumer (sleep/poll loops) | pytest | consumer/`make stream` runs | dbt | Cadence gates | deslop/simplify Agent | other tools | Model |
|---|---|---|---|---|---|---|---|---|---|
| P1 core-6 (391) | 152.9 | **116.5** | 0 | 7.0 | 5.4 | 2.1 | 2.8 | 2.3 | 16.8 |
| P1 full-6 (381) | 40.6 | 3.2 | 13.1 | 1.1 | 1.0 | 0.4 | 5.5 | 2.4 | 13.9 |
| P2 core-5 (272) | 34.2 | 0.1 | 6.1 | 2.1 | 1.2 | 0.8 | 3.3 | 3.2 | 17.4 |
| P2 full-5 (434) | 60.2 | 4.5 | 21.8 | 3.8 | 0.5 | 4.9 | 2.1 | 2.5 | 20.1 |
| P2 full-6 (399) | 48.7 | 1.2 | 14.3 | 9.0 | 0.7 | 0.2 | 0 | 5.8 | 17.5 |
| **Sum** | **336.6** | **125.5 (37%)** | **55.3 (16%)** | **23.0** | **8.8** | **8.4** | **13.7** | **16.2** | **85.7 (25%)** |

**Core-6 alone is 45% of the 336.6 [V].** It launched three `stream_consumer --duration 3600` runs, at lines 689, 756 and 1077, and blocked in poll loops on two of them:
- `stream3600b` (12 polls, 54.2 min). Its log showed `skipped an event (data is not JSON)` at 18:37 (line 881). After that, every poll from 18:47 to 19:32 printed the same `1`. E1 killed it at 19:32 (line 1047), after 63 min, because the consumer did not honor DURATION on heartbeats.
- `stream3600c` (9 polls, 60.0 min). It ran from 19:35 to 20:35, then exit=0.
- **Effect:** 114 of E1's 153 minutes were waits on a wall-clock "replayed hour". The spec says this replay "can run faster than real time" (spec line 56). The cause is the plan's 3600-s step (P4, dispatch item 4). E1's contract has no rule against waiting that long, and none against polling a log that has stopped changing.

**Without core-6 [V]:** the four other peers spent 183.7 min, about 46 min each. The largest tool cost is pytest, 55.3 min over 157 runs. Model time is about 17 min per run.

**The other 5 runs, E1 in the main thread [V]:** these are the runs with no `/spec-driven` Agent call.
- P1 core-4, P1 core-5, P1 full-4 and P2 full-4 loaded `cadence:spec-driven` with the Skill tool, inside the orchestrator. P2 core-6 never invoked it.
- Their E1 windows, from the skill call to the next block: about 27, 87, 45 and 27 min, and 44 min for P2 core-6, about 230 min in all **[I: window bounds]**.
- P1 core-5 spent 56.7 min in `kill -0 <pid>; sleep 30` loops on its stream run (lines 1248-1372).
- **Cause:** the pinned `SKILL.md:211` says "The main agent runs **E1**", which contradicts `stages.json` (`command: /spec-driven`). #229 and #231 both rewrite that line so that a peer runs E1, and #231 adds a hook that denies the orchestrator's block work above 60K tokens.

## Q2. Does E1 require a fresh clone per entry point, a crash at stage boundaries, and empty and malformed input?

**No, on every branch [V].** `spec-driven.md` and `execution-protocol.md` at 2100c6e have no such rule. #228 adds the `## Output checks` section, which #231 carries unchanged (the #231 blob is identical to #228's). It covers malformed input only as a behavior ("a counted skip or a dead-letter", rule 3). It does not require a test for it, and it has nothing on a fresh clone, a crash at a boundary or empty input. `execution-protocol.md` is unchanged on all three PRs.

**What E1 actually tested in core-6, against the reproduced defects [V]:**

| Class | Reproduced defect | Closest E1 test in core-6 (test names written in lines 391-1287) | Gap |
|---|---|---|---|
| Crash at a stage boundary | H2: dlt normalize→load loses events | `restartAfterStop_neverCountsAnEventTwice`, `stopAtDuration_landsContiguousPrefix` | Only a clean stop; no kill between the two parts |
| Fresh clone | M1: `make stream` fails unless `make build` ran first | none. E1 only ran `rm -rf lake/stream_*` in the worktree (lines 686, 756, 1077) | No clone, and each target was never run first |
| Empty input | M2: an empty external mart publishes an all-NULL row | `heartbeatsOnly_stopsAtDuration` | Checks the stop, not the published row count |
| Malformed or wrong-typed input | M6: a list-typed `type`, a huge int or a bad status line crashes the consumer on every restart | `eventWithoutTimestamp_landsAndStreamContinues` (a missing field only) | No wrong-type, out-of-range or parse-failure cases |

**Across all 11 runs [V]:** no test file written with Write or Edit mentions a malformed or wrong-typed record. One run (P2 full-6, `sse_server.py`) touches an empty case. The tests with a crash or restart in their names are restart-after-stop tests.

**Does #231's gate fill these gaps? Partly [V]**, from `scripts/clean_checkout.py` and `scripts/entry_points.py` @4c437ca:
- **Fresh clone:** yes, it clones HEAD. But `clean_build` runs the Makefile `build` target first, then the plan's entries in the same checkout ("after the build"). So M1, where `make stream` needs `make build`, still passes.
- **Empty output:** `output_problems` passes any output with a file of nonzero size. M2's one-row all-NULL parquet passes.
- **Crash and malformed input:** it runs only the dev replay, with no kill and no restart. M6 says none of the 21,502 replay events triggers the crash.
- **Conclusion [I]:** these classes need E1 to own them in the skill text now, and they need new gate code later. Under the front-matter rule "decided by code, never from text a model wrote", the text is a stopgap.

## Q3. Does #228's spec-driven change hold?

**Partly.**
- **It holds:** rules 1, 2 and 4 are sound, and nothing in the 11 runs contradicts them.
- **Rule 5 was not followed in the run it describes [V].** The "bad 1"-style line `skipped an event` appeared at 18:37, and E1 then polled for 55 more minutes before it acted. The rule should say to stop the run and write the test.
- **Stale cross-reference on #231 [V].** "R1 reads these counts in its End-to-end walk" contradicts #231's `review-rigor.md`: "The R1 gate does not read this table to decide on the entry points. It reads the clean-checkout record of HEAD." The printed counts feed no gate. The entry observer counts socket reads itself.
- **No bound on duration [I].** Rule 1 says to run "on the input that the spec names", with no limit on time. Read with spec check 5 ("the replayed hour"), it permits core-6's hour-long waits. #229 gives E1 a 75-min budget (`stages.json`). Under that budget, core-6's E1 would be killed partway through the waits instead of not starting them.
- **Conflict with the front matter on #231 alone [V].** #231's "Cadence binding" keeps "Before E2, delegate deslop … Then continue E2→E4 in the same turn". That contradicts "each block writes one document and stops", and #229's binding.
  - `git merge-tree` of #231 and #229 merges `spec-driven.md` cleanly to #229's text. `SKILL.md` conflicts at line 211, where each PR rewrote the E1 line.
  - **Effect:** in the merged stack the binding is fixed, but #231 alone is not. ADR-0030 exists only on #229.

## Proposed change: diff against the #231 head (4c437ca)

`git apply --check` passes on the #231 blob **[V]**.

- **Hunk 2** is #229's binding text plus one sentence. If the stack merges, keep only that sentence, "with one line for each class of Failure inputs".
- **Front-matter fit:**
  - "Long runs" serves the speed SLO: it would have saved about 114 min in core-6 **[I]**.
  - "Failure inputs" targets survivability (H2, M1, M2, M6), and the one-shots share three of these four defects (postmortem Q1).
  - Commands stay inside the E1 subagent, and no orchestrator work is added.

```diff
--- a/commands/spec-driven.md
+++ b/commands/spec-driven.md
@@ -52,9 +52,50 @@
    that sends a malformed record one time and then sends it intact hides a
    retry loop.
 5. Output that you do not expect mid-run (for example a `bad 1` line) is a
-   defect until you prove its cause.
+   defect until you prove its cause. Stop the run at once and write the failing
+   test. Do not wait for the run to end.
 
-R1 reads these counts in its End-to-end walk (`references/review-rigor.md`).
+E4 runs the plan's `## Entry points` in a clean checkout and decides from what
+they did (`scripts/entry_points.py`). R1 reads E4's record. The counts are for
+the reader of Verification; no gate reads them.
+
+## Failure inputs
+
+The dev replay holds no crash, no empty result and almost no malformed record,
+so the entry point gate cannot see these classes. E1 owns them. For each row of
+the plan's `## Entry points`, write a test or a recorded run for each class
+below, and give each one a Verification line with its command and its output.
+
+1. Fresh clone. In a clean clone of HEAD (`git clone` of the worktree, no
+   untracked or ignored files), run each entry point first, before any other
+   target. A target that needs another target's output runs it, or fails with
+   a message that names it.
+2. Crash at a stage boundary. Each step that commits in two parts (stage and
+   load, write and checkpoint, normalize and load) gets a test that stops the
+   process between the two parts (SIGKILL, or an exception raised at that
+   point), starts it again, and asserts that no record is lost or counted
+   twice. A stop at the end of the duration is not a crash and does not count.
+3. Empty input. Run each step on an input with no records. Each published
+   output holds 0 rows. Count a key column (`count(event_id)`), not rows: some
+   writers publish a placeholder row for an empty table.
+4. Malformed and wrong-typed records. For each field that the code reads: the
+   field missing, of the wrong type, out of range, and the record not parseable.
+   Each one is a counted skip or a dead-letter (Output checks 3), and the next
+   start goes past it.
+
+When a class does not apply (no two-part commit, no record input), write the
+class and the reason under Verification.
+
+## Long runs
+
+A duration in the spec is input time ("the replayed hour"). It is not a
+wall-clock wait when the input can run faster than real time.
+
+1. Run an entry point with the shortest duration that reads to the end of its
+   input, and never longer than the `Seconds` of its `## Entry points` row.
+2. Run one long run at a time, and keep working on tests while it runs.
+3. When its log has not changed for two checks in a row, stop it and find the
+   cause. Do not poll it again.
 
 ## Options in a phase
 
@@ -97,14 +138,19 @@
 ## Cadence binding
 
 Before gated source edits, `entry_invariant.py --phase execution` must be
-green. Write `.context/implementation/{task}_stage4.md` when tests pass:
+green. When E2 is in the run's pipeline (`pipeline_status.py`), delegate
+`$CADENCE_HOME/subagents/deslop.md` on the branch in one Agent call after the last phase. In the core and full
+runs, E2 is off, so do not delegate it: R1 reviews the code.
+
+Then write the E1 document `.context/implementation/{task}_stage4.md`, last:
 
 ```
 RUN_BY_COMMAND: spec-driven
 ```
 
-Include Implementation Summary and Verification (each command and the output that it gave). Before E2,
-delegate `$CADENCE_HOME/subagents/deslop.md` on the branch in one Agent call. Then
-continue E2→E4 in the same turn. Do not ask permission to open the draft PR.
+Include Implementation Summary and Verification (each command and the output that it gave), with one line for
+each class of Failure inputs.
+The document ends the block (ADR-0030). After you write it, return `ARTIFACT: <path>` with no other call.
+The orchestrator dispatches E4. Do not ask permission to open the draft PR.
 Do not answer a finished or aborted shell with status only.
 Resume the open cycle in that turn.
```

`references/execution-protocol.md` needs no change for these items.

## Follow-ups that need code, not skill text (for the owner of #231)

The front matter says enforcement is decided by code.

1. **Fresh clone.** `clean_checkout.py`: run each `## Entry points` row in its own fresh clone, before the build, as well as after it. This catches M1.
2. **Empty output.** `entry_points.output_problems`: for tabular outputs (parquet or CSV), require at least one row with a non-null value, not a file of nonzero size. This catches M2's placeholder row.
3. **Crash and malformed input.** `entry_points.py`:
   - Add an optional fault replay: one wrong-typed record and one unparseable frame, injected into the observer's SSE stub.
   - Add a SIGKILL at about half the row's `Seconds`, followed by a second run, then assert that no event is lost or duplicated.
   - This catches M6 and H2.
4. **Evaluation.** Score each change on the 11 stored trees, as #231's commit did for stream_ok. Keep whichever lands as code over the skill text, per the front matter.
