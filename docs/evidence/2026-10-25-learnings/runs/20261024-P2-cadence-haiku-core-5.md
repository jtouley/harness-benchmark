RUN_BY_COMMAND: run-learnings
Run: 20261024-P2-cadence-haiku-core-5
Cadence: 2100c6e6aa99d99309cfa8e7f8c5cee1018584b4
Packet sha256: d7a07827830b899cb9fdb5ccb3d9f36e29d2e3f4766ddcf482d81bca44b5e5c7

# Learnings: 20261024-P2-cadence-haiku-core-5

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- after-document: 8
- dispatch: 10
- finding: 4
- fix-commit: 3
- gate: 24
- orchestrator-runner: 4
- stop-point: 1

## Proposals

### L-1
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-13, E-14, E-16, E-17, E-18, E-19
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 6 times in E1: % duplicated # of # code lines; bugs s# audit url open for permitted; bugs.max is # fix each ruff finding.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-34
- Rule: late-gate
- Key: late-gate|spec-driven|test-benchmark-gate-code|test-benchmark-code mean score
- Change: E1's phase gate runs the `test-benchmark-gate-code` measure `test-benchmark-code mean score` before E4, so the review phase does not find it first. It failed 1 times after E1 in this run.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-30, E-36, E-38
- Rule: redispatch
- Key: redispatch|test-benchmark|R2
- Change: R2 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-28, E-35, E-37, E-42
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 4 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-27, E-52, E-53, E-54
- Rule: review-finding
- Key: review-finding|spec-driven|core:contracts
- Change: E1 checks `core:contracts` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-31, E-32, E-52, E-53, E-54
- Rule: review-finding
- Key: review-finding|spec-driven|core:test-benchmark
- Change: E1 checks `core:test-benchmark` before E4: the review found 2 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-40
- Rule: open-at-close
- Key: open-at-close|pr-review-local|open-must-fix
- Change: The fix round returns only after `ledger_verify.py` marks each fixed must-fix item verified; R5 found open must-fix items 1 times.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@2100c6e6aa99d99309cfa8e7f8c5cee1018584b4 --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-13 | gate | E1 | FAIL cognitive-complexity |
| E-14 | gate | E1 | FAIL cognitive-complexity |
| E-16 | gate | E1 | FAIL cognitive-complexity |
| E-17 | gate | E1 | FAIL cognitive-complexity |
| E-18 | gate | E1 | FAIL cognitive-complexity |
| E-19 | gate | E1 | FAIL cognitive-complexity |
| E-27 | finding | R1 | Length key guard does not exclude JSON null; classify raises TypeError on length.old null (repro: /tmp/r1-scratch/nulllen.py prints CRASH TypeError). Consumer stops with no commit and restart redelivers the same event. |
| E-28 | orchestrator-runner | orchestrator | uv run pytest tests/test_stream_sink.py -q -k null_length 2>&1 \| tail -15 |
| E-30 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-31 | finding | R2 | Mutant: classify() keeps the watermark of the batch start and never advances it within the batch (stream_lake.py line 43 changed). Suite still passes (12/12 stream sink and source tests). Within one commit, an event 3 min after a 20 min event is not marked late. No test commits two events with different times in one batch. |
| E-32 | finding | R2 | Mutant: the late rule uses >= instead of > (stream_lake.py line 41). Suite still passes. No test sits on the boundary: a watermark exactly 10 min after the window end must be on time, and one second more must be late. The late-count tests do not reach that boundary. |
| E-34 | gate | R2 | FAIL test-benchmark-gate-code |
| E-35 | orchestrator-runner | orchestrator | uv run pytest -q 2>&1 \| tail -3 && git add tests/test_stream_sink.py && GIT_AUTHOR_NAME=Claude GIT_AUTHOR_EMAIL=noreply@anthropic.com GIT_COMMITTER_NAME=Claude GIT_COMMITTER_EMAIL=noreply@anthropic.com git commit -q -m "test(stream): pin the lateness boundary and the in-batch watermark Two surviving mutants of the R2 sample: a >= boundary and a watermark that does not advance inside a batch. Each… |
| E-36 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-37 | orchestrator-runner | orchestrator | uv run pytest -q 2>&1 \| tail -3 && git add tests/test_stream_sink.py && GIT_AUTHOR_NAME=Claude GIT_AUTHOR_EMAIL=noreply@anthropic.com GIT_COMMITTER_NAME=Claude GIT_COMMITTER_EMAIL=noreply@anthropic.com git commit -q -m "test(stream): carry the watermark across batches (spec-F01) The R2 probe showed a watermark that is set once and never advanced survived the suite. The test now checks a late even… |
| E-38 | dispatch | R2 | /test-benchmark dispatched as R2 |
| E-40 | gate | orchestrator | FAIL closure |
| E-42 | orchestrator-runner | orchestrator | uv run pytest tests/test_stream_sink.py -q -k late_boundary 2>&1 \| tail -2 && uv run pytest -q 2>&1 \| tail -1 && git add tests/test_stream_sink.py && GIT_AUTHOR_NAME=Claude GIT_AUTHOR_EMAIL=noreply@anthropic.com GIT_COMMITTER_NAME=Claude GIT_COMMITTER_EMAIL=noreply@anthropic.com git commit -q -m "test(stream): name the late boundary test for its ledger check (spec-F02) The ledger check selects te… |
| E-52 | fix-commit | E1 | test(stream): name the late boundary test for its ledger check (spec-F02) |
| E-53 | fix-commit | E1 | test(stream): carry the watermark across batches (spec-F01) |
| E-54 | fix-commit | E1 | fix(stream): keep an edit with a null length value |
