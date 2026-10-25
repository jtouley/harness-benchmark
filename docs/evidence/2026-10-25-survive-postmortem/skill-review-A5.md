# Skill review, dispatch item 7: A5 (`skills/vibe-test/SKILL.md`)

Date: 2026-10-25. Read only. No network requests, no agents launched, nothing pushed.
Tags: **[V]** means I checked it with my own tool calls. **[I]** means I inferred it.

**Question (dispatch item 7):** do A5's assumptions reach the plan, and do they change E1? Across 11 runs, A5 took 22 peer minutes.

**Short answer.** Yes, both. A5's `A-n` lines reach the plan in every run, nearly word for word, and the gates enforce that by code. E1 then builds on them: core-6's DECISIONS.md cites A-3, A-6, A-11, A-12 and A-18. But no stage after P1 checks an assumption against the rest of the spec, against its cost, or against the failure inputs. So A5 also passes defects and cost on to E1. In core-6, one A5 assumption (A-18) caused about 130 of E1's 153 minutes. Four more A5 assumptions are the design behind H2, M2, M6 and M7. The skill text in #231 is the same file as in 2100c6e, #228 and #229 (same sha1), so no open PR changes any of this.

## Sources

- The front matter of the postmortem doc (Claude Docs project eface3ec…, rev 317). I read it from the start to "Part 1". Relevant lines:
  - "A5 is part of every run … its assumptions go into the plan."
  - "Ambiguity: Cadence does not stop or ask … documents well the assumptions and trade-offs."
  - "The Cadence orchestrator only runs the manifest … does not write, summarize or do block work itself."
  - #231 is `fix/enforcement-gate` @4c437ca (log, Oct 25 04:45).
