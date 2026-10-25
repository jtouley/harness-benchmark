RUN_BY_COMMAND: run-learnings
Run: 20261021-c-run2-cadence-sonnet
Cadence: unrecorded
Packet sha256: f8c438818fbf6812ad54a724ff8132af80a4f5a7fd11059deeeb4aab77063f06

# Learnings: 20261021-c-run2-cadence-sonnet

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- fix-commit: 2
- gate: 8
- orchestrator-runner: 1
- stop-point: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-5
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 1 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@unrecorded --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-11, E-12
- Rule: fix-commits
- Key: fix-commits|spec-driven|fix-commits
- Change: 2 fix commits followed E1 with no review finding recorded. The review records each defect it finds as a ledger finding, so that the fix has an id.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@unrecorded --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-5 | orchestrator-runner | orchestrator | cd /tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/c-budgetcli; git log --oneline \| head -4; grep F5 .context/findings.jsonl \| tail -1 \| cut -c1-400; python3 -m pytest tests -q 2>&1 \| tail -3 |
| E-11 | fix-commit | E1 | fix: feat-local-3-recurring-expenses-F5 store file is <ledger>.recurring.json beside the ledger |
| E-12 | fix-commit | E1 | fix: feat-local-3-recurring-expenses-F3 shared CLI helper checks no Traceback, one cannot-read assertion |
