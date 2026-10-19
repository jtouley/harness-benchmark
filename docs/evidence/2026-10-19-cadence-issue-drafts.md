# Cadence issue drafts from the cadence-core postmortem (19 October 2026)

Not filed: this session could not open `jtouley/cadence`, so neither these drafts nor Cadence's existing
issues have been checked against each other. Before filing, search Cadence's issues for duplicates.
Two defects the runs found are already fixed and are left out: the P9 gate counting applied must-fix
ids (`f6011df`), and no PR record without a forge (`f734888`). Evidence is on harness-benchmark branch
`ccr-3d2e0c73-lr6bdt` at `abb8c07`, under `docs/evidence/2026-10-19-pipeline-cadence-core/`. The
postmortem is [here](2026-10-19-cadence-core-postmortem.md).

## 1. R1's end-to-end walk starts from the code, not from what the spec says is delivered

In the third P1 run, five rounds of the local PR review (R1) found nine must-fix items, all in the stream
consumer's handling of odd input, and each was fixed with a test. No round compared the delivered
outputs with the spec's publish rule ("the marts are materialized as Parquet under `out/marts/`, one
folder per mart; anything downstream reads only `out/marts/`"). The answer map named seven views that
were never published, and the run scored 0 of 7. The same rounds raised the consumer's cognitive
complexity to 34.

Ask: the review rigor contract's end-to-end walk starts from the delivered artifacts the spec names (run
the build, list the outputs, read each check through them), and only then walks the code.

Evidence: `P1-cadence-core-haiku-3/context/prs/reviews/PR_REVIEW_local.md`, `grade.json`,
`oracle_map.yml`, `quality_metrics.json`.

## 2. The audit trail does not match the paths declared for it

harness-benchmark's `frameworks.lock.json` row for cadence-core (`audit_items`) declares where each audit
record is. For the third P1 run (`pipeline_run_id` `c3e98618-2811-4d93-a6d4-9efeb71c0d59`), the
committed `context/` has:

| Declared | Found |
|---|---|
| `.context/gates/entry-invariant-<id>.ok` | none for this id |
| `.context/prs/PR-<id>.md` | `prs/draft-pr-<id>.md` |
| `.context/findings/<task_id>.jsonl` | none (R1 wrote its items in the review file) |
| `.context/attest/<id>.jsonl` | none |

Either the evidence copy is incomplete, or the declaration does not match what Cadence writes. Ask:
make the paths the core writes match one declared set (or correct the declaration), and write the
findings ledger whenever R1 records findings, whatever file they also go in.

## 3. The plan-review loop always reaches its cycle limit

On all three Haiku runs, plan review ran five cycles, each returning `READY WITH CHANGES` with three to
five new must-fix items found in text the previous cycle added (MF-1 to MF-19 over five reviews on the
P1 rerun). The limit, not the reviewer, ended the loop: about 20 minutes and $0.12 to $0.15 a run.

Ask: look at why each cycle finds new items in the last cycle's additions, for example review only the
diff after cycle 1, or require a new item to cite text that changed.

## 4. (Lower priority) The acceptance step is sized by the orchestrator, not the plan

On P2 the orchestrator ran the plan's acceptance step as `make stream DURATION=3600`, a one-hour run the
plan did not require (it says `DURATION=<s>`), and the session was cut off before the export step.
Under harness-benchmark's criteria v2 a harness run has no time cap, so this would not cost a score
there. It still costs an hour. Ask: the orchestrator uses the plan's stated duration, or the shortest
run that covers what the acceptance step checks.
