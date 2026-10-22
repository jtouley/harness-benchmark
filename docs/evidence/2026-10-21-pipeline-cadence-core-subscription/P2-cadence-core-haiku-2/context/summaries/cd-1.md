# Session summary: cd-1

RUN_BY_COMMAND: session-summary
Pipeline-Run: c11abad2-208f-4d85-bb55-2a95c021b556

## Request

- Ship gh-1 end to end through R7, on branch feature/gh-1-pipeline. Source: `.context/proposals/cd-1.md` (sha256 854df8ca...).
- Build a Python 3.12 engine that reads `pipelines/*.yml` and writes a Parquet lake, then dbt (dbt-duckdb) marts under `out/marts/`.
- Question A (batch): FY2024 federal contract and grant money, total and per resident, by state, county, agency and month.
- Question B (stream): Wikipedia edits per wiki, namespace and 5-minute window, split human and bot, with net bytes added.
- No GitHub or Linear in this environment. PR text goes to `outputs/PR.md`, and the run continues as if the writes succeeded.

## What changed

Plan: `.context/plans/cd-1-gh-1-pipeline.plan.md` (sha256 0a523071...). Phase commits per `.context/implementation/cd-1_stage4.md` and the manifest commit list:

| Phase | Commit | Result (per the implementation document) |
|---|---|---|
| 0 | 92eee78 | Dependencies and `engine` package skeleton |
| 1 | 7c9272e | YAML schema validation with `file:line:col` problems |
| 2 | 3dc531e | Run loop, registries, Parquet lake sink with atomic swap and recovery |
| 3 | cd24c00 | USAspending, Census and sitematrix sources |
| 4 | 911a543 | polars and datafusion transforms |
| 5 | 775dbdb | SSE source, `stream_lake` sink with manifests and seen set |
| 6 | 4a1945f | `arrival_seq`, windows, edit rule, late rule, `late_events` |
| 7 | f966319 | `pipelines/build.yml`, `pipelines/stream.yml`, make targets |
| 8 | 659274d | dbt staging, dimensions, fact, Question A mart |
| 9 | aef8769 | `stream_edit_fact`, `mart_wiki_window_5min`, `late_events` view |
| 10 | b6ba463 | `oracle_map.yml`, Checks 1 to 7, acceptance run, DECISIONS.md |
| fix | edc56ea | R3 limits: complexity, duplication, bugs (7 files, 87 insertions and 87 deletions, per `git show --stat`) |

Also in the manifest: 4e102b4 (cadence config for the trial) and the phase 0 to 10 commits above.

User-visible change (per the implementation document):
- `make build` runs the batch path and writes the lake and `out/marts/`.
- `make stream DURATION=<seconds>` runs the stream path and the stream dbt models.

Verification reported in the implementation document (its own runs, not re-run here):
- `uv run pytest -q`: 84 passed.
- Two runs of `make build`: equal sorted content and schemas.
- Acceptance run: A1 to A8 and Checks 1 to 7 reported passed; the replay was reachable.

## Decisions

Nine decision records in `.context/proposals/cd-1-*.md`. Each file still says `status: proposed`.

- `cd-1-lake-layout`: one folder per table, temp folder then rename; load metadata is `_source_file` and `_source_row` only, with no wall-clock column.
- `cd-1-money-decimal`: `decimal128(18,2)` for source money; `obligations_per_person` is `decimal128(18,4)`, rounded half-even once at the end. The implementation document says the per-person division uses integer half-even arithmetic on cents.
- `cd-1-yaml-validation`: PyYAML compose for node marks, jsonschema Draft 2020-12, errors printed as `file:line:col: problem`.
- `cd-1-engine-interface`: registries keyed by `kind`; transforms name `polars` or `datafusion`; no dynamic plugin loader.
- `cd-1-population-vintage`: the July 1, 2024 estimate; fallback 2023, then 2022, then 2021 in the same file; a county missing from the 2024 file uses the 2021 file.
- `cd-1-geography-basis`: recipient location; missing or unmatched county goes to sentinel place (state `UNK`, county `00000`).
- `cd-1-stream-commit`: one manifest per micro-batch, `lake/_commits/stream_recentchange/<seq>.json`; the rename of the manifest is the commit.
- `cd-1-event-identity`: key is `meta.id`, first arrival kept; an edit has `type` `edit` or `new`.
- `cd-1-late-events`: late when the highest prior first-arrival `timestamp` is strictly greater than `window_end + 600`; the watermark is saved in each manifest.

