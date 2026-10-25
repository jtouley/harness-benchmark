RUN_BY_COMMAND: run-learnings
Run: 20261021-P2-cadence-core-haiku-2a-killed
Cadence: 29315c4e64ff318a80a1a7d2c809beb4b3c15611
Packet sha256: f74940be43df79f6b3e98237453da559b0e1ce13ee49fa15bb9151488a95fe45

# Learnings: 20261021-P2-cadence-core-haiku-2a-killed

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
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|spec-driven|E1|infrastructure loss the worker restarted
- Change: The run stopped at E1: infrastructure loss the worker restarted. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@29315c4e64ff318a80a1a7d2c809beb4b3c15611 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | E1 | infrastructure loss: the worker restarted |
