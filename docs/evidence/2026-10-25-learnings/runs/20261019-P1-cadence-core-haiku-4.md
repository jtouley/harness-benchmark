RUN_BY_COMMAND: run-learnings
Run: 20261019-P1-cadence-core-haiku-4
Cadence: 4af76ac7c26de279a066195f1e39993e7f0d093e
Packet sha256: 1d30946bc2aa68236a70ef6208323e813d3226ddfd4334499f82ee61fa572efd

# Learnings: 20261019-P1-cadence-core-haiku-4

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
- Target: commands/pr-review-local.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|pr-review-local|R1|cut off by the operator
- Change: The run stopped at R1: cut off by the operator s two-hour shell limit during the r# fix round. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=pr-review-local@4af76ac7c26de279a066195f1e39993e7f0d093e --config new_skill=pr-review-local@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | R1 | cut off by the operator's two-hour shell limit during the R1 fix round |
