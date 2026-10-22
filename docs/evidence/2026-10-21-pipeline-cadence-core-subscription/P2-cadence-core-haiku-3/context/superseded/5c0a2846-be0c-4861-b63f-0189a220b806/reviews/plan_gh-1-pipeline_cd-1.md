RUN_BY_COMMAND: plan-review
**Tracker:** none
**Ticket:** TICKET_SKIPPED (none: no tracker declared)
Ticket token: cd-1
Pipeline-Run: a4a4146f-ee60-4507-90b6-b015e00c812a

Last reviewed plan sha256: 3089051dfaf05d9081d5358df02335406245e4c5bb1160e15129d0252c132786

Verdict: READY TO EXECUTE

Plan: `.cursor/plans/gh-1-pipeline_cd-1.plan.md` (sha256 3089051d..., includes the test benchmark update with cd-1-F01 to cd-1-F06 applied; the minor findings cd-1-F07 to cd-1-F10 of the on-disk scorecard are noted below).
Inputs checked: `.context/vibetest/cd-1_2026-10-22.md` (sha256 692e057c..., NOT READY FOR PLANNING, G-1 to G-9); `.context/deferrals/cd-1_deferral-register.md` (`## Assumptions` has G-1 to G-9, each with a settling phase, and G-6 and G-7 name the MF-1 running-maximum rule); previous review `.context/reviews/plan_gh-1-pipeline_cd-1.md` (sha256 64db5863..., READY TO EXECUTE on plan sha256 9c87f15e..., no open MF-n; preserved as `.context/superseded/a4a4146f-ee60-4507-90b6-b015e00c812a/plan_gh-1-pipeline_cd-1_review-64db5863.md`); `.context/benchmarks/gh-1-pipeline_cd-1_plan.json` (on disk, sha256 1c39f9b3..., verdict PASS, mean 7.5, findings cd-1-F07 to cd-1-F10, all minor). Repo facts checked: no `engine/`, `scripts/`, `shared/` or `tests/` directory in the repo, so the helpers `engine/tests/support.py` and `engine/tests/conftest.py` written by cd-1-F01 duplicate nothing. `.cadence.json` gates `engine/`, `pipelines/`, `transform/` and `Makefile`.

## Status of earlier items

The previous review (64db5863) has no `MF-n` item, so there is no row to close. Its notes (DURATION path, fixture reset before each Phase 6 run, the `warehouse_path` default in the profile call, the `outputs/` path in the Phase 7 scope line) were carried to E1 as notes. Those notes are still open as notes, and none is a must-fix (see Notes below).

## Must-fix items

None.

## Review of the newest update (test benchmark) against the plan

Checked each rule of cd-1-F01 to cd-1-F06 for consistency with sections 1 to 7 and the earlier updates:

