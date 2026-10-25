# Skill review R1: was each core-6 finding in R1's reach, which rule let it through, and do #228/#229/#231 close it

Date: 2026-10-25. Read only. No network requests, no agents. Dispatch item 1 of `survive/postmortem-weaknesses.md`.

## Answer

- **26 of the 30 finding items were in R1's reach.** The 30 items come from the 15 headings of `final-review-t1.md`, split at their sub-bullets. The log's "28" grouping is not written down anywhere, so I itemized. R1 had the code, the spec and the local replay. The exceptions:
  - H1's 403 needed the live Wikimedia host, which the rules forbid. Its silent exit 0 was in reach.
  - L6a was added by R2-F03 after R1.
  - L6d is reasoned only and cannot be reached.
- **R1 touched 8 of them but cleared or downgraded them:**
  - N-1, N-2, N-3, N-5 and N-6 were filed as nits.
  - MF-1 named the instance, not the class.
  - MF-3 asked for the year column, which the fix did not add.
  - Step 4 claimed that `test_late_events_count` passed.
- **The rule lines that let them through (pinned 2100c6e):**
  - `review-rigor.md:6`: "If you can't reproduce a finding, drop it."
  - `:24-26`: list the steps and whether each cleared.
  - `:30-33`: an adversarial-input list written for Cadence's own CLI.
  - `:37-39`: Contracts checks Cadence's own docs, not the spec.
  - `pr-review-local.md:40`: one fix commit per item.
  - `:44`: "must-fix vs nits", with no severity rule.
  - `:64-65`: open nits go to Follow-ups.
- **#228 and #229 close none of the 30.** Their R1 text is byte-identical: the walk table and "assert on output". That change targets the stream-loop and crash failures of other runs, and core-6's consumer did not have them.
- **#231 (`fix/enforcement-gate` @4c437ca) closes none either.** The log identifies #231 as this branch. `feat/antagonistic-review` is not #231.
  - **It hides M1.** `clean_checkout.py` runs the Makefile `build`/`test`/`check` targets first. It then runs the plan's entry points in that same built checkout (`_check_entries`). So `make stream` never runs on a fresh tree.
  - **It passes M2's placeholder.** `entry_points.output_problems` checks only that a file is larger than 0 bytes. The one-row all-NULL parquet passes.

## Per finding

Reach: Y means R1 could reproduce it locally with what it had. Gap is the pinned rule line that let it through. All three PR columns are "no" except where noted.

| Finding | R1 saw? | Reach | Gap (2100c6e) | #228/#229 | #231 |
|---|---|---|---|---|---|
| H1 silent exit 0 on connect failure | N-3 "Not probed; read from code" | Y (closed local port). 403: N (network) | rigor:6, pr-review:44, :64-65 | no | no: the sse row targets the working replay only |
| H2 kill between dlt normalize and load loses events | no; Contracts says "Met by the tests and by the two live runs" (clean stops) | Y | rigor:30-33 (no kill class) | no | no: an entry is killed only at its limit and never restarted |
| M1 `make stream` fails on a fresh tree | no; walk ran build first (steps 1 then 3) | Y | rigor:24-26 (doc order). The rigor:33 "never ran" case covers hooks only | no | **masks it** (build runs first) |
| M2a check-7 test never selected | claimed PASS in step 4. In R1's tool results the name appears only at lines 1429, 1451, 1455, 1461 and 1531, never in dbt output | Y (`dbt ls`) | rigor:24-26 | no: the gate strips status words, so "PASS=12 including …" passes | no |
| M2b empty mart publishes an all-NULL row | no | Y (short run, 0 late) | rigor:30-33 (no empty-input class) | no | **passes it** (size > 0) |
| M3 dim_date never built | no | Y | rigor:37-39 (no spec trace) | no | no |
| M4a stream lake drops source fields | no | Y | rigor:37-39 | no | no |
| M4b batch lake retypes strings | no | Y | rigor:37-39 | no | no |
| M5a check 4 not answerable from marts | step 6 "Cleared by reading" | Y | rigor:24-26 (reading clears a step) | no | no |
| M5b oracles share the models' macro | Reuse §2 "oracles by design … accepted" | Y | none requires independent oracles | no | no |
| M6 other malformed fields crash the consumer | MF-1 named `length`/`timestamp` only; Lookback named the class | Y | pr-review:40 | partly: the fault-repeat rule exists, but the replay has no such events | no |
| M7 territories labelled UNKNOWN | listed the 7 codes in MF-3 | Y | rigor:37-39 | no | no |
| L1 NULL key duplicates window_5min | no | Y | rigor:30-33 | no | no |
| L2a any_value | N-1 nit | Y | pr-review:44, :64-65 | no | no |
| L2b rerun check covers one mart (spec rule) | N-5 nit, though Contracts line 109 says "Not checked" | Y | pr-review:44 (no spec-line severity) | no | no |
| L3a `--duration=60` ignored | no | Y | rigor:30-33 | no | no |
| L3b empty URL path | no | Y (reading) | rigor:30-33 | no | no |
| L3c deadline overrun | N-2 nit | Y | pr-review:64-65 | no | no |
| L4 population column holds 2021 values | MF-3 asked for "the year used"; the fix dropped it | Y | fix round (dispatch 2) | no | no |
| L5a cites spec.md and A-/G-/N- ids | no | Y | rigor:37-39 | no | no |
| L5b "six" CT codes; there are 8 | R1 repeated "six" | Y | rigor:37-39 | no | no |
| L5c transactions counted as awards | no | Y | rigor:37-39 | no | no |
| L5d replay-hour paragraph | no | Y | rigor:37-39 | no | no |
| L5e check-5 wording | no | Y | rigor:24-26 (read, not run) | no | no |
| L5f check-2 DOUBLE | no | Y | rigor:24-26 | no | no |
| L6a test_rerun.py builds in the repo root | n/a | N (written by R2-F03 after R1) | n/a | n/a | n/a |
| L6b canary events in stream_raw | no | Y | rigor:37-39 | no | no |
| L6c dbt deprecation warning | no; it was in R1's own dbt output | Y | none | no | no |
| L6d macro overflow | no | N (reasoned only) | n/a | n/a | n/a |
| L6e cwd-relative paths | N-6 nit | Y | pr-review:64-65 | no | no |

