# Skill review, dispatch item 4: P1, P3 and P4 (plan-create, plan-review, plan-update)

Date: 2026-10-25. Read only. No network requests, no agents. **[V]** means I checked it with my own tool calls. **[I]** means I inferred it.

Sources:
- The postmortem front matter (doc 4da1cefd-e759, rev 317) and its 04:45 log entry. That entry names #231 as `fix/enforcement-gate` at 4c437ca. #231 contains #228 (9314a61). It does not contain #229 (`fix/speed-slo` 4d36756) **[V]**.
- core-6: `work/scratch/core6.jsonl`, lines 111-363 and the E1 commands.
- P2 full-5 and P2 full-6: the transcripts from `runs-store/blobs` named in record.json (bb173217…, 35500c83…). Line numbers below are 1-based lines of the decompressed JSONL.
- `survive/run2/t1/PR-description.md` (the spec) and `final-review-t1.md`.
- Each skill as it stands at 4c437ca, and at 2100c6e. Between those two commits only `plan-create.md` changed, by gaining `## Entry points`. `plan-review.md` and `plan-update.md` are the same in both **[V]**.

## Q1. How "the replayed hour" became a 3600-second data step [V]

The plan did not invent the 3600-second step. P1 copied it from A5, and P3 then made it a command.

| Step | Where | What happened |
|---|---|---|
| A5 | core6 L111, rewritten at L164 | G-18 [delegated]: "The replayed hour" is not defined. A5 answered it with A-18: "the replayed hour is every edit consumed in the run started with `DURATION=3600`". This is the first appearance of 3600. |
| P1 | L232 | P1 copied A-18 word for word, as `plan-create.md:34-40` tells it to ("Copy each `A-<n>` of the A5 report … as its own list item"). P1's own commands were short: the Phase 6 gate is `make stream DURATION=60`. P1 had also read spec line 56: "Lateness depends on arrival order. A faster replay can change which events are late". |
| P3 | L298 | MF-6 says "Name the step: before `dbt build`, run the consumer directly for `DURATION=3600` against the replay". MF-7 says "a faster replay changes the span", so P3 saw that line 56 applies, but only to what the data means, not to how long the step takes. |
| P4 | L329, L345 | P4 applied MF-6 word for word as a Phase 5 data step and restated A-18 as "the run started with `DURATION=3600`". P4's ledger row (L373) records it. |
| E1 | L689, L756, L1077 | E1 started `--duration 3600` three times and killed one run (L1047). Run 3 is the "data step of record" (L1257). The full replay lands in under 60 s (`final-review-t1.md` L5: "a 60 s `make stream` already landed all 21,502 events"). |

**The skill lines that let this through:**
1. `plan-create.md:34-40` makes P1 copy each A5 item into the plan. The gate checks only the id, but the text gives no permission to change a decision and does not ask P1 to read the item against the spec. So P1 carried the value through.
2. No skill asks what a named command costs. `plan-create.md` asks for "real quality-gate commands" (line 31) but sets no time limit. #231's `## Entry points` table (lines 52-75) covers only the entry points, allows up to 1800 s, and does not apply to data steps or `settled by` checks.
3. `plan-review.md:66` says "name the change, not a direction". That pushes P3 to write a concrete value, and it wrote 3600.
4. `plan-update.md:28-31` says "Apply the review's required changes". P4 has a `trade-off` option, but no rule asks it to weigh the cost of a command.

## Q2. Why P3 did not test the step against spec line 56 [V/I]

- The "Review for" list (`plan-review.md:40-48`) has no item on how long a command takes or how long it waits. Line 56 came up only through "spec gaps", and P3 used it to define the span (MF-7), not the run time **[V]**.
- P3 runs no commands. "This review writes the review file only" (line 58). So P3 had no measured replay time to compare with **[V]**.
- No gate checks it. Once #229 is merged, `supervisor.bound_reason` with `command_max_seconds: 600` will deny the E1 command, but only at E1, after P9 has frozen the plan. The frozen plan would still require 3600 s **[V]** (`cadence.config.json:60`, `scripts/supervisor.py:218-232` on #229). #231 does not have this cap **[V]**.

## Q3. Why the P2 full-5 and full-6 plans named test files that do not exist [V]

**The premise is only half right.** In both runs the file existed when it was planned, or the plan contradicts itself. The cause is that a test moved after P9 froze the plan.

**P2 full-5 (stop: items 5 and 6 name `tests/test_checks.py`):**
- P1's table (L184) named `tests/test_checks.py::test_stream_edits_and_bytes_per_wiki` and the matching test for item 6. E1 created that file (L656) and its tests passed.
- R2 (`/test-benchmark --code`) raised spec-F05 as must-fix, "Layer score 6" (L1638). The fix commit (L1738, `07ce822`) moved checks 5 and 6 to the new `tests/test_stream_checks.py`.
- The plan was frozen after P9 (`SKILL.md:54`), so its table still named the old file and R5 failed (L2063-2188).
- At plan time, P7 had raised the same layer issue only as a nit, also numbered spec-F05 (L376), so P4 did not have to act on it.
- **The actual cause is the R2 fix round, not the plan.** This overlaps item 3: the R2 score floor forced the move.

