RUN_BY_COMMAND: run-learnings
Run: 20261019-P2-cadence-core-haiku-1
Cadence: b1bbdcda7663ef08daf8fdeb2c6af853254016a9
Packet sha256: e6e5ae347d3fad6885e4b16d1d42304c3615ce05412d136d06084b292113ce6d

# Learnings: 20261019-P2-cadence-core-haiku-1

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
- Key: early-stop|spec-driven|E1|cut off by the host
- Change: The run stopped at E1: cut off by the host s # # s guard before phase. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@b1bbdcda7663ef08daf8fdeb2c6af853254016a9 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | E1 | cut off by the host's 7,200 s guard before phase 10 |
