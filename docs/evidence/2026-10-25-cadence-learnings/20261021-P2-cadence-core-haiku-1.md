RUN_BY_COMMAND: run-learnings
Run: 20261021-P2-cadence-core-haiku-1
Cadence: 29315c4e64ff318a80a1a7d2c809beb4b3c15611
Packet sha256: c8634bfe52286ee9f085b7d1d52ca081a925cde3cba711d88eb0c91054439d16

# Learnings: 20261021-P2-cadence-core-haiku-1

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
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|test-benchmark|P7|retries hard stop p# failed
- Change: The run stopped at P7: retries hard stop p# failed three times. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@29315c4e64ff318a80a1a7d2c809beb4b3c15611 --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | P7 | retries hard stop: P7 failed three times |
