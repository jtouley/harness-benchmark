RUN_BY_COMMAND: run-learnings
Run: 20261021-P1-cadence-core-haiku-0-killed
Cadence: 29315c4e64ff318a80a1a7d2c809beb4b3c15611
Packet sha256: b65ba761023ccc03c3f6ccec5c23b767e1917c34592d5b925baaebe4a35fc2f6

# Learnings: 20261021-P1-cadence-core-haiku-0-killed

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
- Key: early-stop|spec-driven|E1|infrastructure loss the cloud container
- Change: The run stopped at E1: infrastructure loss the cloud container was reclaimed while idle. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@29315c4e64ff318a80a1a7d2c809beb4b3c15611 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | E1 | infrastructure loss: the cloud container was reclaimed while idle |