- `postmortem-weaknesses.md`: dispatch item 7, plus the sections "Which blocks buy correctness" and Q3.
- cadence in `/home/user/cadence`:
  - `git show <rev>:skills/vibe-test/SKILL.md` at 2100c6e, 9314a61 (#228), 4d36756 (#229) and 4c437ca (#231). All four have the same sha1, 3fdc516.
  - At 4c437ca: `commands/plan-create.md:34-42`, `commands/plan-review.md:41-42`, `commands/spec-driven.md`, `scripts/vibe_gaps.py`, `scripts/gate_common.py:354,380`, `scripts/artifact_requirements.py:1377` and `SKILL.md:262-265`.
  - Local `main` (ad5d9e8) is stale. `origin/main` is 2100c6e.
- Transcripts:
  - core-6: `work/scratch/core6.jsonl`, sha 870ecb7c… (1-based line numbers).
  - The other 10 runs: `work/runs-store/blobs/*` via each `record.json`. I extracted them to scratch and have since deleted them.
- `core6.git` at 998515a (DECISIONS.md), `t1/PR-description.md` (the spec) and `t1/final-review-t1.md`.

## 1. Do the assumptions reach the plan? Yes, by code [V]

- The P1 gate (`gate_common.py:380`) and the P9 gate (`artifact_requirements.py:1377`) call `vibe_gaps.carry_problems`. A plan fails while any `A-n` of the report is not its own item under `## Assumptions`.
- What I measured, per run. Last A5 peer report, then the first plan Write:

| Run | A-n in A5 report | Carried by the first plan Write | Blocking gaps |
|---|---|---|---|
| P1 core-4 | 16 | 15 (the plan was edited 6 more times) | 0 |
| P1 core-5 | 10 | 10 | 0 |
| P1 core-6 | 19 | 19 | 1 |
| P1 full-4 | 14 | 14 | 0 |
| P1 full-6 | 12 | 12 | 1 |
| P2 core-4 | 20 | 11 at line 226; 20 when it was rewritten at line 240 | 1 |
| P2 core-5 | 14 | 14 | 0 |
| P2 core-6 | 19 | 19 | 1 |
| P2 full-4 | 14 | 14 | 1 |
| P2 full-5 | 20 | 20 | 2 |
| P2 full-6 | 17 | 17 | 1 |

- The plan items are A5's text, plus a `(settled by …)` test name that P1 adds. Compare core-6, lines 164 and 232.
- **What the gate does not check.** The `settled by` text is free. No gate checks that the named test exists, that the plan's quality-gate command selects it, or that it ran.
- **What E1 is told.** `commands/spec-driven.md` never mentions `## Assumptions`. E1 learns the assumptions only from the phase text that P1 writes around them.

## 2. Do they change E1? Yes. In core-6 they set the design behind most of the reproduced defects

**How the assumptions reached the code [V]:**
- DECISIONS.md @998515a cites A-11 (the place-of-performance columns, line 27), A-12 (the UNKNOWN rule, line 40), A-6, A-7 and A-3 (lines 71-72), and A-18 (lines 103-105).
- The code follows the same assumptions.

**Origin of each issue, A5 report (core6.jsonl line 164) to final review:**

| A5 assumption | Path into E1 | Outcome |
|---|---|---|
| **A-18:** "the replayed hour is every edit consumed in the run started with `DURATION=3600`" (first written at line 111; the line-68 draft had a different A-18) | P1 copied it (line 232). P3 MF-6 then asked for a data step that runs the consumer for `DURATION=3600` (line 298), and P4 added it (lines 329, 345). | E1 ran the consumer for an hour twice: about 130 of its 153 min. The final review's L5 is the resulting "Replay behavior" artifact. The assumption contradicts spec line 56: "The replay can run faster than real time". **The postmortem's Q3 cause 1 names P1, P3 and P4. The origin is A5.** |
| A-1 (`[blocking]` G-1): publish `late_events` as a mart | P1 named the settling test `test_late_events_count`. | M2: that test is never selected, and the published file holds the all-NULL placeholder row. The test name is also R1's unobserved "PASS" (postmortem Q2, cause 2). |
| A-2, A-3, A-4: dedup on `meta.id`, a checkpoint in the lake, high-water mark restored | Taken over by P4 MF-1 and MF-2 (lines 324, 327) and then by E1. | H2: the kill between staging and the checkpoint was never traced. A5 scenario 2 covers only "drops mid-stream". |
| A-6 (`bot` is true means bot) and A-7 (a missing length counts as 0) | Into E1 unchanged. | M6: `bot="false"` lands as a bot, and wrong-typed fields crash the consumer. The assumptions cover a missing value only, never a wrong-typed one. |
| A-11 and A-12: place of performance, and an `UNKNOWN` county or state | Into E1 unchanged. | M7: territories also get state_name `UNKNOWN`. A-12 is "settled by" the self-consistent `test_county_state_source_reconcile`, which feeds M5. |
| A-19: the rerun check compares the marts | Into E1 unchanged. | L2: `check_rerun` covers one mart. |
| (none) | Scenario 1 traces a cold `make build`, never a cold `make stream`. | M1: `make stream` fails on a fresh tree. |

So A5 is where the data-model choices are made, and at present the defects come from the same place. **[I]** The fix is cheap. A5 cost 1.8 min in core-6 and 21.8 min over the batch. A better gap list there costs less than any downstream review round.

**Batch-wide: how A5 read "the replayed hour" [V], from the A5 peer reports**

| Reading | Runs |
|---|---|
| Wall-clock `DURATION=3600` | P1 core-6 only (A-18) |
| An event-time hour or event-time windows | P1 core-5, P1 full-4, P2 core-5, P2 full-4, P2 full-5, P2 full-6 |
| `DURATION` is wall-clock time for consumption only | P1 core-4, P2 core-6 |
| `DURATION` ends the run when the stream closes or the time ends, whichever is first | P2 core-4 |
| No such assumption | P1 full-6 |

- The cost was specific to how core-6's A5 read the phrase.
- **[I]** With no per-check grade (dispatch item 8, reverted 2026-10-25: see README), I cannot tell whether the wall-clock reading helped core-6 score 4/7.

## 3. Correction to the postmortem's "9 of 11 made the geography choice in A5" [V]

- In every one of the 11 runs, the orchestrator first loaded `cadence:vibe-test` with the Skill tool in the main thread (core-6, line 28). It then drafted the whole A5 report itself. The hook blocked the Write: "only a delegated peer writes `vibetest/…`" (core-6, line 69).
  - This took 0.4 to 1.1 min per run, about 7 min across the batch.
  - It is block work by the orchestrator, which the front matter forbids. Nothing in `skills/vibe-test/SKILL.md` tells the main thread to dispatch instead.
- For P1 core-4, core-5 and full-6, and for P2 core-4, core-5, core-6 and full-6, the postmortem's line numbers point to these **blocked drafts**, not to the peer's reports.
- The delegated A5 peer report holds the place-of-performance `A-n` in 5 of 11 runs:

| Run | Peer report line |
|---|---|
| P1 core-4 | 131 |
| P1 core-6 | 164 |
| P2 core-5 | 106 |
| P2 core-6 | 125 |
| P2 full-5 | 118 |

- In the other runs, the first written mention is in a later block:

| Run | First written mention |
|---|---|
| P1 core-5 | E1 `schema.yml`, line 630 |
| P1 full-6 | P6, line 287, then the plan at line 363 |
| P2 core-4 | the plan, line 226 |
| P2 full-6 | P6, line 323, then the plan at line 382 |
| P1 full-4 and P2 full-4 | P6 and E1, as the postmortem says |

- The postmortem's conclusion still holds: all 11 runs chose place of performance, so that choice does not explain the score.
- In core-6, the peer also wrote its report beside the spec (`spec/.context/vibetest/`, line 111), with `Pipeline-Run: none` and the wrong tracker. The gate answered "no artifact matching vibetest/*.md" (line 134), so the report was sent back once and rewritten at line 164.

## 4. "A5 never stops": still true, and the proposals keep it [V]

- At 4c437ca, no stop path exists. `SKILL.md:262-265` and `vibe-test/SKILL.md:60,78-81` say A5 never stops, and `vibe_gaps._gap_problem` returns only "write the report again" reasons.
- One stale code comment says the opposite, `gate_common.py:354`: "a blocking gap stops the run". The diff fixes it.
- core-6's G-1 `[blocking]` passed the gate as a contradiction because both quotes exist (spec lines 28 and 69). It is not a contradiction: one reading meets both lines, and P3's N-3 said so ("the only reading that meets … and also meets check 7"). That is harmless now, but it sends P3 a "contradiction noted" item to review for nothing.
- None of the changes below adds a gate failure or a stop:
  - The new lines are skill text only.
  - A `line <n>: "…"` quote inside a delegated gap is parsed but never fails: the effective class stays delegated.

## 5. Proposed changes: a diff against the #231 head (4c437ca)

What each change answers:
1. The orchestrator dispatches A5 and does not draft it (section 3).
2. The report goes under the repository root (section 3, core-6 line 111).
3. Five domain-neutral scenarios, one each for M1, H2, M2, M6 and M7.
4. An assumption must agree with the rest of the spec and quote the spec line that settles it (A-18).
5. An assumption that sets a run length states its cost (A-18).
6. A field rule covers wrong-typed values (M6). A sentinel value needs a collision check (M7).
7. When one reading meets both quoted lines, the gap is delegated (G-1).
8. P1's `settled by` names a test that the quality-gate command selects (M2).
9. The stale gate comment.

The wording avoids the benchmark spec's text, to keep the contamination fingerprint test clear.

```diff
diff --git a/commands/plan-create.md b/commands/plan-create.md
--- a/commands/plan-create.md
+++ b/commands/plan-create.md
@@ -34,7 +34,9 @@
 4. Add a `## Assumptions` section. Copy each `A-<n>` of the A5 report (`.context/vibetest/`, the
    `[delegated]` and `[blocking]` gaps) as its own list item, `- A-<n>: <decision> (settled by <check or test>)`.
    The item of a `[blocking]` gap starts with the mark: `- A-<n>: contradiction noted: <reading chosen> (settled
-   by <check or test>)`. P3 reviews that choice. Write
+   by <check or test>)`. P3 reviews that choice. Name a test or check that a phase's quality-gate command
+   selects, so its pass shows in that command's output. When the `A-<n>` sets a run length or a wait, copy
+   its cost in minutes from the A5 report. Write
    `None.` when the report carries none. The P1 gate and P9 fail while an `A-<n>` of the report is not its
    own item there, or the item of a blocking gap has no mark. They also fail on an `A-<n>` item that no
    `[delegated]` or `[blocking]` gap of the report gives. Write
diff --git a/scripts/gate_common.py b/scripts/gate_common.py
--- a/scripts/gate_common.py
+++ b/scripts/gate_common.py
@@ -351,7 +351,7 @@
         root = Path(__file__).resolve().parent.parent
         # cd-93 D8: every report A5 accepts also has its header judged.
         errors.extend(marked_report_header_errors(context_dir, root, session, accept=accept))
-        # F-11: each gap is classified; a delegated gap carries an assumption; a blocking gap stops the run.
+        # F-11: each gap is classified; a delegated or blocking gap carries an assumption; no gap stops the run.
         errors.extend(vibe_gaps.gate_problems(context_dir, accept, session))
     errors.extend(
         require_lean_delegation(context_dir, spec.get("delegation_stage", spec["label"]))
diff --git a/skills/vibe-test/SKILL.md b/skills/vibe-test/SKILL.md
--- a/skills/vibe-test/SKILL.md
+++ b/skills/vibe-test/SKILL.md
@@ -10,9 +10,14 @@
 
 Load `$CADENCE_HOME/references/peer-contract.md`.
 
+In a Cadence run, only the delegated A5 peer does this work. When this skill loads in the
+orchestrator's main thread, do not read the spec or draft gaps: dispatch the A5 peer with
+`/vibe-test <ticket>` (`references/delegation.md`) and continue the run.
+
 ## Deliverable
 
-Write `.context/vibetest/{slug}_{YYYY-MM-DD}.md` on the first Write. Use the Write tool,
+Write `.context/vibetest/{slug}_{YYYY-MM-DD}.md` under the repository root: the folder that
+holds `.cadence.json` and the active session. Do not write it next to the spec. Use the Write tool,
 not a shell command. The hook attests a Write or an Edit. It denies a shell write to a
 report (#78). Do not write over a report that exists. When the file exists, write
 `{slug}_{YYYY-MM-DD}-rev{N}.md` with the first free `N` from 2. Include:
@@ -24,7 +29,21 @@
 
 A free-floating chat is not a target. Snapshot what is available to `.context/proposals/`,
 document the assumption, and continue. Trace realistic scenarios through the spec. Flag gaps, conflicts, and
-missing exit criteria. Close with C.O.R.E. pointing at the file. When a Cadence run delegates this peer, replace the C.O.R.E. close with the one-line return in `peer-contract.md`.
+missing exit criteria.
+
+Trace these scenarios as well, for each entry point the spec names. Each one that the spec does not
+settle is a gap:
+
+- A fresh clone runs the entry point first, before any other entry point has made its outputs.
+- The process is killed between two steps of one write, for example after data is staged and before
+  the position or state is saved. Then it starts again.
+- The input is empty, so an output table has no rows. Say what the published file holds.
+- One input record is malformed or has a field of the wrong type (a string where a number or a
+  boolean is expected). Say whether the run skips it, and what the row holds.
+- A value falls outside the set that the spec names (a code with no name, a region that is not a
+  state). Say where it goes.
+
+Close with C.O.R.E. pointing at the file. When a Cadence run delegates this peer, replace the C.O.R.E. close with the one-line return in `peer-contract.md`.
 
 ## Ticket line
 
@@ -74,8 +93,18 @@
 ```
 
 - `[delegated]`: the spec asks for a recorded decision or leaves a choice open. Write the decision as a nested `A-<n>` line. P1 carries each `A-<n>` into the plan under `## Assumptions`.
