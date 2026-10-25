RUN_BY_COMMAND: run-learnings
Run: 20261021-k-run2-cadence-core-sonnet
Cadence: unrecorded
Packet sha256: 1a9629b3b176b2887c181ec89d3ab18b0ad001c2f709d3b1a92e5c525a11ace4

# Learnings: 20261021-k-run2-cadence-core-sonnet

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- fix-commit: 3
- gate: 5
- orchestrator-runner: 2
- stop-point: 1
- stop-refusal: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-4, E-5
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 2 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-10, E-11, E-12
- Rule: fix-commits
- Key: fix-commits|spec-driven|fix-commits
- Change: 3 fix commits followed E1 with no review finding recorded. The review records each defect it finds as a ledger finding, so that the fix has an id.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-3
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 1 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-3 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 15 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-4 | orchestrator-runner | orchestrator | git log --oneline \| head -3; git status --short \| head; grep F3 .context/findings.jsonl \| cut -c1-80; grep -o '"status": "[a-z_]*"' .context/findings.jsonl \| tail -1; python3 -m pytest tests -k blank_category -q 2>&1 \| tail -5 |
| E-5 | orchestrator-runner | orchestrator | git log --oneline \| head -2; grep F3 .context/findings.jsonl \| grep -o '"status": "[a-z_]*"'; python3 -m pytest tests -q 2>&1 \| tail -2 |
| E-10 | fix-commit | E1 | fix(LOCAL-3): reject blank recurring category (F3) |
| E-11 | fix-commit | E1 | fix: phase 5 add uses _today(); clears ruff DTZ011 |
| E-12 | fix-commit | E1 | fix: F4 reject a budgets file of the wrong shape |