**P2 full-6 (stop: row 4 names `tests/test_marts_fy2024.py`):**
- P1 (L194) named `tests/test_marts_fy2024.py::test_county_totals_sum_to_state_and_source` in A-6, A-8 and acceptance row 4.
- P4 (L382) answered P7 spec-F01 by writing this in its appended update section: "It moves to `tests/test_marts_real_data.py` … A-6 and A-8 cite this file". It added a new layer table there.
- P4 did not touch the original `## Acceptance checks` table, because `plan-update.md:26` says "Append-only: keep the prior text".
- `acceptance_checks.section_text` reads only the first section headed exactly `## Acceptance checks` (`scripts/acceptance_checks.py:60,153-164`). So the row still pointed at the old file.
- E1 followed the update and created `tests/test_marts_real_data.py` (L676). R5 then failed with "exits 4 (not found)" (L1941).
- **The actual cause is the append-only rule, together with gates that read only the original sections.** Nothing checks that a later section and the table agree.

## Proposed changes (diff against #231 head 4c437ca)

I checked that the diff applies: `git apply --check` succeeds on copies of the four files at 4c437ca. Note that `SKILL.md`'s Review phase is rewritten on #229, so step 2 has to be re-placed when the stack is combined.

```diff
diff --git a/SKILL.md b/SKILL.md
index 1d272f0..8a0f0d0 100644
--- a/SKILL.md
+++ b/SKILL.md
@@ -226,6 +226,8 @@ The run has one code review and one round of fixes (ADR-0028).
 
 1. Run **R1** `/pr-review-local` one time. Check the artifact, the provenance, and the rigor sections.
 2. Do one round of fixes for the must-fix findings. Fix each one, or defer it with a ticket. Set each fixed row to `fixed`, then run `ledger_verify.py`.
+   A fix does not move or rename a test that a row of the plan's `## Acceptance checks` names: the plan is frozen after P9, and R5 runs that row.
+   When a finding asks for the move, set its row to `deferred` with the reason `the acceptance row <n> names <test id>`.
 3. Run **R2** `/test-benchmark --code`. Resolve each HIGH item. Record `adversarial_inputs`.
 4. Run **R3** cognitive complexity. Split each function that the gate names. Fix each `bugs` (ruff) and `types` (mypy) finding that it names.
 5. Do not run a second R1 review after the fix commits. The R1 gate accepts a review of HEAD or of an ancestor of HEAD.
diff --git a/commands/plan-create.md b/commands/plan-create.md
index a0b6c89..3455e2e 100644
--- a/commands/plan-create.md
+++ b/commands/plan-create.md
@@ -40,12 +40,16 @@ RUN_BY_COMMAND: plan-create
    `[delegated]` or `[blocking]` gap of the report gives. Write
    other assumptions as plain text in the section. The heading can have more words, for example
    `## Assumptions and trade-offs`. A table row `| A-<n> | ... |` is also an item.
+   Copy the id, not the words: before you copy an `A-<n>`, read it against the spec. When its decision names a
+   command, a duration or a value that the spec contradicts or does not require, write your reading in the item and
+   add `(P1 changed A5: <reason, with the spec line>)`. The gate checks the id only.
 5. Add a `## Reuse and extension` section (`core:dry-extension`).
    Name the existing helpers and modules that the plan reuses.
    Name the extension point that the plan adds or uses.
    When the plan adds none, write `None` and the reason.
 6. Add a `## Acceptance checks` section. See "Acceptance checks" below.
    Add a `## Entry points` section. See "Entry points" below.
+   Add a `## Command cost` section. See "Command cost" below.
 7. Footer: next step is `/plan-review <plan>`. Do not tell the user to
    `/plan-update` before a review file exists.
 
@@ -74,6 +78,27 @@ The row fails when the command exits nonzero, prints a traceback, connects 3 or
 `Last-Event-ID`, or leaves an output with no data.
 When the ticket names no `make` command and the change has no entry point, write the line `No entry points.`
 
