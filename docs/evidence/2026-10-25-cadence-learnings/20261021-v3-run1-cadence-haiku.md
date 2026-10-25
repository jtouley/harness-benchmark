RUN_BY_COMMAND: run-learnings
Run: 20261021-v3-run1-cadence-haiku
Cadence: ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e
Packet sha256: 822f39aebf229ce12fd5e2e7eeacd9ef7f334912072a7e3e5c1a883235b6d7f7

# Learnings: 20261021-v3-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 15
- gate: 46
- hard-stop: 2

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-6, E-17, E-20, E-22, E-34, E-35, E-40, E-44, E-47, E-57, E-60, E-62
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 12 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-11, E-15, E-16, E-31, E-33, E-37, E-38, E-39, E-50, E-55, E-56, E-59
- Rule: gate-repeat
- Key: gate-repeat|plan-review|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 12 times in P3: fail plan-review-round reviews this plan but its; fail plan-review-round round # waits on plan-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-27, E-28
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in P7: fail plan-review-round a finding needs an id; fail plan-review-round phase phases # to.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-51, E-52, E-54
- Rule: gate-repeat
- Key: gate-repeat|de-adversarial-reviewer|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 3 times in P6: fail plan-review-round round # waits on plan-review; fail plan-review-round in round # a must-fix.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-7, E-23, E-36, E-42, E-48, E-58
- Rule: redispatch
- Key: redispatch|plan-review|P3
- Change: P3 was dispatched 6 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: skills/de-adversarial-reviewer/SKILL.md
- Status: candidate
- Evidence: E-8, E-24, E-49
- Rule: redispatch
- Key: redispatch|de-adversarial-reviewer|P6
- Change: P6 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=de-adversarial-reviewer@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=de-adversarial-reviewer@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-9, E-25
- Rule: redispatch
- Key: redispatch|test-benchmark|P7
- Change: P7 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-21, E-46
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-41
- Rule: hard-stop
- Key: hard-stop|cadence|orchestrator|retries`.
- Change: orchestrator recorded a `retries`.` hard stop: hard-stop retries. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-10
- Target: commands/plan-review.md
- Status: candidate
- Evidence: E-63
- Rule: hard-stop
- Key: hard-stop|plan-review|P3|retries
- Change: P3 recorded a `retries` hard stop: p# plan-review hit its five-cycle limit loop_cycles # . the fifth review. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-review@ab66ac71fd1b2d5dc80c9d0e9412d28461e0af8e --config new_skill=plan-review@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-6 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-7 | dispatch | P3 | /plan-review dispatched as P3 |
| E-8 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-9 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-11 | gate | P3 | FAIL plan-review-round: plan_feat-local-4-csv-export.md reviews this plan, but its verdict `REQUEST CHANGES` is not a plan-review verdict: write `Verdict:` and one of `READY TO EXECUTE`, `NOT READY`, `READY WITH CHANGES`, `REQUEST CHANGES` |
| E-15 | gate | P3 | FAIL plan-review-round: plan_feat-local-4-csv-export.md reviews this plan, but its verdict `REQUEST CHANGES` is not a plan-review verdict: write `Verdict:` and one of `READY TO EXECUTE`, `NOT READY`, `READY WITH CHANGES`, `REQUEST CHANGES` |
| E-16 | gate | P3 | FAIL plan-review-round: plan_feat-local-4-csv-export.md reviews this plan, but its verdict `REQUEST CHANGES` is not a plan-review verdict: write `Verdict:` and one of `READY TO EXECUTE`, `NOT READY`, `READY WITH CHANGES`, `REQUEST CHANGES` |
| E-17 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review |
| E-20 | gate | orchestrator | FAIL plan-review-round: round 1 has 16 must-fix rows |
| E-21 | dispatch | P4 | /plan-update dispatched as P4 |
| E-22 | gate | orchestrator | FAIL plan-review-round: round 2 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-23 | dispatch | P3 | /plan-review dispatched as P3 |
| E-24 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-25 | dispatch | P7 | /test-benchmark dispatched as P7 |
| E-27 | gate | P7 | FAIL plan-review-round: a finding needs an id such as MF-1 and a severity of must-fix or nit |
| E-28 | gate | P7 | FAIL plan-review-round: phase 'Phases 1 to 4' is not a section of the plan: use one of Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, global, record |
| E-31 | gate | P3 | FAIL plan-review-round: plan_feat-local-4-csv-export.md reviews this plan, but its verdict `REQUEST CHANGES` is not a plan-review verdict: write `Verdict:` and one of `READY TO EXECUTE`, `NOT READY`, `READY WITH CHANGES`, `REQUEST CHANGES` |
| E-33 | gate | P3 | FAIL plan-review-round: plan_feat-local-4-csv-export.md reviews this plan, but its verdict `REQUEST CHANGES` is not a plan-review verdict: write `Verdict:` and one of `READY TO EXECUTE`, `NOT READY`, `READY WITH CHANGES`, `REQUEST CHANGES` |
| E-34 | gate | orchestrator | FAIL plan-review-round: round 2 waits on plan-review |
| E-35 | gate | orchestrator | FAIL plan-review-round: round 2 waits on plan-review |
| E-36 | dispatch | P3 | /plan-review dispatched as P3 |
| E-37 | gate | P3 | FAIL plan-review-round: plan_feat-local-4-csv-export.md reviews this plan, but its verdict `REQUEST CHANGES` is not a plan-review verdict: write `Verdict:` and one of `READY TO EXECUTE`, `NOT READY`, `READY WITH CHANGES`, `REQUEST CHANGES` |
| E-38 | gate | P3 | FAIL plan-review-round: plan_feat-local-4-csv-export.md reviews this plan, but its verdict `REQUEST CHANGES` is not a plan-review verdict: write `Verdict:` and one of `READY TO EXECUTE`, `NOT READY`, `READY WITH CHANGES`, `REQUEST CHANGES` |
| E-39 | gate | P3 | FAIL plan-review-round: round 2 waits on plan-review |
| E-40 | gate | orchestrator | FAIL plan-review-round: round 2 waits on plan-review |
| E-41 | hard-stop | orchestrator | --hard-stop retries`. |
| E-42 | dispatch | P3 | /plan-review dispatched as P3 |
| E-44 | gate | orchestrator | FAIL plan-review-round: round 2 has 7 must-fix rows |
| E-46 | dispatch | P4 | /plan-update dispatched as P4 |
| E-47 | gate | orchestrator | FAIL plan-review-round: round 3 waits on plan-review, adversarial-review |
| E-48 | dispatch | P3 | /plan-review dispatched as P3 |
| E-49 | dispatch | P6 | /de-adversarial-reviewer dispatched as P6 |
| E-50 | gate | P3 | FAIL plan-review-round: plan_feat-local-4-csv-export.md reviews this plan, but its verdict `READY TO EXECUTE` is not a plan-review verdict: write `Verdict:` and one of `READY TO EXECUTE`, `NOT READY`, `READY WITH CHANGES`, `REQUEST CHANGES` |
| E-51 | gate | P6 | FAIL plan-review-round: in round 3 a must-fix may target only a section that the update changed, or one where adversarial-review still had a must-fix: Phase 4. Record a finding in global as a nit |
| E-52 | gate | P6 | FAIL plan-review-round: round 3 waits on plan-review, adversarial-review |
| E-54 | gate | P6 | FAIL plan-review-round: round 3 waits on plan-review |
| E-55 | gate | P3 | FAIL plan-review-round: plan_feat-local-4-csv-export.md reviews this plan, but its verdict `READY TO EXECUTE` is not a plan-review verdict: write `Verdict:` and one of `READY TO EXECUTE`, `NOT READY`, `READY WITH CHANGES`, `REQUEST CHANGES` |
| E-56 | gate | P3 | FAIL plan-review-round: plan_feat-local-4-csv-export.md reviews this plan, but its verdict `READY TO EXECUTE` is not a plan-review verdict: write `Verdict:` and one of `READY TO EXECUTE`, `NOT READY`, `READY WITH CHANGES`, `REQUEST CHANGES` |
| E-57 | gate | orchestrator | FAIL plan-review-round: round 3 waits on plan-review |
| E-58 | dispatch | P3 | /plan-review dispatched as P3 |
| E-59 | gate | P3 | FAIL plan-review-round: plan_feat-local-4-csv-export.md reviews this plan, but its verdict `READY WITH CHANGES` is not a plan-review verdict: write `Verdict:` and one of `READY TO EXECUTE`, `NOT READY`, `READY WITH CHANGES`, `REQUEST CHANGES` |
| E-60 | gate | orchestrator | FAIL plan-review-round: round 3 waits on plan-review |
| E-62 | gate | orchestrator | FAIL plan-review-round: round 3 waits on plan-review |
| E-63 | hard-stop | orchestrator | P3 plan-review hit its five-cycle limit (loop_cycles=5). The fifth review was not counted: it returned READY WITH CHANGES with MF-1 (Phase 4 read-only test is skipped as uid 0), and the round-3 plan-findings file holds a stray MF-1 row. The P6 adversarial review is also at its three-cycle limit with REQUEST CHANGES. Re-invoking reviewers inflated the cycle count (see .context/issues/plan-review-r… |