## Proposed skill text, diff against #231 head (4c437ca)

- I checked the diff with `git apply --check` (no offsets) on copies of the 4c437ca files.
- It adds no `###` heading, so `test_review_rigor_doc_lists_the_enforced_sections` still holds.
- Neither file is in the frozen-hash list.
- Side effect: R2's `adversarial_inputs` ("one entry per input class above") grows to the 7 new classes.

```diff
--- a/commands/pr-review-local.md
+++ b/commands/pr-review-local.md
@@ -38,10 +38,16 @@
 The run has one code review (ADR-0028). After this review, the orchestrator makes one round of fixes for the must-fix items. No second review follows.
 `pr_review_local_gate.py` fails while the last `Last reviewed commit:` line of the newest review is not HEAD of the run's worktree or an ancestor of HEAD.
 So write each must-fix item so that one fix commit can settle it, and name the test that proves the fix.
+A must-fix item names its failure class and every instance that you found, with a fix for the class (for
+example: validate the type of every field that the code reads, not only `length` and `timestamp`). Its test
+is parametrized over those instances.
 
 Staff review: contracts, blast radius, `core:dry-extension`,
 `core:standalone-package`, test quality (no partial-success thresholds),
 adversarial scenarios with evidence. Verdict must-fix vs nits.
+Each item quotes the spec line that sets its
+severity (`references/review-rigor.md`). An item that breaks a spec rule or a spec output is a must-fix. It is
+never a nit, and never a follow-up only because you did not reproduce it.
 ## Must-fix items
 
 Put every must-fix item under one `## Must-fix items` heading. Give each item an id: `MF-1`, `MF-2`, and so on.
--- a/references/review-rigor.md
+++ b/references/review-rigor.md
@@ -3,7 +3,14 @@
 Load this for every review stage after TDD and PR creation: resolving **E3**
 architecture findings, the **R1** PR review, and the **R2** test review. The
 reviewer does the verification. Never hand the author "please check whether X".
-If you can't reproduce a finding, drop it.
+Severity and reproduction are two fields. Severity comes from the spec line
+that the finding breaks: quote that line. A finding that breaks a spec rule or
+a spec output is a must-fix, reproduced or not. Try to reproduce it locally
+first (a closed local port, a local stub server, a copy of the input with one
+field changed). Never send a request to a host outside the machine. When you
+cannot reproduce it, write `reproduced: no` and the reason. Do not drop the
+finding and do not lower its severity for that reason. Drop a finding only when
+a reproduction shows it is false.
 
 Background and worked example: [`docs/review-followup.md`](../docs/review-followup.md).
 
@@ -27,6 +34,17 @@
 that the spec names on the input that the spec names. Unchecked test-plan items
 in the PR are yours to run.
 