+- Before you write an `A-<n>`, read the whole spec for a line that already settles the question or limits the
+  choice. When one exists, take its reading and quote it in the `A-<n>` line (`per line <n>: "<words>"`). An
+  assumption that another spec line contradicts is wrong. For example, when the spec measures time from the
+  data and not from a clock, a span that the spec names is a span of data time, not a wall-clock run length.
+- When an `A-<n>` sets a run length, a wait or a data volume, write its cost in minutes. Choose the cheapest
+  reading that the spec allows.
+- When an `A-<n>` reads a field, say what a missing value and a wrong-typed value do. When it adds a sentinel
+  value such as `UNKNOWN`, say why no real value can have that label.
 - `[non-blocking]`: a note for P1. Nothing to carry.
 - `[blocking]`: the task is impossible or the spec contradicts itself. Quote the two spec lines that clash, each as a nested `line <n>: "<words>"` item with its line numbers. Copy the words exactly: the gate looks for each quote on that line of the spec. A blocking gap does not stop the run. Choose one reading, and write it and the reason as a nested `A-<n>` line. P1 carries it under `## Assumptions` marked "contradiction noted", and P3 reviews the choice.
+- When one reading meets both quoted lines, they do not contradict each other. Class the gap `[delegated]` and
+  write that reading as its `A-<n>`.
 - A blocking gap without two quotes that the spec holds at their line numbers is a choice, not a contradiction. The gate treats it as delegated: give it an `A-<n>` line. A one-shot run makes that choice and goes on, so a Cadence run does too.
 
 No A5 failure stops the run. The gate `scripts/validate_gate.py` fails on a malformed report, and the peer writes it again.
```

## 6. Open points (not settled here)

- **The skill-creator eval.** The front matter requires one for review skills only. This is a block skill, but the same approach would apply.
  - Re-run A5 alone on the stored P1 and P2 specs, before and after the change.
  - Score the new reports on two things: whether the five scenario gaps appear, and whether the replayed-hour reading agrees with spec line 56.
  - This costs no full benchmark run.
- **The `settled by` check.** Section 1 found that no gate checks the named test. A code check that the named test is selected (`dbt ls` / `pytest --collect-only`) belongs to the P1 gate or the R5 gate. That is dispatch item 1's area (selection proof), so I wrote no code for it here.
- **The other ten runs.** I traced the A5 to E1 path end to end only for core-6. For the other ten runs, I checked only how the A-n lines carried into the plan and where the replayed-hour and geography choices were written.
