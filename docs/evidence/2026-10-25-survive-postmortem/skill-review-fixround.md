# Skill review, dispatch item 2: the core-6 fix round

Date: 2026-10-25. Read only. No network requests, no agents. Tags as in the postmortem: **[V]** checked with my own tool calls, **[I]** inferred.

## Question and inputs

Dispatch item 2 asks: did each fix commit fix the class or only the named instance, and what rule wording drives that?

Inputs I read:
- `work/scratch/core6.git`, range `76ed6c8..998515a`.
- The R1 review, which is the Write at `core6.jsonl:1570`: MF-1 to MF-9, N-1 to N-7, and its `## Lookback` classes.
- The R2 rows at `core6.jsonl:2103-2113`.
- `survive/run2/t1/final-review-t1.md`, sections M6 and L2 and the other findings.
- The skill text at the pin 2100c6e and at the branch heads.
- The front matter, rev 305 in `work/pm_plain.txt`.

Points to keep in mind:
- **Commit count.** The range holds **15** commits, not 12: 13 `fix(...)` commits and 2 `test:` commits **[V]**. I graded all 15.
- **The reviewed tree is the fix head.** The outside reviewers' tree `t1/tree` @736d6fe has the same files as 998515a, minus `.cadence.json` (`ls-tree` diff) **[V]**. So the final-review findings apply to the fix head.
- **Which branch is #231.** The local refs give no PR numbers, and I made no GitHub call.
  - I took #231 to be `fix/enforcement-gate` @4c437ca. It is the Oct 25 branch off #228, pushed at 03:15:12, next to `feat/antagonistic-review` at 03:15:10 **[I]**.
  - `commands/pr-review-update.md` is byte-identical on main, #228, #229, #231 and the antagonistic branch, blob d1647d2 **[V]**.
  - `SKILL.md` lines 219-235 (the Review phase) are the same at #231 as at the pin.

## Answer

**Mostly the named instance.**
- 6 of the 15 commits fixed only the named instance. One of them later regressed another fix.
- 7 fixed the whole class, but in 5 of those the class has a single instance or is a gate's own list.
- 2 are follow-ups that clean up after earlier fix commits.

The instances that were left are four of the outside reviewers' findings: M6, the silent-exit half of H1, M2 and L2. Two LOW findings, L4 and L6, are new defects that fix commits introduced.