+Run each entry point first in its own fresh clone of HEAD, before any other
+entry point has run there (no build output, no lake, no data that another
+target makes). The order in the docs is a second walk, not the first.
+
+A row clears only on output that you captured in this review. When a row says
+that a test passed, give the test name and the line of captured output that
+shows it ran, and show that the runner selects it (`pytest --collect-only -q`,
+`dbt ls --resource-type test --select <the same selection>`). A count such as
+`PASS=12` does not name the tests in it. A step that you checked by reading
+is not a walk row: put it under `## Contracts`.
+
 A gate asserts on output, not on exit code. The R1 gate does not read this table to decide on the entry points.
 It reads the clean-checkout record of HEAD (`scripts/entry_points.py`), and a failed entry point is a must-fix
 of the fix round. Write the walk as one table:
@@ -61,10 +79,31 @@
 
 ### `## Adversarial inputs`
 
-For every changed gate, CLI, hook or installer, the result for each input:
-missing, corrupt, another ticket's leftovers, `--resume`, an adjacent id
-(`cd-1` vs `cd-12`), an offline host without `gh`. For hooks and installers,
-also a workspace that never ran Cadence and a user symlink with the same name.
+For every entry point and every changed module that reads input, the result
+for each class below. Write `n/a: <reason>` only when the code has no such
+input. "Not applicable to this CLI" is not a reason.
+
+1. Fresh clone: each entry point alone, with no output of another target.
+2. Empty input: zero records, or a filter that keeps none. Read every
+   published output. A row with a NULL key, or a count that is not 0, is a
+   finding. A file that exists is not proof.
+3. Malformed record: for each field that the code reads, a wrong type, a
+   value out of range, a missing field and a NULL. Send the same fault on each
+   send. Name every field that you tried.
+4. Kill at a stage boundary: `kill -9` between each two steps that write
+   (for example extract and load, load and checkpoint), then start again. Give
+   the input accounting of the restart: nothing counted twice, nothing lost.
+   A clean stop is not this test, and a kill at a random time is not either.
+5. Source unreachable or refusing: a closed local port, and a local stub
+   server that answers 4xx and 5xx. The run must exit nonzero or print the
+   failure. Exit 0 with nothing read and nothing printed is a must-fix.
+6. Command line: each documented option in each spelling (`--x 1`, `--x=1`).
+7. Run twice: the second run changes no output.
+
+For every changed Cadence gate, CLI, hook or installer, also: missing,
+corrupt, another ticket's leftovers, `--resume`, an adjacent id (`cd-1` vs
+`cd-12`), an offline host without `gh`. For hooks and installers, also a
+workspace that never ran Cadence and a user symlink with the same name.
 
 ### `## Contracts`
 
@@ -72,6 +111,13 @@
 A finding that contradicts written design is a decision for the author, not a
 must-fix. List it here with the doc line it contradicts.
 
+Then trace the spec: one line for each output, rule and check in the spec or
+the ticket, with `met` or `not met` and the evidence (a command and its
+output, or a file and line). An output that the spec names and the build does
+not make (for example a dimension that no target selects) is `not met`. Check
+each number and claim in the PR's own decision and mapping documents against
+output that you captured.
+
 ### `## Design choices`
 
 For each finding with more than one reasonable fix (including E3 findings):
```

What each change covers:
- The severity rule covers H1, L2b and L3c.
- The fresh-clone rule covers M1.
- The selection proof covers M2a and M5a.
- The new classes cover H2, M2b, M6, L1, L3a and L3b.
- The spec trace covers M3, M4, M7 and L5.
- The class-not-instance rule covers M6.

Not covered by these changes: L4 (the fix round, dispatch 2), L6a, L6c and L6d.

## Gate code to match (not skill text)

Prose alone does not make R1 do these. Two changes to #231's gate code would:
- In `scripts/clean_checkout.py` `_check_entries`, run each plan entry point in its own fresh clone before the build targets, as well as after them. The ordering is at clean_checkout.py lines 89-112 on 4c437ca.
- In `scripts/entry_points.py` `output_problems`, fail a declared Parquet output that has a row whose columns are all NULL. File size alone is not enough.

A kill-at-boundary probe needs the plan to name its boundaries, so it is a design question. Check the ADRs before raising it.

## Sources
- R1 review: core6.jsonl line 1570 (the Write of PR_REVIEW_local.md, reviewed head 76ed6c8).
- `survive/run2/t1/final-review-t1.md` and `PR-description.md`.
- `git show 2100c6e:` and `fix/enforcement-gate:` for `references/review-rigor.md`, `commands/pr-review-local.md`, `scripts/entry_points.py` and `scripts/clean_checkout.py`.
- `git diff 2100c6e fix/gate-asserts-output` and `fix/speed-slo`.
- The postmortem doc log (rev 317), which names #231 as fix/enforcement-gate @4c437ca.
