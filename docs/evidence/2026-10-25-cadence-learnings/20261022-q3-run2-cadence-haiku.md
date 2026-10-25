RUN_BY_COMMAND: run-learnings
Run: 20261022-q3-run2-cadence-haiku
Cadence: fb0270d010cbfb284df5af992e1db36ed45cbeda
Packet sha256: 020b47833c4ba1519d0095a82bc8220a16062f45de845c3dcd36d412fbe15add

# Learnings: 20261022-q3-run2-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- fix-commit: 10
- gate: 6
- stop-point: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-8, E-9, E-10, E-11, E-12, E-13, E-14, E-15, E-16, E-17
- Rule: fix-commits
- Key: fix-commits|cadence|fix-commits
- Change: 10 fix commits followed E1 with no review finding recorded. The review records each defect it finds as a ledger finding, so that the fix has an id.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-8 | fix-commit | E1 | test: feat-local-4-csv-export-F03 narrow the pipe types for mypy |
| E-9 | fix-commit | E1 | fix: feat-local-4-csv-export-F03 a closed stdout pipe exits 1 without a traceback |
| E-10 | fix-commit | E1 | test: feat-local-4-csv-export-F03 closed stdout pipe prints no traceback (red) |
| E-11 | fix-commit | E1 | test: feat-local-4-csv-export-F01 export prints a negative amount with its sign |
| E-12 | fix-commit | E1 | fix: feat-local-4-csv-export-9c91f891-MF-2 format the magnitude and put the sign first |
| E-13 | fix-commit | E1 | test: feat-local-4-csv-export-9c91f891-MF-2 negative cents keep their sign (red) |
| E-14 | fix-commit | E1 | fix: feat-local-4-csv-export-F02 encode once before either output path |
| E-15 | fix-commit | E1 | test: feat-local-4-csv-export-F02 unencodable note on stdout is an error (red) |
| E-16 | fix-commit | E1 | fix: feat-local-4-csv-export-9c91f891-MF-1 encode before the file is opened |
| E-17 | fix-commit | E1 | test: feat-local-4-csv-export-9c91f891-MF-1 unencodable note with --out is an error (red) |