+## Command cost
+
+Write one row for each command in the plan that runs for a set time or waits: a `DURATION`, `--duration`,
+`SECONDS`, `timeout`, `sleep`, or a run that reads a service until it stops.
+This includes data steps, phase quality gates and the `settled by` checks of `## Assumptions`.
+
+```
+| Command | Seconds | Why this long |
+|---|---|---|
+| `uv run python -m app.consumer --duration 60` | 60 | spec line 17: a replay of a recorded capture; it ends in less than 60 s |
+```
+
+- `Seconds` is the wall time of one run. Use the shortest value that gets the output the check needs.
+- `Why this long` quotes the spec line that sets the time. A spec phrase that names a span of data ("the replayed
+  hour", "a day of events") is not a wall-clock time when the spec says the input can run faster than real time.
+  Then read the input to its end, and do not wait for the clock.
+- No row is over 600 seconds. A spec that needs more gets the row `deferred: <spec line>` and E1 runs a shorter
+  check.
+
+When the plan has no such command, write the line `No timed commands.`
+
 ## Acceptance checks
 
 The ticket text is the file `.context/tickets/<ticket>.md`.
@@ -97,6 +122,9 @@ A numbered line indented under an item is part of that item.
 - `Item` is the number of the item in the ticket.
 - `Ticket text` quotes words of that item, as the ticket writes them. Quote at least three words or 15 characters. Do not restate the item.
 - `Check` is one of three forms: a command with a test runner, a test id (`tests/x.py::test_y`), or a file and an assertion (`<path>: <text>`).
+- A test id names the file that holds the test at R5, not only at E1. Put the test in the file of its layer
+  (unit, fixture, real data, end to end) now: after P9 the plan is frozen, and a later move of the test fails R5.
+  Use one file for each test. A phase, an `A-<n>` item and this row name the same file.
 - Do not put `|` in a cell.
 
 When the ticket has no numbered item, write the line `No numbered items.` in the section. Write no table.
diff --git a/commands/plan-review.md b/commands/plan-review.md
index 665d78f..c41458f 100644
--- a/commands/plan-review.md
+++ b/commands/plan-review.md
@@ -44,6 +44,12 @@ On Claude Code, write this file with the Write or Edit tool, not a shell redirec
 - The `## Reuse and extension` section of the plan
 - `core:standalone-package` (host path leaks)
 - TDD + commit checkpoints + real quality gates
+- The `## Command cost` section, and each command of the plan that runs for a set time or waits. Read each
+  time against the spec lines on the input, for example "the replay can run faster than real time". A wall-clock
+  time that the spec does not require, or a row over 600 seconds, is a must-fix item. Name the shorter command.
+  A must-fix item that you write does not add such a command either: give its `Seconds` and its spec line.
+- Test ids: each `## Acceptance checks` row, each `A-<n>` `settled by` and each phase name the same file for
+  one test. A must-fix item that moves a test names each row and item that it changes.
 - Weakened assertions or partial-success tests
 - Rollback / blast radius
 
diff --git a/commands/plan-update.md b/commands/plan-update.md
index 5fe8b00..a15edb4 100644
--- a/commands/plan-update.md
+++ b/commands/plan-update.md
@@ -25,6 +25,13 @@ An id in a note, or outside that heading, is not open.
 
 - Append-only: keep the prior text. Add a dated update section that records what
   changed and why. Start it with the heading `## Plan update <YYYY-MM-DD>`.
+- Exception: the gates and E1 read three sections where they are, not in the update section:
+  `## Acceptance checks` (the first section with this heading), the `A-<n>` items of `## Assumptions`, and
+  `## Entry points`. When a finding changes a row or an item there, change it in place. Record the old text and the
+  new text in the update section. A test that moves gets its new file in each row, item and phase that names it.
+- A change that adds or changes a timed command gets its row in `## Command cost` (`commands/plan-create.md`).
+  When a finding asks for a wall-clock time that the spec does not require, or over 600 seconds, write
+  `trade-off: <spec line>` and put the shorter command in the plan.
 - Apply the review's required changes. Do not silently drop a must-fix.
 - This is the one update of the run (ADR-0028). Answer each `MF-n` in this update: no second review follows.
   For each finding, make the change. Or, when you do not make it, record the finding with its reason:
```

### Why each hunk, and which run it would have changed

| Hunk | Fixes | Evidence it targets |
|---|---|---|
| plan-create step 4, "copy the id, not the words" | P1 can correct an A5 value against the spec. The gate checks only ids, so no gate change is needed. | core-6 A-18 at L232 |
| plan-create `## Command cost` | Each timed command gets a spec line and a 600 s limit, which matches #229's `command_max_seconds`. A phrase that names a span of data is not a clock time when the spec says the input can run faster than real time. | core-6 MF-6 → about 130 min of E1 waiting |
| plan-review "Review for" bullets | P3 checks the cost of each timed command and cannot add a long one itself. P3 also checks that the test-id files agree across the plan. | core-6 MF-6 (L298); full-6 A-6, A-8 and row 4 |
| plan-update in-place exception | P4 changes `## Acceptance checks`, the `A-n` items and `## Entry points` in place, and records the old and new text in the update section. | full-6 L382 → R5 fail |
| plan-create acceptance bullet and SKILL.md fix-round lines | P1 puts each test in the file of its layer from the start. A fix round does not move a test that an acceptance row names; it defers the finding instead. | full-5 `07ce822` → R5 fail |

### Follow-ups that need code (the front matter says rules are "decided by code") [I]

These skill lines are prose until a gate checks them.

1. **`plan_create_gate.py`, P4 gate and P9:** fail when a timed command in the plan has no `## Command cost` row, or when a row is over 600. This can reuse `supervisor.bound_reason` from #229.
2. **P4 gate and P9:** fail when an acceptance row's test name (`::name`) appears anywhere else in the plan with a different file path. This would have caught full-6 at P4.
3. **`acceptance_checks.py pass`:** when a test id is not found, print where the name lives (`pytest --collect-only -q | grep ::name`). That makes the failure clear. It does not pass the row.
4. **The R2 floor (item 3):** a layer finding whose fix would move a test that an acceptance row names should not force a re-score.
