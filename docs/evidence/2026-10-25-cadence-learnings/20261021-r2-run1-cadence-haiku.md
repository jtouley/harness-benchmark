RUN_BY_COMMAND: run-learnings
Run: 20261021-r2-run1-cadence-haiku
Cadence: unrecorded
Packet sha256: 09cff41785d52209baa445d9111929e05f04ae4e4638d04c21561f1867145815

# Learnings: 20261021-r2-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 25
- finding: 5
- fix-commit: 5
- gate: 66
- hard-stop: 1
- orchestrator-runner: 1
- stop-refusal: 2

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-5, E-13, E-15, E-23, E-25, E-33, E-35, E-40, E-42, E-46
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 10 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-12, E-31
- Rule: gate-repeat
- Key: gate-repeat|de-adversarial-reviewer|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in P6: fail plan-review-round round # has # must-fix; fail plan-review-round in round # a must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@unrecorded --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-20, E-28, E-29, E-37, E-39, E-44
- Rule: gate-repeat
- Key: gate-repeat|plan-review|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 6 times in P3: fail plan-review-round in round # a must-fix; fail plan-review-round write the plan review of; fail plan-review-round add a row for each.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-51, E-53
- Rule: gate-repeat
- Key: gate-repeat|cadence|entry-invariant
- Change: Before the return, run the `entry-invariant` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: adversarial-review orchestrator unknown activate through the bash; plan-review review limit reached # cycles.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-59, E-62, E-63
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 3 times in E1: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-87, E-89
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in spec-driven: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: SKILL.md
- Status: candidate
- Evidence: E-93, E-95, E-98
- Rule: gate-repeat
- Key: gate-repeat|cadence|closure
- Change: Before the return, run the `closure` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: feat-local-#-csv-# must-fix status fixed not terminal; feat-local-#-csv-export-f# must-fix status open not terminal.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-73
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local no peer-written
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local no peer-written` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-6, E-16, E-26, E-36, E-43
- Rule: redispatch
- Key: redispatch|plan-review|P3
- Change: P3 was dispatched 5 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@unrecorded --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-7, E-17, E-27
- Rule: redispatch
- Key: redispatch|de-adversarial-reviewer|P6
- Change: P6 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@unrecorded --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-8, E-18
- Rule: redispatch
- Key: redispatch|test-benchmark|P7
- Change: P7 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-14, E-24, E-34, E-41, E-47, E-52
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 6 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@unrecorded --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-70, E-81
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@unrecorded --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-14
- Target: commands/pr-review-update.md
- Status: candidate
- Evidence: E-80, E-91, E-94
- Rule: redispatch
- Key: redispatch|pr-review-update|R4
- Change: R4 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-update@unrecorded --config new_skill=pr-review-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-15
- Target: SKILL.md
- Status: candidate
- Evidence: E-99
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 1 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-16
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-72, E-82, E-83, E-101, E-102, E-103, E-104, E-105
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-17
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-84, E-101, E-102, E-103, E-104, E-105
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-18
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-85, E-101, E-102, E-103, E-104, E-105
- Rule: review-finding
- Key: review-finding|spec-driven|core:test-benchmark-pr
- Change: E1 checks `core:test-benchmark-pr` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-19
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-95, E-98
- Rule: open-at-close
- Key: open-at-close|pr-review-local|open-must-fix
- Change: The fix round returns only after `ledger_verify.py` marks each fixed must-fix item verified; R5 found open must-fix items 2 times.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@unrecorded --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-20
- Target: SKILL.md
- Status: candidate
- Evidence: E-100
- Rule: hard-stop
- Key: hard-stop|cadence|R5|retries
- Change: R5 recorded a `retries` hard stop: r# closure must-fix f# open after # fix rounds two fresh fix. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-21
- Target: SKILL.md
- Status: candidate
- Evidence: E-96
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-22
- Target: SKILL.md
- Status: candidate
- Evidence: E-97
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in review. continue
- Change: The hooks refused 1 times with `blocked early stop in review. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-5 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-6 | dispatch | P3 | /plan-review dispatched as P3 |
| E-7 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-8 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-12 | gate | P6 | FAIL plan-review-round: round 1 has 15 must-fix rows |
| E-13 | gate | orchestrator | FAIL plan-review-round: round 1 has 15 must-fix rows |
| E-14 | dispatch | P4 | /plan-update dispatched as P4 |
| E-15 | gate | orchestrator | FAIL plan-review-round: round 2 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-16 | dispatch | P3 | /plan-review dispatched as P3 |
| E-17 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-18 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-20 | gate | P3 | FAIL plan-review-round: write the plan review of this plan first: its `Last reviewed plan sha256:` line names it |
| E-23 | gate | orchestrator | FAIL plan-review-round: round 2 has 4 must-fix rows |
| E-24 | dispatch | P4 | /plan-update dispatched as P4 |
| E-25 | gate | orchestrator | FAIL plan-review-round: round 3 waits on plan-review, adversarial-review |
| E-26 | dispatch | P3 | /plan-review dispatched as P3 |
| E-27 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-28 | gate | P3 | FAIL plan-review-round: in round 3 a must-fix may target only a section that the update changed, or one where plan-review still had a must-fix: Phase 3, global. Record a finding in Phase 1 as a nit |
| E-29 | gate | P3 | FAIL plan-review-round: add a row for each must-fix item of the review: MF-4 |
| E-31 | gate | P6 | FAIL plan-review-round: in round 3 a must-fix may target only a section that the update changed, or one where adversarial-review still had a must-fix: Phase 3, global. Record a finding in Phase 2 as a nit |
| E-33 | gate | orchestrator | FAIL plan-review-round: round 3 has 4 must-fix rows |
| E-34 | dispatch | P4 | /plan-update dispatched as P4 |
| E-35 | gate | orchestrator | FAIL plan-review-round: round 4 waits on plan-review |
| E-36 | dispatch | P3 | /plan-review dispatched as P3 |
| E-37 | gate | P3 | FAIL plan-review-round: round 4 waits on plan-review |
| E-39 | gate | P3 | FAIL plan-review-round: round 4 has 1 must-fix rows |
| E-40 | gate | orchestrator | FAIL plan-review-round: round 4 has 1 must-fix rows |
| E-41 | dispatch | P4 | /plan-update dispatched as P4 |
| E-42 | gate | orchestrator | FAIL plan-review-round: round 5 waits on plan-review |
| E-43 | dispatch | P3 | /plan-review dispatched as P3 |
| E-44 | gate | P3 | FAIL plan-review-round: in round 5 a must-fix may target only a section that the update changed, or one where plan-review still had a must-fix: Phase 3. Record a finding in Phase 1 as a nit |
| E-46 | gate | orchestrator | FAIL plan-review-round: round 5 has 1 must-fix rows |
| E-47 | dispatch | P4 | /plan-update dispatched as P4 |
| E-51 | gate | orchestrator | FAIL entry-invariant |
| E-52 | dispatch | P4 | /plan-update dispatched as P4 |
| E-53 | gate | orchestrator | FAIL entry-invariant |
| E-59 | gate | E1 | FAIL cognitive-complexity |
| E-62 | gate | E1 | FAIL cognitive-complexity |
| E-63 | gate | E1 | FAIL cognitive-complexity |
| E-70 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-72 | finding | R1 | --out writes mode 0600 regardless of umask (mkstemp default); existing 0644 target becomes 0600; tests/test_export.py:197 pins it. Reproduced against HEAD 46fcb72. See .context/prs/reviews/PR_REVIEW_1.md Reproductions 1-2. |
| E-73 | gate | R1 | FAIL pr-review-local-gate |
| E-80 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-81 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-82 | finding | R4 | --out writes mode 0600 regardless of umask (mkstemp default); existing 0644 target becomes 0600; tests/test_export.py:197 pins it. Reproduced against HEAD 46fcb72. See .context/prs/reviews/PR_REVIEW_1.md Reproductions 1-2. |
| E-83 | finding | R4 | --out writes mode 0600 regardless of umask (mkstemp default); existing 0644 target becomes 0600; tests/test_export.py:197 pins it. Reproduced against HEAD 46fcb72. See .context/prs/reviews/PR_REVIEW_1.md Reproductions 1-2. |
| E-84 | finding | R4 | Fix 9315608 sets the temp file mode to 0o666 & ~umask on every overwrite. An existing 0600 target becomes 0644 under umask 022 (reproduced: pre-mode 600, umask 022, result 644). A private report is made world-readable by a re-export. The original 0600 result narrowed the mode. See .context/prs/reviews/PR_REVIEW_#1.md Update 2026-10-21. |
| E-85 | finding | R4 | The regression test pins umask 0o022 only, so it passes when the code hardcodes 0o644 (mutant reproduced: 34 passed). MF-1 requires the mode to follow the umask. The test must cover a second umask, such as 0o077, and expect 0o600 for a new file. See .context/prs/reviews/PR_REVIEW_#1.md Update 2026-10-21. |
| E-87 | gate | spec-driven | FAIL cognitive-complexity |
| E-89 | gate | spec-driven | FAIL cognitive-complexity |
| E-91 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-93 | gate | orchestrator | FAIL closure |
| E-94 | dispatch | R4 | /pr-review-update dispatched as R4 |
| E-95 | gate | orchestrator | FAIL closure |
| E-96 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 3 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-97 | stop-refusal | orchestrator | BLOCKED early stop in review. Continue paceline: next R4 (final-consolidate) via `python3 /tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-r2/scripts/final_consolidate.py` |
| E-98 | gate | orchestrator | FAIL closure |
| E-99 | orchestrator-runner | orchestrator | cd /tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/r2-budgetcli (uv run --offline pytest -q 2>&1 \|\| python3 -m pytest -q 2>&1) \| tail -15; echo "pytest rc=$?"; echo ----; cat pyproject.toml \| sed -n 1,30p |
| E-100 | hard-stop | orchestrator | R5 closure: must-fix F1 open after 4 fix rounds; two fresh fix peers report an environment blocker (no code change) and need a decision. Tests pass (37). R6 and R7 not run. |
| E-101 | fix-commit | E1 | fix: MF-3 new file mode test covers umask 0o077 |
| E-102 | fix-commit | E1 | fix: MF-2 overwrite keeps existing target mode |
| E-103 | fix-commit | E1 | test: MF-2 overwrite keeps existing target mode (red) |
| E-104 | fix-commit | E1 | fix: MF-1 out file mode follows umask |
| E-105 | fix-commit | E1 | test: MF-1 out replace keeps umask mode (red) |
