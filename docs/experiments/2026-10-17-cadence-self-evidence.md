# What Cadence caught while it built Cadence (2026-10-10 to 2026-10-17)

**Interim operator evidence (unsourced in this repository).** The plans, reviews, scorecards and findings
ledger behind these counts are the operator's local Cadence records (`.context/...`, not public). Nobody can
check the counts against those records from this repository. The Cadence PRs they cite are public
([jtouley/cadence](https://github.com/jtouley/cadence)), so the counts can be checked against the public PRs
(their review comments, fix commits and merge dates), not against the local records. Severity is the
reviewer's word, not a re-grade; see [Honest limits](#4-honest-limits).

Written 2026-10-17 by a read-only pass over those records. No record changed.
All paths below are relative to the operator's local Cadence records (`.context/...`, not public).

## Headline numbers

| # | Number | Source |
|---|--------|--------|
| 1 | **85** must-fix findings caught and closed before merge, in the 10 Cadence runs that merged this week | tables below |
| 2 | **62 of 85 (73%)** were caught at plan time (P3, P6, P7), before any code | Section 2 |
| 3 | **23 of 85 (27%)** were caught at code review (R1, R2). E3 caught 0 must-fix | Section 2 |
| 4 | **0** must-fix findings of these runs were deferred. **0** reached main open | ledger + reviews |
| 5 | **112** must-fix in all 13 runs, open PRs and the unmerged run included (86 at plan time, 77%) | Section 2 |

## Scope and method

- Window: merged PRs from 2026-10-10 to 2026-10-17.
  Command: `gh pr list -R jtouley/cadence --state merged --limit 40 --json number,title,mergedAt`.
- A "run" is a task id with an `implementation/<task>.json` record (`task_id`, `pipeline_run_id`).
- Stage names: P3 plan review, P6 adversarial review, P7 test benchmark of the plan,
  E3 architecture conformance, R1 PR review, R2 test benchmark of the code.
- How each stage was counted:
  - **P3**: `MF-n` items per review cycle. The review file is overwritten each cycle.
    So the per-cycle lists come from the `## Update Rn` header lines and the Revision Ledger in `plans/<plan>.plan.md`.
    Example: `grep -n 'Review applied' plans/go_java_c_ci_cd-100_0c33.plan.md`.
  - **P6**: blocking items (`B-n`) only. Conditions (`C-n`) are shown in their own column.
    They had to ship in the PR, but the reviewer did not call them blocking.
    Source: `adversarial/adversarial_<plan>*.md`, plus the plan Revision Ledger when a report was overwritten (cd-58).
  - **P7**: ledger rows with `stage: test-benchmark-plan` and `severity: must-fix`, cross-checked against the plan's `Update Rn` line for P7.
  - **E3**: ledger rows with `stage: architecture-review-impl`. All are `nit`. Each run has a gate file `gates/architecture-review-impl-<run>.json`.
  - **R1**: the must-fix or "Required" items in `prs/reviews/PR_REVIEW_#<n>.md`.
  - **R2**: ledger rows with `stage: test-benchmark-pr` or `test-benchmark-code` and `severity: must-fix`.
- Ledger dump: `python3 -c "import json;[print(json.loads(l)['id'],json.loads(l)['stage'],json.loads(l)['severity'],json.loads(l)['status']) for l in open('findings.jsonl')]"`.

## 1. One table per run

Column key: P3 / P6 (B) / P7 / E3 / R1 / R2 are must-fix counts. "P6 C" is P6 conditions (not counted as must-fix).
"Closed before merge" means: P3 and P6 items were closed in a later cycle or carried into an E1 phase.
R1 and R2 items were fixed on the PR branch, and a re-review or a ledger `verified` row shows it.

### Merged runs

| Task | PR | Stages run | P3 | P6 (B) | P6 C | P7 | E3 | R1 | R2 | Must-fix | Closed before merge | Ledger `verified` | Deferred with ticket |
|------|----|------------|----|--------|------|----|----|----|----|----------|---------------------|-------------------|----------------------|
| cd-47 | [#52](https://github.com/jtouley/cadence/pull/52) | P3 x5, P6, P7, E3, R1, R2 | 6 | 0 | 4 | 0 | 0 | 2 | 2 | **10** | 10 | 4 (F2-F5) | 0 |
| cd-58 | [#62](https://github.com/jtouley/cadence/pull/62) | P3 x5, P6 x2, P7, E3, R1, R2 | 4 | 1 | 8 | 0 | 0 | 1 | 4 | **10** | 10 | 4 (F30-F33) | 0 |
| cd-64 | [#75](https://github.com/jtouley/cadence/pull/75) | P3 x3, P6, P7, E3, R1, R2 | 6 | 0 | 4 | 0 | 0 | 0 | 2 | **8** | 8 | 2 (F10, F11) | 0 |
| cd-53 | [#74](https://github.com/jtouley/cadence/pull/74) | P3 x4, P6, P7, E3, R1, R2 | 4 | 0 | 7 | 0 | 0 | 0 | 2 | **6** | 6 | 2 (F9, F10) | 0 |
| cd-76 | [#81](https://github.com/jtouley/cadence/pull/81) | P3 x3, P6, P7 x2, E3, R1, R2 | 4 | 0 | 6 | 1 | 0 | 0 | 2 | **7** | 7 | 3 (F31, F41, F42) | 0 |
| cd-63 | [#88](https://github.com/jtouley/cadence/pull/88) | P3 x5, P6 x3, P7, E3, R1, R2 | 6 | 3 | 9 | 1 | 0 | 2 | 2 | **14** | 14 | 5 (F8, F10-F13) | 0 |
| cd-82 | [#87](https://github.com/jtouley/cadence/pull/87) | P3 x7, P6, P7 x2, E3, R1, R2 | 8 | 0 | 3 | 1 | 0 | 1 | 0 | **10** | 10 | 1 (F01) | 0 |
| cd-84 | [#91](https://github.com/jtouley/cadence/pull/91) | P3 x5, P6, P7, E3, R1 x3, R2 x3 | 5 | 0 | 6 | 0 | 0 | 2 | 1 | **8** | 8 | 1 (F07) | 0 |
| cd-93 | [#95](https://github.com/jtouley/cadence/pull/95) | P3 x4, P6 x2, P7, E3, R1, R2 | 5 | 1 | 6 | 0 | 0 | 0 | 0 | **6** | 6 | 0 | 0 |
| cd-49 | [#114](https://github.com/jtouley/cadence/pull/114) | P3 x2, P6, P7 x2, E3, R1, R2 | 5 | 0 | 4 | 1 | 0 | 0 | 0 | **6** | 6 | 1 (F01) | 0 |
| **Sum** | | | **53** | **5** | 57 | **4** | **0** | **8** | **15** | **85** | **85** | **23** | **0** |

### Runs not merged yet (shown for completeness, not in the 85)

| Task | PR | Stages run | P3 | P6 (B) | P6 C | P7 | E3 | R1 | R2 | Must-fix | Fixed on branch | Ledger | Deferred |
|------|----|------------|----|--------|------|----|----|----|----|----------|-----------------|--------|----------|
| cd-100 | [#118](https://github.com/jtouley/cadence/pull/118) (open) | P3 x4, P6 x3, P7 x2, E3, R1 x2, R2 | 6 | 2 | 10 | 1 | 0 | 1 | 0 | **10** | 10 | F21, F29 `verified` | 0 |
| cd-92 | [#126](https://github.com/jtouley/cadence/pull/126) (open) | P3 x3, P6, P7, E3, R1, R2 x2 | 5 | 0 | 2 | 0 | 0 | 1 | 1 | **7** | 7 | F2, F3 `verified` | 0 |
| cd-66 | none yet | P3 x5, P6 x3, P7, E3 | 7 | 2 | 13 | 1 | 0 | - | - | **10** | plan text only | F20 still `open` in ledger | 0 |

### Where each number comes from

- **cd-47**: P3 cycles 1-4 had MF 2+1+2+1 (`plans/review_independence_cd-47_b7a3.plan.md` line 25). P6: `adversarial/adversarial_review_independence_cd-47_b7a3.md`, "None" blocking, conditions 1-4. R1: R-1, R-2 (`prs/reviews/PR_REVIEW_#52.md` lines 15, 30, 36) = ledger cd-47-F2, F3. R2: cd-47-F4, F5.
- **cd-58**: P3 MF-1 to MF-4 (cycles 3-5). Cycles 1-2 had only SF and N rows (`plans/peer_models_cd-58_6f3e.plan.md` Revision Ledger, lines 377-413). P6 round 1 B-1 "fork call runs on the parent model" (same file, line 386). Final P6 report: no blocking, C-1 to C-4. P7: `test-benchmarks/cd-58_2026-10-12.md` F1-F13 are MEDIUM or LOW (older scale), so 0 must-fix. R1: MF-1 (`PR_REVIEW_#62.md` line 20), closed ("Open must-fix: 0", same file). R2: cd-58-F30 to F33.
- **cd-64**: P3 cycle 1 "5 must-fix", cycle 2 MF-6 (`plans/claude_lean_record_cd-64_83f5.plan.md` lines 328, 514). P6: C-1 to C-4, no blocking. R1: "Must-fix: 0" (`PR_REVIEW_#75.md`). R2: cd-64-F10, F11.
- **cd-53**: P3 cycle 1 MF-1 to MF-3, cycle 2 MF-1, cycles 3-4 none (`reviews/plan_peer_shadows_cd-53*.md`). P6: C1-C7. R1: "Must-fix: 0" (`PR_REVIEW_#74.md`). R2: cd-53-F9, F10.
- **cd-76**: P3 cycle 1 MF-1 to MF-4, cycle 2 notes only (`plans/run_scoped_records_cd-76_281f.plan.md` lines 321, 474). P6: C1-C6. P7: cd-76-F31. R1: "Must-fix: none" (`PR_REVIEW_#81.md`). R2: cd-76-F41, F42.
- **cd-63**: P3 cycle 1 MF-1 to MF-4, cycle 5 MF-1, MF-2, cycles 2-4 nits only (`plans/p6_cycle_limit_cd-63_cd15.plan.md` lines 328, 449, 581, 693, 791). P6: B-1 in each of 3 rounds (same file, lines 448, 580, 692). P7: cd-63-F8. R1: cd-63-F10, F11 (`PR_REVIEW_#88.md` lines 19, 160, 185). R2: cd-63-F12, F13.
- **cd-82**: P3 MF per cycle 1+2+2+1+1+1, then 0 (`plans/host_workspace_cd-82_fb90.plan.md` Revision Ledger lines 329-350). P6: C1-C3. P7: cd-82-F01. R1: R1 "payload cwd hides the host project" (`PR_REVIEW_#87.md` line 93), resolved in 585ba6a (line 223). R2: PASS with one HIGH item, not must-fix (`test-benchmarks/gh-82-pr87_2026-10-14.md` line 15).
- **cd-84**: P3 MF-1 to MF-3 (cycle 1), MF-4 (cycle 3), MF-5 (cycle 5) (`plans/pi_gates_cd-84_76ac.plan.md` lines 427-736). P6: no `B-n`. C1-C6. C1 and C2 carry the label "must-fix" in the report (`adversarial/adversarial_pi_gates_cd-84_76ac.md` lines 49, 59), but they are not counted here. R1: R1, R2 Required (`PR_REVIEW_#91.md` line 13), "Must fix before merge: none" after the fix (line 314). R2: cd-84-F07.
- **cd-93**: P3 MF-1 to MF-4, then MF-5 (`plans/a5_run_scope_cd-93_cceb.plan.md` lines 210, 348). P6 round 1 B-1, C-1 to C-4. Round 2 C-1, C-2 (line 417, 522). R1: "no must-fix items" (`PR_REVIEW_#95.md`). R2: 0.
- **cd-49**: P3 MF-1 to MF-5 (`plans/run_scoped_closure_cd-49_77d3.plan.md` line 243). P6: C-1 to C-4, no blocking (line 344). P7: cd-49-F01. R1: "no must-fix items" (`PR_REVIEW_#114.md`). R2: 0.
- **cd-100**: P3 cycle 1 MF-1 to MF-5, cycle 3 MF-1 (`plans/go_java_c_ci_cd-100_0c33.plan.md` lines 297, 556). P6 round 1 B-1, B-2 (line 424). P7: cd-100-F21. R1: cd-100-F29 (`PR_REVIEW_#118.md` line 15).
- **cd-92**: P3 cycle 1 MF-1 to MF-4, cycle 2 MF-1 (`reviews/plan_set_check_cd-92_dece*.md`). P6: C-1, C-2. R1: cd-92-F2 (`PR_REVIEW_#126.md` line 20). R2: cd-92-F3.
- **cd-66**: P3 MF-1 to MF-7 over 5 cycles (`reviews/plan_verdict_stage_peer_cd-66_e84b*.md`). P6 round 1 B-1, B-2 (`plans/verdict_stage_peer_cd-66_e84b.plan.md` line 776). P7: cd-66-F20 (line 1279).

### Merged PRs in the window that were not Cadence runs

[#128](https://github.com/jtouley/cadence/pull/128), [#116](https://github.com/jtouley/cadence/pull/116), [#101](https://github.com/jtouley/cadence/pull/101), [#97](https://github.com/jtouley/cadence/pull/97) and [#57](https://github.com/jtouley/cadence/pull/57) have no `implementation/<task>.json`. They are not in the tables.
[#128](https://github.com/jtouley/cadence/pull/128) had an R1-style review: APPROVE, no must-fix (`PR_REVIEW_#128.md`). [#57](https://github.com/jtouley/cadence/pull/57): no Critical or Required (`PR_REVIEW_#57.md`).

## 2. Totals for the week

### Merged runs (10 runs, 10 PRs)

| Stage | Must-fix caught | Share |
|-------|-----------------|-------|
| P3 plan review | 53 | 62% |
| P6 adversarial (blocking) | 5 | 6% |
| P7 test benchmark, plan | 4 | 5% |
| **Plan time, before any code** | **62** | **73%** |
| E3 architecture conformance | 0 | 0% |
| R1 PR review | 8 | 9% |
| R2 test benchmark, code | 15 | 18% |
| **Code review** | **23** | **27%** |
| **Total** | **85** | 100% |

- All 85 were closed before merge. None was deferred.
- 23 of the 85 have a ledger row with status `verified` (a check re-ran).
  The other 62 are closed by text: a later review cycle marks them "Closed", or the plan carries them to a phase test.
- P6 conditions add 57 more required changes. They are not counted as must-fix.

### All 13 runs (adds cd-100, cd-92 and cd-66)

| Stage | Must-fix |
|-------|----------|
| P3 | 71 |
| P6 (B) | 9 |
| P7 | 6 |
| E3 | 0 |
| R1 | 10 |
| R2 | 16 |
| **Total** | **112** |

Plan time: 86 of 112 (77%). Code review: 26 of 112 (23%).

## 3. Five defects a stage caught that the tests did not

Each one: the test suite passed, and the stage found a real defect with a reproduction.

1. **cd-100-F29 (R1, PR [#118](https://github.com/jtouley/cadence/pull/118)).** A Go function literal with a result type, passed as a call argument, was not scored as nested. The Go 1.27.1 stdlib has 2,120 such closures (for example `sort.Slice(xs, func(i, j int) bool {`). The full suite had passed: 2561 passed, 1 skipped.
   Artifact: `prs/reviews/PR_REVIEW_#118.md` lines 15, 26, 70. Fix 916f3dc, ledger row `verified`.
2. **cd-84 R1 (PR [#91](https://github.com/jtouley/cadence/pull/91), finding R1, not in the ledger).** The Pi extension mapped the `powershell` tool to `Bash`. The shell parser reads only POSIX syntax, so `Set-Content -Path src/a.py` before P9 was ALLOWED (fail open). The Pi tests had all passed. The fixture for that tool held a `sed -i` command, not a PowerShell write.
   Artifact: `prs/reviews/PR_REVIEW_#91.md` lines 28, 108-116. Fixed in b00c1f2 (line 228).
3. **cd-82 R1 (PR [#87](https://github.com/jtouley/cadence/pull/87), finding R1, not in the ledger).** On Cursor, a payload `cwd` hid `CURSOR_PROJECT_DIR` and `workspace_roots` from every guard. A shell call from outside the project could write a gated file by absolute path before P9. The full suite passed at the PR head.
   Artifact: `prs/reviews/PR_REVIEW_#87.md` lines 11, 93, 223. Fixed in 585ba6a.
4. **cd-47-F2 (R1, PR [#52](https://github.com/jtouley/cadence/pull/52)).** The PR guard did not see `gh pr create` on a new line, inside `{ }`, after `env`, or by absolute path. The hook allowed all four forms. The full suite had passed (1296 passed at 55860d9).
   Artifact: `prs/reviews/PR_REVIEW_#52.md` lines 19, 30-33. Fixed in fe84361, ledger row `verified`.
5. **cd-92-F2 (R1, PR [#126](https://github.com/jtouley/cadence/pull/126)).** The new `set-check` command let a fixer replace the reviewer's check with `test -d .`. The ledger then promoted the row to `verified` and `closure.py --check` exited 0 with no fix. The full suite passed at the head.
   Artifact: `prs/reviews/PR_REVIEW_#126.md` lines 14-26. Fix 88da3e8, ledger row `verified`.

Spare example (a test that could not fail): **cd-64-F11 (R2)**. `assert code == 0, err and decision(out) == "allow"` put the decision check into the assert message, so Python never ran it. Ledger `evidence` field; fix 4203cbd.

## 4. Honest limits

- **Severity is the reviewer's claim.** "Must-fix", "Required" and "blocking" are words in a peer's report. No person re-graded them.
- **Counts come from text and ledger rows.** The P3, P6 and R1 counts come from Markdown ids (`MF-n`, `B-n`, `R-n`), not from a database. A different reader could count conditions or "Required" test gaps in a different way.
- **Ledger coverage is partial.** `findings.jsonl` has 55 rows. Most are P5, E3, P7 and R2 rows. P3 and P6 items are not in the ledger. Four R1 must-fix items are only in the review text: [#62](https://github.com/jtouley/cadence/pull/62) MF-1, [#87](https://github.com/jtouley/cadence/pull/87) R1, [#91](https://github.com/jtouley/cadence/pull/91) R1 and R2. One row (`CADENCE-F1`) is in the file twice. Ledger ids skip numbers (for example cd-58-F2 to F29), because scorecards number their own findings.
- **Overwritten artifacts.** Each plan review and each scorecard file is rewritten per cycle. So earlier cycles are counted from the plan's `Update Rn` lines and Revision Ledger, not from the original report. The first cd-58 P6 report (the one with B-1) is gone. Only the plan ledger line records it.
- **"Closed" is not always "verified".** 62 of the 85 merged must-fix items are closed by a later review's status table or a carry table, not by a re-run check in the ledger.
- **Two scales.** cd-47 and cd-58 P7 scorecards use HIGH/MEDIUM/LOW. Those are counted as 0 must-fix.
- **Window edge.** cd-47 plan reviews ran on 2026-10-10. Its PR merged on 2026-10-11.
- **Missing artifacts:**
  - cd-82: no `benchmarks/cd-82_code.json`. R2 comes from `test-benchmarks/gh-82-pr87_2026-10-14.md`.
  - cd-66: no PR, no PR review, no code scorecard, no summary. cd-66-F20 is still `open` in the ledger, but plan Update R10 applied it.
  - No summary for cd-58 or cd-92.
  - Phase logs exist only for cd-100, cd-49 and cd-93 (`implementation/*_phase-log.md`).
  - No P3 review file for cd-58 cycles 1-2, cd-63 cycles 1-4 or cd-84 cycles 1-4 (overwritten).
- **No control group.** This does not show that the bugs would have shipped without Cadence. It shows that the stages found them and the tests did not.
