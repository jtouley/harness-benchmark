RUN_BY_COMMAND: run-learnings
Run: 20261022-q2-run2-cadence-haiku
Cadence: fb0270d010cbfb284df5af992e1db36ed45cbeda
Packet sha256: e30f4971c41e1e2b463a825e7f4426b48d3b0c7111994e4ff5455adc88e7e0df

# Learnings: 20261022-q2-run2-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- finding: 5
- fix-commit: 17
- gate: 25
- hard-stop: 1
- stop-refusal: 2

## Proposals

### L-1
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-8, E-9, E-10, E-18, E-19, E-34, E-35, E-36, E-37, E-38, E-39, E-40, E-41, E-42, E-43, E-44, E-45, E-46, E-47, E-48, E-49, E-50
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 5 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-32
- Rule: hard-stop
- Key: hard-stop|cadence|R4|retries
- Change: R4 recorded a `retries` hard stop: r# open mf-# must-fix. the fix peer reports blocked it needs a. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: SKILL.md
- Status: candidate
- Evidence: E-27, E-28
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 2 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-8 | finding | pr-review-update | The MF-1 refusal compares resolved paths, so a hard link to the ledger passes it. Repro at b81d04a: cp the ledger to h.json, ln -f h.json alias.json, budgetcli --file h.json export --out alias.json exits 0 and h.json holds CSV text. Fix: also refuse when os.path.samefile(args.out, ledger.path). Cross-ref MF-1. |
| E-9 | finding | pr-review-update | A stored amount_cents of 1e400 loads as inf. int(inf) raises OverflowError, which the except clause in Ledger.load does not catch. Repro at b81d04a: export exits 1 with a traceback. Fix: add OverflowError to the except tuple. Cross-ref MF-4. |
| E-10 | finding | pr-review-update | Ledger.load does not check the type of category or note. A row with category null and note 5 exports 2026-10-01,,0.05,5 with exit 0 and no error line. Fix: Ledger.load raises ValueError for a non-string category or note, so cli prints an error line and exits 2. |
| E-18 | finding | pr-review-update | Ledger.load does not check the type of category or note. A row with category null and note 5 exports 2026-10-01,,0.05,5 with exit 0 and no error line. Fix: Ledger.load raises ValueError for a non-string category or note, so cli prints an error line and exits 2. |
| E-19 | finding | pr-review-update | The MF-9 fix in _is_ledger calls out.exists() before the write. For an --out in a directory the process cannot search, exists() raises PermissionError, so export prints a traceback with exit 1. At b81d04a the write handler printed error: cannot write and exited 2. Fix: treat an OSError in the samefile or exists check as not the ledger, so the write reports the error. |
| E-27 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 2 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-28 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message is not a lean return (ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>). Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-32 | hard-stop | orchestrator | R4 open: MF-5 must-fix. The fix peer reports BLOCKED: it needs a plan-level repin or an author decision. Five fix rounds ran; the last one changed nothing on MF-5. |
| E-34 | fix-commit | E1 | fix: feat-local-4-csv-export-dda983fd-MF-12 --out in an unsearchable directory is an error line |
| E-35 | fix-commit | E1 | test: feat-local-4-csv-export-dda983fd-MF-12 --out in an unsearchable directory is an error line (red) |
| E-36 | fix-commit | E1 | fix: feat-local-4-csv-export-dda983fd-MF-11 a stored category or note that is not text is an error line |
| E-37 | fix-commit | E1 | test: feat-local-4-csv-export-dda983fd-MF-11 a stored category or note that is not text is an error line (red) |
| E-38 | fix-commit | E1 | fix: feat-local-4-csv-export-dda983fd-MF-10 an infinite stored amount is an error line |
| E-39 | fix-commit | E1 | test: feat-local-4-csv-export-dda983fd-MF-10 an infinite stored amount is an error line (red) |
| E-40 | fix-commit | E1 | fix: feat-local-4-csv-export-dda983fd-MF-9 --out through a hard link to the ledger is refused |
| E-41 | fix-commit | E1 | test: feat-local-4-csv-export-dda983fd-MF-9 --out through a hard link keeps the ledger (red) |
| E-42 | fix-commit | E1 | test: feat-local-4-csv-export-dda983fd-MF-2 narrow the pipe types for the R3 type gate |
| E-43 | fix-commit | E1 | fix: feat-local-4-csv-export-dda983fd-MF-3 an unencodable note is an error line |
| E-44 | fix-commit | E1 | test: feat-local-4-csv-export-dda983fd-MF-7 unloadable or unencodable rows are an error line and exit 2 |
| E-45 | fix-commit | E1 | fix: feat-local-4-csv-export-dda983fd-MF-4 a stored row the ledger cannot read is an error line |
| E-46 | fix-commit | E1 | test: feat-local-4-csv-export-dda983fd-MF-4 a stored row the ledger cannot read is an error line (red) |
| E-47 | fix-commit | E1 | fix: feat-local-4-csv-export-dda983fd-MF-2 closed stdout pipe exits without a traceback |
| E-48 | fix-commit | E1 | test: feat-local-4-csv-export-dda983fd-MF-2 closed stdout pipe exits without a traceback (red) |
| E-49 | fix-commit | E1 | fix: feat-local-4-csv-export-dda983fd-MF-1 refuse --out equal to the ledger path |
| E-50 | fix-commit | E1 | test: feat-local-4-csv-export-dda983fd-MF-1 export --out refuses the ledger path (red) |
