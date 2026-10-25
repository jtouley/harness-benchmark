RUN_BY_COMMAND: run-learnings
Run: 20261019-P1-cadence-core-haiku-1
Cadence: b1bbdcda7663ef08daf8fdeb2c6af853254016a9
Packet sha256: 2101eb3a55eb23a94c732ba2156c5b05a5545cfd9a3a54754387a6529b63f307

# Learnings: 20261019-P1-cadence-core-haiku-1

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
- Change: The run stopped at E4: credentials hard stop no github remote and no pr number. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=commit-push-pr@b1bbdcda7663ef08daf8fdeb2c6af853254016a9 --config new_skill=commit-push-pr@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | E4 | credentials hard stop: no GitHub remote and no PR number |