| Commit | Item | Class per R1 `## Lookback` | Fixed | Evidence [V] |
|---|---|---|---|---|
| acd9d90 | MF-1 | Input validation at the ingest edge for typed fields | **Instance** | `_field_problem` checks the 4 cases MF-1 lists: `length`, `timestamp`, `length.old`, `length.new`. It does not check `type`, `wiki`, `server_name`, `namespace`, `bot`, `meta.id`, int64 bounds, `HTTPException` or the utf-8 decode. All of these come back as **M6** ("one malformed event crashes the consumer on every restart"). The test covers exactly the 4 named cases. |
| 979609b | MF-2 | Silent success on missing input | **Instance** | The check is for the USAspending README zips only. The same class in the stream consumer, `except OSError: return` (`stream_consumer.py:159` @998515a), is left. R1 had it as nit N-3 ("not probed"). R2 reproduced it in this run (`core6.jsonl:2090-2091`: "offline run returned normally, exit=0") and did not file it. It comes back as the silent exit 0 in **H1** (HIGH). |
| 2e59ca4 | MF-3 | Spec drift through a DECISIONS entry | Instance, new defects | The CT fallback is right. The test asserts one code (09001) of the six. The fix keeps the 2021 values in `population_2024` (new **L4**), and DECISIONS says "six" where 8 rows landed (**L5**). |
| e5047c5 | MF-7 | Gates not run before the PR | Class (1 instance) | `__init__.py` markers; the class has one instance. |
| 82d2913 | MF-6, MF-9 | Gates; a helper copied, not shared | Class, as R1 scoped it | S608 bound. `read_ids` and `DLT_COLUMNS` deduplicated. R1 had accepted the other duplicates as oracles. |
| 8fff1b6 | MF-8 | Weak assertions that accept partial success | Instance, **later regressed** | Strengthened the named test only. 30fe1d1 then removed its count assert. At 998515a, `tests/test_stream_consumer.py:122-124` asserts only uniqueness and `raw == sent[:len(raw)]`, so zero landed events passes. That is weaker than the `> 0` assert R1 flagged. The test file is the same in the reviewed tree **[V]**. |
| 5417b8a | MF-4 | Host-dependent behaviour in a UTC column | Class (1 instance) | `git grep to_timestamp` @998515a finds the single site. |
| 4b4ef0d | MF-5 | Missing key tests on published marts | Class as stated | Both marts now have key tests. The sibling class "a declared test that no runner selects" is left: **M2** (check 7 is never selected) and **M3** (dim_date's key tests never run). |
| f00c921 | R3 types | The gate's list | Class (gate list) | Fixes the 12 mypy findings the gate named. |
| 35a2dcf | MF-6 follow-up | — | Cleans up after 82d2913 | Removes the RUF100 noqa that 82d2913 added. |
| 30fe1d1 | R2-F01 | Non-deterministic live test | **Instance, regression** | Removed the completeness assert instead of making the test deterministic (see MF-8 above). |
| 7c9cc90 | R2-F02 | Row counts for every batch table | Class | Census 2024, Census 2021 and sitematrix were all added. |
| 75b8993 | R2-F03 | A check that no runner runs; mixed layers | **Instance, new defect** | Wrapped `check_rerun.py` in unittest. The same class in dbt, `test_late_events_count`, is left (**M2**). The wrapper runs `make build` twice in the real repo root inside the unit suite (new **L6**). That is the layer mixing R2-F03 itself complained about. |
| 492adc6 | test | Partial-success thresholds | Class (sibling) | Replaced the `> 0` assert in the sibling `stopAtDuration` test. |
| 998515a | test | Load columns for every table | Class | Every lake table, including the 2021 one. |

**L2** is the clearest case of an instance that sat next to a fix:
- R1 found both halves: N-1 (`any_value`) and N-5 ("check_rerun compares mart_monthly_obligations only").
- Both went to `## Follow-ups` as nits, under ADR-0009 and `pr-review-local.md:64-65`.
- 75b8993 then edited the same `check_rerun.py` and left `MART_GLOB` on one mart.

## What drives it (rule wording)

1. **`commands/pr-review-local.md:40`, the same at the pin and at #231:** "So write each must-fix item so that one fix commit can settle it, and name the test that proves the fix."
   - The unit of an item is one commit and one test.
   - R1 complied. Every MF has one `Fix:` and one `Check:` test for the reproduced case. MF-1's check lists the four cases it probed.
   - The fixer then wrote exactly those tests.
2. **ADR-0028 Consequences:** "No reviewer reads the fix commits. `ledger_verify.py` runs each finding's check."
   - The row closes when the instance's test passes. `ledger_verify.py:33` only promotes `fixed` rows **[V]**.
   - So a `verified` row is never re-run, and a later weakening goes unseen. A re-run would not have caught it anyway: MF-8's weakened test still passes.
3. **`references/review-rigor.md:96-100` (#231):** "Name the failure class … After fixes land, re-run the suite and every matrix on the combined tree, then re-read the combined diff adversarially."
   - The class is named in `## Lookback`, but no field carries it into the must-fix item.
   - The post-fix pass has no owner. SKILL.md:229 says "Do not run a second R1 review", and R4 is off.
   - R1 wrote this down itself: "Post-fix pass: not yet due … which R4 or R5 runs." R5 is `closure.py`, which is code.
4. **`SKILL.md:228` (#231):** "Do one round of fixes for the must-fix findings. Fix each one …".
   - It names no peer and no contract. SKILL.md:63 says `/spec-driven`, but the Review phase does not.
   - The orchestrator wrote a free-form brief: "Keep each fix small … add the test the Check line names first" (`core6.jsonl:1597`).
   - The lean-peer hook rejected the brief (1598). The orchestrator then did the whole fix round in its own thread (1603: "I'll do the fix round in this thread"). This breaks the front-matter line "the orchestrator … does not write, summarize or do block work itself".
   - All 15 commits, including R2's fixes, were made by an agent that no reviewer checked.
   - #229's SKILL.md step 3 names "one `/spec-driven` peer". #231 does not.
5. **`commands/spec-driven.md:34` (rule 2, bug-fix mode):** "write a failing reproduction test first, then the fix."
   - The rule is per instance, and nothing in it forbids loosening an earlier assertion.

## Proposed skill text (diff against the #231 head, 4c437ca)

Under the front matter, these are review-skill revisions:
- They are built with skill-creator and scored against the current version on existing diffs.
- The `pr-review-local.md` hunk is a part of /pr-review-local. It merges only where it beats both baselines (the current /pr-review-local and the built-in code-review skill) by more than run-to-run variance, without breaking the speed SLO.

A proposed eval:
- Replay the fix round from 76ed6c8 with the R1 review.
- Count how many of {M6, the H1 silent exit, M2, L2, L6, the MF-8 regression} survive. The current text leaves all 6.
- Also count the fix-round minutes.
- This is n=1, so add other runs' R1 reviews before trusting a delta.

```diff
diff --git a/SKILL.md b/SKILL.md
--- a/SKILL.md
+++ b/SKILL.md
@@ -225,8 +225,10 @@ adversarial inputs, and tests each design choice three ways with strict TDD.
 The run has one code review and one round of fixes (ADR-0028).
 
 1. Run **R1** `/pr-review-local` one time. Check the artifact, the provenance, and the rigor sections.
-2. Do one round of fixes for the must-fix findings. Fix each one, or defer it with a ticket. Set each fixed row to `fixed`, then run `ledger_verify.py`.
-3. Run **R2** `/test-benchmark --code`. Resolve each HIGH item. Record `adversarial_inputs`.
+2. Do one round of fixes: one `/spec-driven` peer for the must-fix findings, in one Agent call. The orchestrator does not fix them itself.
+   The peer fixes the class of each finding, not only the named line (`commands/spec-driven.md`, Fix round). Defer a finding with a ticket when it cannot be fixed.
+   Set each fixed row to `fixed`, then run `ledger_verify.py`.
+3. Run **R2** `/test-benchmark --code`. Resolve each HIGH item with the same `/spec-driven` peer and the same Fix round rules. Record `adversarial_inputs`.
 4. Run **R3** cognitive complexity. Split each function that the gate names. Fix each `bugs` (ruff) and `types` (mypy) finding that it names.
 5. Do not run a second R1 review after the fix commits. The R1 gate accepts a review of HEAD or of an ancestor of HEAD.
diff --git a/commands/pr-review-local.md b/commands/pr-review-local.md
--- a/commands/pr-review-local.md
+++ b/commands/pr-review-local.md
@@ -37,7 +37,15 @@ Last reviewed commit: <full sha of the reviewed head>
 
 The run has one code review (ADR-0028). After this review, the orchestrator makes one round of fixes for the must-fix items. No second review follows.
 `pr_review_local_gate.py` fails while the last `Last reviewed commit:` line of the newest review is not HEAD of the run's worktree or an ancestor of HEAD.
-So write each must-fix item so that one fix commit can settle it, and name the test that proves the fix.
+So write each must-fix item so that one fix commit can settle its failure class:
+
+- `Class:` the failure class, in the words of its `## Lookback` line.
+- `Search:` the command that finds the other instances of the class in the diff (a `grep`, a `dbt ls`, the list of entry points), and what it found.
+  Every instance it found is part of the item. An instance you did not reproduce is still listed, marked `not reproduced`.
+- `Check:` one test that runs over every instance, one case each (a parametrized test or a subTest loop). Show that the runner selects it
+  (`pytest --collect-only`, `dbt ls --resource-type test`).
+
+A finding under `## Follow-ups` in the same class as a must-fix item moves into that item.
 
 Staff review: contracts, blast radius, `core:dry-extension`,
 `core:standalone-package`, test quality (no partial-success thresholds),
diff --git a/commands/pr-review-update.md b/commands/pr-review-update.md
--- a/commands/pr-review-update.md
+++ b/commands/pr-review-update.md
@@ -39,7 +39,8 @@ python3 "$CADENCE_HOME/scripts/pr_threads.py" <PR>
    When the JSON has `truncated: true`, the PR has more than 100 threads: write the first 100 and add
    the line `Review threads: truncated at 100`.
 3. Review every commit from that commit to HEAD (`git log <last>..HEAD`, `git diff <last>..HEAD`).
-   Check that each must-fix finding is fixed and that the fixes add no new defect. Reproduce each claim.
+   Check that each must-fix finding is fixed for its class: run its `Search:` again on HEAD, and run its `Check:` over every instance.
+   Check that the fixes add no new defect and remove no assertion that an earlier commit added. Reproduce each claim.
 4. Append to `.context/prs/reviews/PR_REVIEW_#{N}.md` a section `## Update <date>` with:
diff --git a/commands/spec-driven.md b/commands/spec-driven.md
--- a/commands/spec-driven.md
+++ b/commands/spec-driven.md
@@ -35,6 +35,17 @@ Do not reset the branch to change the history. E1 records one-shell commits as a
 3. Mock at the process or network edge, never the module under test, because a test of a mock does not test the code.
 4. A test name names the behavior, never a connector, a customer or a ticket, because the name tells the reader what broke.
 
+## Fix round
+
+In the fix round, the input is the review's `## Must-fix items` and the R2 and R3 findings. The output is `.context/prs/fixes_round1.md`.
+
+1. Fix the class, not the line. Run the item's `Search:` command again on HEAD. Fix each instance it finds, in one commit for the class.
+2. Write the item's `Check:` as one test over every instance, one case each. Make each case fail before the fix.
+3. Do not remove or loosen an assertion that an earlier commit of the run added. A test that fails on timing is made deterministic, not weaker.
+   `git diff <reviewed commit>..HEAD -- <test paths>` must remove no assertion. When it does, say so in the report as an open must-fix.
+4. After the last fix commit, do the post-fix pass of `references/review-rigor.md` (`## Lookback`): the suite, every must-fix check and every class search on HEAD.
+   An instance that the pass finds is fixed in this round, or listed in the report with its reason.
+
 ## Output checks
 
 A gate asserts on output, not on exit code. This applies to a phase gate of the
diff --git a/references/review-rigor.md b/references/review-rigor.md
--- a/references/review-rigor.md
+++ b/references/review-rigor.md
@@ -95,9 +95,12 @@ changes? Give the file count, and recommend a split when concerns are mixed.
 
 ### `## Lookback`
 
-Name the failure class behind each finding, not just the bug. After fixes
-land, re-run the suite and every matrix on the combined tree, then re-read the
-combined diff adversarially and record what that pass found.
+Name the failure class behind each finding, not just the bug, and the search
+that finds its other instances. The must-fix item carries both
+(`commands/pr-review-local.md`). R1 runs one time, so the post-fix pass belongs
+to the fix-round peer: after the last fix commit, it re-runs the suite, every
+must-fix check and every class search on the combined tree, and records what
+that pass found in its fix report.
 
 ### `## Reuse and extension`
```

The full hunks, with index lines, were generated with `git diff --no-index` from `git show 4c437ca:<path>` copies. They apply to the #231 head.

## Open points (not in the diff)

- **Enforcement by code.** Under the front matter, the rule should be enforced by code, not by prose. Two script changes would do that:
  - `pr_review_local_gate.py` fails on an MF item that has no `Class:`, `Search:` or `Check:` line.
  - A closure check fails when the fix commits remove an `assert`, `self.assert*` or dbt test line from a test path between the reviewed commit and HEAD. That check would have caught 30fe1d1.
- **The lean-peer hook.** It accepts only a one-line `/command <args>` (`core6.jsonl:1598`). The fix-round dispatch is then `/spec-driven <review path>`. The `spec-driven.md` argument hint names a plan path, and I did not check whether the hook or the E1 gate takes a review path.
- **Conflict with #229.** #229 reorders the Review phase: R2 and R3 run before the one fix peer. If #229 merges first, rebase hunk 1 onto its step 3 ("one `/spec-driven` peer for the must-fix findings of R1, R2 and R3"). Keep the class sentence.
- **Item 1's ground.** `review-rigor.md:6` ("If you can't reproduce a finding, drop it") is why N-3, the offline silent exit, became a nit. That is dispatch item 1's and item 7's ground, so it is not changed here.
