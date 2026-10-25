RUN_BY_COMMAND: run-learnings
Run: 20261021-P2-cadence-core-haiku-2
Cadence: 29315c4e64ff318a80a1a7d2c809beb4b3c15611
Packet sha256: 1b54a8e7763174d585e156ba634de97d57b64b50014dbfd539fad06e7ca20e45

# Learnings: 20261021-P2-cadence-core-haiku-2

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
- Target: commands/commit-push-pr.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|commit-push-pr|E4|credentials hard stop no github
- Change: The run stopped at E4: credentials hard stop no github pr url under adapter none. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=commit-push-pr@29315c4e64ff318a80a1a7d2c809beb4b3c15611 --config new_skill=commit-push-pr@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | E4 | credentials hard stop: no GitHub PR URL under adapter none |