Spec gaps answered by the plan (plan, "Weak scope, challenged", items 1 to 6):
- Census 2021 file as fallback only, with the fallback count measured in Phase 3.
- Connecticut planning-region gap: the implementation document reports 7 county codes on the 2021 population (68 rows, 7,212,018.08).
- Award key per file type: the plan requires a choice recorded in `DECISIONS.md`. The implementation document does not state the key chosen.
- Stream disconnect: `Last-Event-ID` resume plus dedupe on `meta.id`. The implementation document reports that the resume is inclusive, so the replayed event is dropped by the seen set.
- `make build` determinism: no wall-clock column.
- Lateness decided at ingest, with the watermark persisted in the manifest.

Deviations recorded in the implementation document (also in `DECISIONS.md` per that document): transforms have no `kind` (the key is `engine`); a `census_county_population` source kind was added; canary and malformed events are skipped; `make build` excludes stream models with `--exclude tag:stream`; the status file adds a `failed` value.

## Reviews

- Plan review, cycle 4: `.context/reviews/plan_cd-1-gh-1-pipeline.md`. Verdict READY TO EXECUTE. Last reviewed plan sha256 0a523071 matches the plan. Must-fix items: none. Notes are not blocking.
- Earlier plan review cycles (from the plan's revision ledgers, not separate documents in the manifest): cycle 1 (review 6698473c665c) READY WITH CHANGES, MF-1 to MF-5; cycle 2 (review aea71577045f) READY WITH CHANGES, MF-6 and MF-7; cycle 3 (review 6135ad33f49e) READY WITH CHANGES, MF-8. Cycle 4 records MF-6, MF-7 and MF-8 as closed. It does not re-check MF-1 to MF-5 in its own text.
- Adversarial review: no document in the manifest.
- Benchmark: no document in the manifest.
- PR review (R1): not run. The hard stop below stops the run before R1.
- Implementation review: the implementation document (`.context/implementation/cd-1_stage4.md`) is the only implementation record. It lists the R3 fix round as commit edc56ea.

## Findings

- No findings ledger and no PR review are in the manifest.
- Plan must-fix items MF-1 to MF-8 were closed in the plan, by amendments listed in the plan's revision ledgers. Each ledger row names the test or check that proves it. Those tests are named in the plan; this summary does not confirm they exist in code.
- Code findings: none recorded as must-fix in any document in the manifest. The R3 fix round (edc56ea) is the only code change recorded after the phase commits, and the manifest does not give its finding list.
- Plan review notes not applied, per the cycle 4 review: the Phase 2 exit text that says "A crash mid-write leaves the previous table readable" (MF-1 governs); the Phase 5 exit text on the replay fixture (MF-5 governs); the missing `last_arrival_seq` in the Phase 9 mart column list (needed for `contract: enforced: true`); and the `is_incremental()` guard for Phase 9. The implementation document does not say whether these were applied in code.

## Deferrals and open items

- Hard stop (manifest, credentials): the E4 draft PR cannot be opened. Origin is a local bare repo, `gh` rejects it, and `GH_TOKEN` is invalid. The draft-pr gate and R1 need a github.com pull-request URL, which this environment cannot produce. No PR URL was invented. PR text is at `outputs/PR.md`. The branch is pushed to origin at edc56ea (manifest).
- Non-blocking plan notes, not applied in the plan update (plan, cycle 1 update): rollback, rounding function, shared test helpers.
- Volume costs (plan review cycle 4 notes): the window mart recomputes keys from all on-time rows, and the seen-set rebuild scans every committed batch on start. Both costs grow with the stream. The plan states no expected volume.
- `duplicates_dropped` is a running total. After a restart it can differ from an uninterrupted run (plan review cycle 4 notes). A2 compares totals, not this counter.
- Replay: the implementation document records 60 late events from the replay runs, and reports the replay reachable throughout, so the blocked path did not apply.

## Next action

1. Fix GitHub access for this repo (a valid `GH_TOKEN` and a github.com remote, or a PR opened by a person from `outputs/PR.md`). Then run E4 again to get the draft PR URL. Do not write a PR URL by hand.
2. After the PR exists, run R1 (the PR review) on the branch.
3. Check the plan review notes against the code (the four unapplied notes above) before merge. Merge is not yet possible: the PR is not open and R1 has not run.
