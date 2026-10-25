RUN_BY_COMMAND: run-learnings
Run: 20261021-P1-cadence-core-haiku-2
Cadence: 29315c4e64ff318a80a1a7d2c809beb4b3c15611
Packet sha256: 081b1230e09f68a8098a2a107bb441a8f10d42ea7525b74472f1fbace20a4c4c

# Learnings: 20261021-P1-cadence-core-haiku-2

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: no
- transcript: no

## Evidence counts

- stop-point: 1

## Proposals

### L-1
- Target: commands/plan-update.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|plan-update|P4|retries hard stop p# drops
- Change: The run stopped at P4: retries hard stop p# drops the plan s run_by_command marker. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=plan-update@29315c4e64ff318a80a1a7d2c809beb4b3c15611 --config new_skill=plan-update@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | P4 | retries hard stop: P4 drops the plan's RUN_BY_COMMAND marker |
