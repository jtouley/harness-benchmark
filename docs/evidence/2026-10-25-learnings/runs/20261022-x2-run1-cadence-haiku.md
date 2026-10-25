RUN_BY_COMMAND: run-learnings
Run: 20261022-x2-run1-cadence-haiku
Cadence: 9c2505a78ef6f6d74e057975cc9f3919db2e4dc5
Packet sha256: a97bd15e15de9433348ab56a98a1fd594afdbc70dcb6a4844c8d73f4aa20b8f1

# Learnings: 20261022-x2-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 13
- finding: 9
- gate: 43
- hard-stop: 1
- orchestrator-runner: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-8, E-19, E-21, E-22
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 4 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix; fail plan-review-round changed phase # phase.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-15, E-16, E-17
- Rule: gate-repeat
- Key: gate-repeat|plan-review|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 3 times in P3: fail plan-review-round no open round names plan-review; fail plan-review-round the run has no plan; fail plan-review-round round # waits on plan-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-24, E-25
- Rule: gate-repeat
- Key: gate-repeat|plan-update|plan-update-gate
- Change: Before the return, run the `plan-update-gate` gate once and fix every class it names in one pass. In this run it failed 2 times in P4: plan-review-round changed phase # phase # which; plan-review-round changed phase # which no finding.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-34, E-35, E-41
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 3 times in E1: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; fix step run r# without --check to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-49, E-60
- Rule: gate-repeat
- Key: gate-repeat|pr-review-local|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in R1: % duplicated # of # code lines; duplication.max_percent is # reuse the code that; fix step delegate with as its one.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-54, E-63, E-66
- Rule: gate-repeat
- Key: gate-repeat|pr-review-local|pr-review-local-gate
- Change: Before the return, run the `pr-review-local-gate` gate once and fix every class it names in one pass. In this run it failed 3 times in R1: pr-review-local no join row yet the peer.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-49, E-60
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|% duplicated
- Change: E1's phase gate runs the `cognitive-complexity` measure `% duplicated` before E4, so the review phase does not find it first. It failed 2 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-49, E-60
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|duplication.max_percent is
- Change: E1's phase gate runs the `cognitive-complexity` measure `duplication.max_percent is` before E4, so the review phase does not find it first. It failed 2 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-49, E-60
- Rule: late-gate
- Key: late-gate|spec-driven|cognitive-complexity|fix step delegate
- Change: E1's phase gate runs the `cognitive-complexity` measure `fix step delegate` before E4, so the review phase does not find it first. It failed 2 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-54, E-63, E-66
- Rule: late-gate
- Key: late-gate|spec-driven|pr-review-local-gate|pr-review-local no join
- Change: E1's phase gate runs the `pr-review-local-gate` measure `pr-review-local no join` before E4, so the review phase does not find it first. It failed 3 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-11
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-20, E-23
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-12
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-46, E-58, E-64
- Rule: redispatch
- Key: redispatch|pr-review-local|R1
- Change: R1 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-13
- Target: SKILL.md
- Status: candidate
- Evidence: E-42
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 1 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-14
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-50, E-51, E-52, E-53, E-55, E-61
- Rule: review-finding
- Key: review-finding|spec-driven|core:plan-conformance
- Change: E1 checks `core:plan-conformance` before E4: the review found 6 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-15
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-56
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-16
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-57
- Rule: review-finding
- Key: review-finding|spec-driven|R2 test-benchmark: mutation resilience
- Change: E1 checks `R2 test-benchmark: mutation resilience` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-17
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-62
- Rule: review-finding
- Key: review-finding|spec-driven|core:standalone-package
- Change: E1 checks `core:standalone-package` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-18
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-67
- Rule: hard-stop
- Key: hard-stop|pr-review-local|R1|retries
- Change: R1 recorded a `retries` hard stop: r# gate needs the pr-review-local peer wrote in three runs fix round. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@9c2505a78ef6f6d74e057975cc9f3919db2e4dc5 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-8 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-15 | gate | P3 | FAIL plan-review-round: no open round names plan-review for this plan: run plan_wave.py first |
| E-16 | gate | P3 | FAIL plan-review-round: the run has no plan. Run P1 (/plan-create) first |
| E-17 | gate | P3 | FAIL plan-review-round: round 1 waits on plan-review |
| E-19 | gate | orchestrator | FAIL plan-review-round: round 1 has 10 must-fix rows |
| E-20 | dispatch | P4 | /plan-update dispatched as P4 |
| E-21 | gate | orchestrator | FAIL plan-review-round: /plan-update changed Phase 1, Phase 4, which no finding of round 1 names. Send /plan-update again: undo that change, and change only Phase 2, Phase 3, global. The change: - - `parse_month` accepts `2026-10` and rejects `2026-13`, `2026-1`, `2026-00`, `October` and `2026-10-01`. \| + - `parse_month` accepts `2026-10` and rejects `2026-13`, `2026-1`, `2026-00`, `October`, `20… |
| E-22 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review f3c049d2e7c8)` row for MF-2 of round-1.md. Send /plan-update again |
| E-23 | dispatch | P4 | /plan-update dispatched as P4 |
| E-24 | gate | P4 | FAIL plan-update-gate |
| E-25 | gate | P4 | FAIL plan-update-gate |
| E-34 | gate | E1 | FAIL cognitive-complexity |
| E-35 | gate | E1 | FAIL cognitive-complexity |
| E-41 | gate | E1 | FAIL cognitive-complexity |
| E-42 | orchestrator-runner | orchestrator | SKILL_ROOT="/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-x"; C="$SKILL_ROOT/scripts"; git log --oneline \| head -8; echo ---; python3 "$C/impl_artifact.py" 2>&1 \| tail -20; echo "E2=$?"; echo ---; python3 "$C/architecture_review.py" --phase impl 2>&1 \| tail -20; echo "E3=$?"; echo ---; python3 -m pytest -q 2>&1 \| tail -15 |
| E-46 | dispatch | R1 | /pr-review-local dispatched as R1 |
| E-49 | gate | R1 | FAIL cognitive-complexity |
| E-50 | finding | R1 | --out set to the ledger path overwrites the JSON ledger with CSV; reproduced in scratch dir (exit 0, ledger lost). See PR_REVIEW_1 Reproductions. |
| E-51 | finding | R1 | Stored row missing a field, a non-object row, or a non-list top level gives KeyError/TypeError traceback, exit 1; G-9 requires error: line and exit 2. |
| E-52 | finding | R1 | Lone surrogate in stored note raises UnicodeEncodeError traceback at export_csv(...).encode(utf-8); exit 1. |
| E-53 | finding | R1 | format_amount(-5) gives -1.95 for stored amount_cents -5; expected -0.05. Amounts must print with two decimals (AC-2 claim). |
| E-54 | gate | R1 | FAIL pr-review-local-gate |
| E-55 | finding | R1 | export piped into head -0 gives BrokenPipeError traceback, exit 1 (closed output pipe input class of review-rigor). |
| E-56 | finding | R1 | R3 duplication FAIL: 29.4% duplicated, 37 of 126 code lines (new); lines 57-66 equal 70-79. Fix needs repin of pinned acceptance script. |
| E-57 | finding | R2 | Mutant len(rows) -> len(expenses) in the wrote message survives: python3 -m pytest -q tests/test_cli_export.py -k out_writes_file passes. The fixture has two expenses, both in 2026-10, so selected and total counts match. |
| E-58 | dispatch | R1 | /pr-review-local dispatched as R1 |
| E-60 | gate | R1 | FAIL cognitive-complexity |
| E-61 | finding | R1 | Mutant wrote {len(expenses)} rows survives: fixture has two expenses both in 2026-10, so the selected and total counts match. Same as R2-F01. |
| E-62 | finding | R1 | The request asks for two deferrals (LOCAL-9 upload, RFC 4180 quoting to LOCAL-10). The register approves one; RFC quoting is under Deferrals rejected. AC-3 requires RFC quoting now. The user must choose. |
| E-63 | gate | R1 | FAIL pr-review-local-gate |
| E-64 | dispatch | R1 | /pr-review-local dispatched as R1 |
| E-66 | gate | R1 | FAIL pr-review-local-gate |
| E-67 | hard-stop | orchestrator | R1 gate needs prs/reviews/PR_REVIEW_#1.md; the pr-review-local peer wrote PR_REVIEW_1.md in three runs (fix round hook blocks without #). Peer naming defect, not a code defect. 31 tests pass at HEAD 88142db. |
