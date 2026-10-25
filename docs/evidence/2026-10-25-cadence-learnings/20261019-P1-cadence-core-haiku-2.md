RUN_BY_COMMAND: run-learnings
Run: 20261019-P1-cadence-core-haiku-2
Cadence: b1bbdcda7663ef08daf8fdeb2c6af853254016a9
Packet sha256: dcfaf1b7db5994d16d05f2ca97b0baad31405a53a08d93e6c8e9b5afe67fc54b

# Learnings: 20261019-P1-cadence-core-haiku-2

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
- Target: SKILL.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|cadence|P9|retries hard stop at the
- Change: The run stopped at P9: retries hard stop at the p# entry invariant. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@b1bbdcda7663ef08daf8fdeb2c6af853254016a9 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | P9 | retries hard stop at the P9 entry invariant |
