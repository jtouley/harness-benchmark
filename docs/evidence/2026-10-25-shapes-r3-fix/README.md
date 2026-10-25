# The shapes-r3 fix: evidence

This is the evidence for the cadence branch `fix/shapes-r3`, jtouley/cadence#234, head `fdfb554c001c2ac2a05aea51476898b55748617d`. It fixes each stop of
batch 2026-10-25-shapes-r3, which ran on cadence `9fafe09` (#233). The cadence PR is not merged. Merging it is the
owner's decision.

- **Produced by:** the shapes-r3 fix agent (a subagent of the coordinator), 2026-10-25.
- **Inputs read:** the postmortem front matter and its update log from Oct 25 07:00, the diagnosis diff
  `shapes-r3-fix-9fafe09.diff`, and the twelve records `runs/20261025-*` (#138 to #149) with their stored
  transcripts and trees (runs-store).
- **No benchmark run** was started. All checks ran on stored trees, toy repos, or the dev replay on localhost.

| File | What it is |
|---|---|
| `tests/table.md`, `tests/results-*.txt` | The regression tests on `9fafe09`, on `9fafe09` plus the diagnosis diff, and on the branch |
| `r3-gate-replay/table.md`, `r3-gate-replay/<run>.<code>.txt` | The P1 and P4 gates (`--check`) on the stored `.context` of each of the 12 shapes-r3 trees, for the three code versions |
| `r2-stream-gate/table.md`, `r2-stream-gate/<run>.json` | The enforcement gate on the 11 stored shapes-r2 trees, with the branch's Cadence (the method of `2026-10-25-stack`) |
| `verify-toy.md` | `/verify` (cadence:verify): the sandbox install, the Cursor hooks, and the core gates A1 to R7 on a toy repo |
| `ci_local.log` | `scripts/ci_local.sh` at the head, with its own TMPDIR |
| `bin/` | The scripts that produced these files |

## The stops, and why (from the records and transcripts)

| Run | Record | Score | Stop | Cause | Regression tests |
|---|---|---|---|---|---|
| P1 core-1 | #138 | 0/7 | P1 | The stop guard re-ran the P1 gate on P4's text (P1/P4 loop). P9 refused a bare `DURATION=600` and a `not run` row with `trade-off:` in its Why cell | `test_after_p4_..._text_to_p4[core-1]`, `test_p1_gate_costs_each_timed_command_once[core-1]`, `test_core_1_a_bare_value_is_not_a_command` |
| P1 full-3 | #139 | 0/7 | P1 | P1/P4 loop: P4 narrowed acceptance row 6 (tie-break) in place. Its `plan-update` mark is on line 200 | `test_after_p4_..._text_to_p4[full-3-core-3]` |
| P2 core-3 | #140 | 0/7 | P1 | P1/P4 loop: P4 put a note in row 5's check cell. Mark on line 230 | same |
| P2 full-3 | #141 | 0/7 | "A1" | The work deny on a read-only `seq`/`sleep` poll, and the deny text matched the max_tokens hard-stop row | `test_full_3_a_read_only_poll_is_not_block_work`, `test_full_3_the_work_deny_does_not_read_as_the_max_tokens_hard_stop` |
| P1 full-2 | #142 | 0/7 | "A1" | The work deny on `P=<root>/scripts; python3 $P/plan_update_gate.py`. P1/P4 loop with the mark on line 6 | `test_full_2_a_gate_check_through_a_variable_is_not_block_work`, `test_after_p4_..._text_to_p4[full-2]` |
| P2 full-2 | #143 | 0/7 | P4 | The 4 min P4 budget against 4.8 min used | `test_full_2_block_budgets_cover_the_slowest_observed_call` |
| P2 full-1 | #144 | 0/7 | P1 | A `make stream DURATION=600 && pytest` gate needed its own row. The 3600 s row is a real refusal | `test_p1_gate_costs_each_timed_command_once[full-1]`, guard `test_a_long_row_without_a_waiver_still_fails` |
| P2 core-2 | #145 | 0/7 | E1 | `STOPPED` with phases open. E1 had no allowed wait for its 600 s gate. The second dispatch wrote its E1 document early, was then locked out, and its hand-back was denied eight times | `test_core_2_*` in `test_shapes_r3_e1.py`, `test_the_wait_*` |
| P1 core-2 | #146 | 0/7 | E1 | `STOPPED` twice with phases open; each hand-back killed the background 600 s stream run | `test_core_2_a_stopped_return_with_phases_open_is_refused`, `test_the_third_refused_return_is_a_recorded_supervisor_stop` |
| P1 core-2, P2 core-2 | | 0/7 | | The plans wrote `oracle_map.yml` and `DECISIONS.md` in their last phase, and the trees have neither | `test_p1_fails_while_the_first_phase_does_not_write_the_specs_outputs`, `test_the_specs_outputs_are_its_outputs_list_only`, `test_the_first_phase_is_the_lowest_number` |
| P1 full-1 | #147 | 2/7 | "A1" | At 94790 tokens the max_tokens deny fell on the dispatch of the next block and named `--hard-stop context`. The context grew from the orchestrator's reads: two read-only commands were taken for block work (`grep -c ""`, `find \(`), so it read the plan with Read, and it read Cadence's source while fixing the P1/P4 loop | `test_full_1_*` in `test_shapes_r3_late_stops.py` |
| P2 core-1 | #148 | 5/7 | E1 | The fix-round peer got E1's packet and made no fix. The retry with the review path was refused as not lean | `test_core_1_*` in `test_shapes_r3_late_stops.py` |
| P1 core-3 | #149 | 0/7 | "A1" | At 85255 tokens the work deny fell on `python3 -I -c` reading a report (the flag before `-c`), and the model took it as a hard stop. Its graded tree has `oracle_map.yml` and `DECISIONS.md`, so its 0/7 is not the missing-deliverable failure | `test_core_3_*` in `test_shapes_r3_late_stops.py` |

"A1" in a record's stop label comes from the harness, not from Cadence: `scripts/host_trial.py` `rebind_sessions`
skips a completed session, so after R7 `headless.py next` fails at A1 with "no active cadence session". The real
stop is in the reason text. This is read from the code and was not changed; it is a harness item.

## Results

- **Regression tests** (`tests/table.md`): 37 regression tests fail on `9fafe09` and pass on the branch. 28 of
  them also fail on `9fafe09` plus the diagnosis diff alone. 12 guards pass on all three, as they should. On the
  branch, 49 of 49 pass.
- **ci_local** (`ci_local.log`, head `fdfb554`, its own TMPDIR, `UV_OFFLINE=1`, node 24 from the npm cache):
  4650 passed and 2 skipped on Python 3.11 and on 3.13, then the complexity job; `ci_local: all CI steps passed at
  fdfb554`. The pre-push hook ran it again for the push.
- **/verify** (`verify-toy.md`): the install is idempotent, the three Cursor hook states hold, and each core gate
  from A1 to R7 behaves as its doc says on the toy run, including the new Deliverables, P1/P4 and fix-round paths.
- **Stored shapes-r3 trees** (`r3-gate-replay/table.md`): after P4, the branch's P1 gate passes on each of the 10
  trees where P4 wrote its mark (9fafe09: 4 of 10, the diagnosis diff: 6 of 10). P4's gate now carries the text
  checks of P4's own rows, and the new Deliverables check fails on all 12.
- **Stored shapes-r2 trees** (`r2-stream-gate/table.md`): the gate's stream verdict after the build matches the
  recorded `stream_ok` on **11 of 11** trees at `DURATION=400`. The fresh-clone and output columns have the same
  verdicts as `2026-10-25-stack/table.md` (only connection counts differ). This branch does not change
  `clean_checkout.py` or `entry_points.py`.

## Verified and inferred

- **Verified (tool output in this folder):** each test result in `tests/`, each gate verdict in `r3-gate-replay/`
  and `r2-stream-gate/`, the `/verify` steps, and ci_local. The causes in the table come from the transcripts,
  read with `bin/view.py` and quoted by line in the commit messages.
- **Verified on stored data:** the fix-round pointer that the branch builds from P2 core-1's own ledger names
  MF-1 to MF-6, F20 and F21. On the branch, none of the 67 orchestrator Bash calls of P1 core-3 and P1 full-1 is
  block work (on `9fafe09`: 4).
- **Inferred, not measured:** how Haiku acts on the new denies (the refused E1 hand-back, the manifest-only tier,
  `wait_gate.py`). That needs a fresh run. The coordinator proposed one P1 core smoke run before any batch.
- **Verified, and a cost to watch:** the Deliverables check fails on all 12 stored plans (all of them put the
  outputs in a late phase). It shows in the P1 gate before P4 and in the P4 gate after it. **Inferred:** in a fresh
  run P1 writes them in the first phase from `commands/plan-create.md`, or gets its one fix round for it.