- cd-1-F01 (helpers): `support.py` in Phase 4 and `conftest.py` in Phase 5 are created before Phase 6 imports them. The users named (Phase 4, Phase 6, Phase 7) match the phases. Consistent. Pass.
- cd-1-F02 (expected values): the Phase 2 decimal sums are right (0.10 + 0.20 - 0.05 = 0.25; ten times 0.10 = 1.00). The G-2 failure row (2024-10-01 is outside FY2024, so the engine must fail) is right. The Phase 3 rounding test (0.25 / 2 = 0.125, which gives 0.13 half away from zero, and 0.12 under banker's rounding) is right. Pass.
- cd-1-F03 (checks 5 to 7): the tie order (12:10 with 3, then 12:00 with 2, then 12:05 with 2 by ascending `window_start`) matches N-5 and the cycle-four check 6 rule. Pass.
- cd-1-F04 (mutant rows): edit types match G-6; null length matches G-6 (0 byte delta, `has_length` false); window start matches the UTC floor of section 5. Pass.
- cd-1-F05 and cd-1-F06: the restart test and the integration split match section 7 Phase 6 and the exit criteria. Pass.

## Notes (not must-fix)

- Test benchmark source record: the ledger heading `## Revision ledger (scorecard 6acb5c150ea6)` and the update text ("verdict FAIL, mean 6.5, findings cd-1-F01 to cd-1-F06") cite a scorecard that is not on disk. The file on disk is `gh-1-pipeline_cd-1_plan.json` (sha256 1c39f9b3..., verdict PASS, mean 7.5, findings cd-1-F07 to cd-1-F10). Its own notes say the FAIL scorecard (plan sha e2c50302) carried F01 to F06. Cite the scorecard file that the ledger refers to, so the trail can be checked. E1 does not depend on it.
- Scorecard findings cd-1-F07 to cd-1-F10 (minor, benchmark verdict PASS) are not in the plan text. Each is a test-strengthening note for E1 to settle in the phase named, or for a later `/plan-update` at the orchestrator's choice:
  - cd-1-F07: N-1 population fallback has no named test. Add a parametrized case set (present in 2024; missing from 2024 and present in 2021; missing from both, NULL) in Phase 2 or Phase 3.
  - cd-1-F08: G-2 has one boundary case. Add the in and out boundary rows (2023-10-01 in, 2024-09-30 in, 2023-09-30 out, 2024-10-01 error).
  - cd-1-F09: Phase 6 "Dedupe test on event_id" has no name and no expected row count. Name it and give the expected count after one replayed `meta.id`.
  - cd-1-F10: check 3 (award key with two transactions) and check 6 (server filter) have no named fixture case. Add them to the Phase 4 and Phase 7 TDD text.
- Phase 1 marker: cd-1-F06 places the `integration` marker registration in Phase 1, but the Phase 1 scope and exit do not list it, and the update says it changes no phase scope except Phase 7 and section 4. Add the marker to the Phase 1 scope line. Without it, `-m integration` only warns.
- Ledger headings: `## Revision ledger (review 64db58631998)` appears twice (after the cycle-five update and after the test benchmark update). Both say no `MF-n` is open. Merge them into one heading so that a gate that reads the ledger by heading finds one section.
- Phase 6 stream runs (carried from cycle five): the plan still does not say how `DURATION` reaches the engine for `make stream`, and does not say how `DURATION` ends the fake-server run in tests. E1 names both. The restart test (cd-1-F05) runs the engine twice inside one test, so the reset of `transform/tests/fixtures/lake/stream_events/` must come before the test, not between its two runs.
- Phase 4 profile default (carried from cycle five): `transform/profiles.yml` renders from CLI `--vars` only. The default must be written in the call, `{{ var('warehouse_path', 'out/warehouse.duckdb') }}`, not only in `dbt_project.yml`. Otherwise `make build` fails at profile load. E1 applies this.
- Phase 7 output path: the scope line names `outputs/summary.md` and `outputs/PR.md`, but the cycle-four note places them in the run's `outputs/` directory (an additional working directory, outside the repo). Name which one E1 writes to. The plan itself names no host path, so the standalone rule holds.
- Phase 2 bucket text (cd-1-F02): "a US place with blank county FIPS gives county `UNKNOWN` and its own state" reads as if a new state is created. G-1 says the row stays in its own state. E1 uses the G-1 wording.
- The cd-1-F02 crash and disconnect tests assert `meta.id` values e1 to e10. The fake SSE fixture must set `meta.id` to those values, not only the SSE `id` field. E1 names this in the fixture.
- stages.json defines the pipeline blocks (A1 to A5, P1 and later), not the plan's phases 1 to 7. The phase order matches the P1 flow and the E1 quality gates in section 7. No mis-ordered phase.
- Gaps G-1 to G-9: each has a row in plan section 3, a row in the register `## Assumptions`, and a settling phase. Pass.
- Reuse and extension (section 4): the helpers written by the plan (`run_cli`, `hash_snapshot`, `fake_sse_server`) exist nowhere in the repo, and the section names the existing skeleton files it reuses. Pass.
- Standalone package: the plan names no host path. Pass.
- TDD, commit checkpoints, quality gates, rollback and blast radius: present. Pass.

## Edits not made

This review does not edit the plan. No plan update is needed before E1 for the must-fix list. The notes above are for E1 to settle, or for a later plan update at the orchestrator's choice.
