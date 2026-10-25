RUN_BY_COMMAND: run-learnings
Run: 20261024-P2-cadence-haiku-full-2
Cadence: d3c2ffe86a4a294335123290f6ca6ae836bc6afb
Packet sha256: 1c6916dcb62d9c7b8133e4f0b3ee38be05d5da814f163eb70e36cdc9ca797b9c

# Learnings: 20261024-P2-cadence-haiku-full-2

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- after-document: 3
- dispatch: 4
- finding: 2
- gate: 11
- hard-stop: 1
- stop-point: 1
- stop-refusal: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-11, E-14, E-16, E-19
- Rule: gate-repeat
- Key: gate-repeat|cadence|entry-invariant
- Change: Before the return, run the `entry-invariant` gate once and fix every class it names in one pass. In this run it failed 4 times in orchestrator: plan-update p# verdict is request changes has; plan-update p# has no ## revision ledger.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@d3c2ffe86a4a294335123290f6ca6ae836bc6afb --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-12, E-13, E-15, E-18
- Rule: redispatch
- Key: redispatch|plan-update|P4
- Change: P4 was dispatched 4 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@d3c2ffe86a4a294335123290f6ca6ae836bc6afb --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-7
- Rule: review-finding
- Key: review-finding|cadence|test-benchmark:assertion-strength
- Change: E1 checks `test-benchmark:assertion-strength` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@d3c2ffe86a4a294335123290f6ca6ae836bc6afb --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-8
- Rule: review-finding
- Key: review-finding|cadence|test-benchmark:dry
- Change: E1 checks `test-benchmark:dry` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@d3c2ffe86a4a294335123290f6ca6ae836bc6afb --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-20
- Rule: hard-stop
- Key: hard-stop|plan-update|P4|retries
- Change: P4 recorded a `retries` hard stop: p# plan-update peer did not write the revision ledgers for the p. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@d3c2ffe86a4a294335123290f6ca6ae836bc6afb --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: SKILL.md
- Status: candidate
- Evidence: E-17
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in planning. continue
- Change: The hooks refused 1 times with `blocked early stop in planning. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@d3c2ffe86a4a294335123290f6ca6ae836bc6afb --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|plan-update|P4|hard stop retries p# plan-update
- Change: The run stopped at P4: hard stop retries p# plan-update peer did not write the revision ledgers for the. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@d3c2ffe86a4a294335123290f6ca6ae836bc6afb --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | P4 | hard stop retries: P4 plan-update peer did not write the revision ledgers for the P6 review (e17fb87d94b6) or the P7 review (e070bb537547) after four attempts; P9 entry-invariant fails. See .context/issues/spec-p4-ledger.md. (FAIL no active cadence session) |
| E-7 | finding | test-benchmark | Assertion strength 6 of 10. test_pinned_packages_import only imports packages. test_reads_zip_in_place (Phase 4) and test_crash_between_data_and_commit_loses_nothing (Phase 8) name no expected value and no observable check (no extracted file on disk; exact rows and commit state after the crash). Fix: state the expected value in each test row. |
| E-8 | finding | test-benchmark | DRY score 6 of 10. The Reuse section names no shared owner for the make-build run (Phase 7 test_second_build_same_rows and the seven Phase 11 acceptance tests all need build output), the fake SSE server (Phases 8 and 10), or the fixture zips (Phases 4 and 5). Without a named session fixture each test clones the setup. test_second_run_continues_without_duplicates (Phase 10) repeats test_drop_and_r… |
| E-11 | gate | orchestrator | FAIL entry-invariant |
| E-12 | dispatch | P4 | /plan-update dispatched as P4 |
| E-13 | dispatch | P4 | /plan-update dispatched as P4 |
| E-14 | gate | orchestrator | FAIL entry-invariant |
| E-15 | dispatch | P4 | /plan-update dispatched as P4 |
| E-16 | gate | orchestrator | FAIL entry-invariant |
| E-17 | stop-refusal | orchestrator | BLOCKED early stop in planning. Continue paceline: next P4 (plan-update) via `/plan-update`: plan-update: P6 adversarial_spec.md verdict is REQUEST CHANGES; spec.plan.md has no `## Revision ledger (review e17fb87d94b6)` for B-1, B-2, B-3, B-4, C-1, C-2, C-3, C-4, C-5, C-6 of adversarial_spec.md. Run /plan-update spec.plan.md --from-review adversarial_spec.md. End the update with `## Revision ledg… |
| E-18 | dispatch | P4 | /plan-update dispatched as P4 |
| E-19 | gate | orchestrator | FAIL entry-invariant |
| E-20 | hard-stop | orchestrator | P4 plan-update peer did not write the revision ledgers for the P6 review (e17fb87d94b6) or the P7 review (e070bb537547) after four attempts; P9 entry-invariant fails. See .context/issues/spec-p4-ledger.md. |
