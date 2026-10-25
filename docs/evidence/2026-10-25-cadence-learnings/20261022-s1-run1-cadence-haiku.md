RUN_BY_COMMAND: run-learnings
Run: 20261022-s1-run1-cadence-haiku
Cadence: cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5
Packet sha256: 81bc9ce3dd6f04efd3945282d3093d801d633c385f893d3545392892dd1b3ab0

# Learnings: 20261022-s1-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 7
- fix-commit: 13
- gate: 61
- hard-stop: 1
- stop-refusal: 4

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-5, E-10
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-37, E-39
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in spec-driven: types union-attr item none of io bytes; types.max is # fix each mypy finding; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-53, E-58, E-60, E-64
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|acceptance
- Change: Before the return, run the `acceptance` gate once and fix every class it names in one pass. In this run it failed 4 times in spec-driven: acceptance ac-# has an open defect ac.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-31, E-32, E-47, E-74, E-75, E-76, E-77, E-78, E-79, E-80, E-81, E-82, E-83, E-84, E-85, E-86
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-33, E-48, E-74, E-75, E-76, E-77, E-78, E-79, E-80, E-81, E-82, E-83, E-84, E-85, E-86
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-49, E-56, E-74, E-75, E-76, E-77, E-78, E-79, E-80, E-81, E-82, E-83, E-84, E-85, E-86
- Rule: review-finding
- Key: review-finding|spec-driven|cadence:test-benchmark R2 (code mode)
- Change: E1 checks `cadence:test-benchmark R2 (code mode)` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: SKILL.md
- Status: candidate
- Evidence: E-72
- Rule: hard-stop
- Key: hard-stop|cadence|R4|retries
- Change: R4 recorded a `retries` hard stop: r# holds on pr review mf-# pinned check ac-# . ac-# check. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: SKILL.md
- Status: candidate
- Evidence: E-6
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked record each finding of your
- Change: The hooks refused 1 times with `blocked record each finding of your`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-44, E-50, E-71
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 3 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@cf2ed61e0c744f102c53d67ea1bd9d0710b2eff5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-5 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-6 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-s/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-s/scripts/plan_wave.py" done --stage test-benchmar… |
| E-10 | gate | orchestrator | FAIL plan-review-round: round 1 has 8 must-fix rows |
| E-31 | finding | pr-review-local | --out set to the ledger path overwrites the ledger with the CSV (ledger.json holds the expense, the export replaces it; the ledger is no longer loadable). Reproduced: export --out l.json then cmp against the saved ledger differs; ADR-0027 output-equals-input class. |
| E-32 | finding | pr-review-local | A note with a byte that is not UTF-8 (add accepts it) makes export raise UnicodeEncodeError (traceback, exit 1) on every run until the ledger is hand-edited. Reproduced with add --note of byte 0x80 then export. |
| E-33 | finding | pr-review-local | AC-4 claim is that the row count is printed; the last assert is a standalone-2 regex, so a build that prints a hard-coded 'wrote 2 rows' passes. Mutant run: sed the count to 2 then check_ac4.py exits 0. Fix goes through plan-update --acceptance AC-4. |
| E-37 | gate | spec-driven | FAIL cognitive-complexity |
| E-39 | gate | spec-driven | FAIL cognitive-complexity |
| E-44 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-47 | finding | pr-review-update | A note with a byte that is not UTF-8 (add accepts it) makes export raise UnicodeEncodeError (traceback, exit 1) on every run until the ledger is hand-edited. Reproduced with add --note of byte 0x80 then export. |
| E-48 | finding | pr-review-update | The F05 fix catches only KeyError, TypeError and ValueError from Ledger.load(). A stored amount_cents of float inf (JSON Infinity) parses to inf, and int(inf) raises OverflowError: export prints a traceback and exits 1 (totals fails the same way). A ledger of 100000 nested brackets raises RecursionError with the same traceback. Reproduced at HEAD 32321742353035c2dd2ff4156b548f03aaf30426. The clas… |
| E-49 | finding | test-benchmark | Surviving mutant: src/budgetcli/export.py run_export broken-pipe branch, return 1 changed to return 0. The mutant copy gives 46 passed. The test asserts stderr only and never asserts proc.returncode; HEAD exits with status 1 on a closed pipe. Fix in the existing test: assert proc.returncode == 1. |
| E-50 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-53 | gate | spec-driven | FAIL acceptance |
| E-56 | finding | test-benchmark | Surviving mutant at HEAD 355a892: src/budgetcli/ledger.py line 32, the loop in Ledger.add changed from (expense.category, expense.note) to (expense.note,), so a category with a lone surrogate is no longer checked. Run in a mktemp copy of HEAD outside the worktree: python3 -m pytest -q tests gives 49 passed (mutant survives). HEAD itself refuses the category: add food with category bytes 0x80 give… |
| E-58 | gate | spec-driven | FAIL acceptance |
| E-60 | gate | spec-driven | FAIL acceptance |
| E-64 | gate | spec-driven | FAIL acceptance |
| E-71 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 396 characters; the limit is 300. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-72 | hard-stop | orchestrator | R4 holds on PR review MF-3 (pinned check AC-4). AC-4 check passes at HEAD, the repin refuses (no open defect), and five fix rounds have not closed the ledger row. Needs a human decision on MF-3. |
| E-74 | fix-commit | E1 | test: MF-3 repro of the AC-4 defect |
| E-75 | fix-commit | E1 | fix: MF-4 bad stored amount or deep nesting gives an error line |
| E-76 | fix-commit | E1 | test: MF-4 export of an infinite amount or a deeply nested ledger (red) |
| E-77 | fix-commit | E1 | test: MF-4 export of an infinite amount or a deeply nested ledger (red) |
| E-78 | fix-commit | E1 | fix: MF-2 add refuses a note that is not UTF-8 |
| E-79 | fix-commit | E1 | test: MF-2 add refuses a note that is not UTF-8 (red) |
| E-80 | fix-commit | E1 | fix: R3 types narrow proc.stdout in the closed-pipe test |
| E-81 | fix-commit | E1 | fix: F04 exit quietly when stdout is a closed pipe |
| E-82 | fix-commit | E1 | fix: F05 error line for an unreadable ledger file |
| E-83 | fix-commit | E1 | fix: MF-2 F03 error line for a note that is not UTF-8 |
| E-84 | fix-commit | E1 | test: MF-2 F03 export of a note that is not UTF-8 (red) |
| E-85 | fix-commit | E1 | fix: MF-1 F02 refuse --out that is the ledger file |
| E-86 | fix-commit | E1 | test: MF-1 F02 export onto the ledger path (red) |
