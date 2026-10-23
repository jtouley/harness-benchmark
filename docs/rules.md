# The rules of the learning loop

The rules the loop acquired in the week of 19 to 23 October 2026, each with the code or the test that
enforces it. A reader audits the loop from this page: each link is the place where the rule is a check,
a refusal or a test, not a sentence. A rule that is only in a pull request not merged yet says so with
the number. No rule here is new.

## Runs and what counts

1. **A Cadence run's only prompt is `/cadence <spec path>`.** The driver refuses a Cadence benchmark or
   live run without `--spec`, gives the command exactly `/cadence <the spec's absolute path>` as
   `HB_AGENT_PROMPT`, refuses a command whose `claude` call carries any other prompt text, and keeps the
   spec's path, sha256 and the prompt in `record.spec`. A run whose agent argv shows another prompt does
   not count. (Only in #73: `loop/driver.py`, `loop/schema/record.schema.json`; tests
   `test_the_command_gets_exactly_slash_cadence_and_the_spec_path_and_the_record_has_the_spec`,
   `test_a_command_that_gives_the_agent_other_prompt_text_is_refused`,
   `test_an_agent_that_ran_with_another_prompt_does_not_count` in `tests/test_loop_record.py`.)
   The saved specs are the golden inputs: [golden/cadence/README.md](../golden/cadence/README.md),
   [tests/test_golden_cadence.py](../tests/test_golden_cadence.py).
2. **Whether a clean run counts is a function of its kind.** A stub never counts; a backfilled record
   counts only with a score from the harness-benchmark grader; a driver run counts, and with a plugin
   only on a clean published tree that the run did not change (a one-shot has no plugin and counts). [loop/record.py](../loop/record.py) (`NON_COUNTING_KINDS`, `GRADER_REPO`),
   [loop/check.py](../loop/check.py) (`validate_tree`); tests
   `test_whether_a_clean_run_counts_is_a_function_of_its_kind`,
   `test_the_check_refuses_a_counting_record_of_a_kind_that_never_counts`,
   `test_the_check_refuses_a_counting_backfilled_record_without_a_grader_score` in
   [tests/test_loop_record.py](../tests/test_loop_record.py). The 55 self-graded live runs are records
   with `counts` false for that reason: [loop/backfill_live.py](../loop/backfill_live.py),
   [tests/test_loop_backfill_live.py](../tests/test_loop_backfill_live.py).
3. **Records are written once and scores are appended.** `loop.check --base` refuses a changed or
   deleted record and a rewritten score. [loop/check.py](../loop/check.py) (`append_only`); test
   `test_the_check_refuses_a_changed_or_deleted_record_and_allows_new_ones_and_new_scores` in
   [tests/test_loop_record.py](../tests/test_loop_record.py).
4. **The plugin is a clean published commit.** The driver refuses a plugin tree with any modified,
   untracked or ignored file, or a HEAD on no remote branch; a run that changes its own plugin source
   does not count. [loop/driver.py](../loop/driver.py) (`plugin_commit`, `plugin_unchanged`); tests
   `test_the_driver_refuses_a_patched_plugin_before_running_anything`,
   `test_a_run_that_changes_or_adds_plugin_source_does_not_count` in
   [tests/test_loop_record.py](../tests/test_loop_record.py).

## Isolation

5. **Two scans, and `counts` false on contact.** Before the run, the driver searches the working
   directory and HOME for any other Cadence checkout and refuses the run when it finds one
   ([loop/driver.py](../loop/driver.py), `other_checkouts`; tests
   `test_other_cadence_checkouts_under_the_roots_are_found_and_the_plugin_is_not`,
   `test_the_driver_refuses_a_run_that_can_reach_another_cadence_checkout` in
   [tests/test_loop_record.py](../tests/test_loop_record.py)). After the run, every tool-call input in the
   transcript is scanned for the benchmark and for any other Cadence checkout; a hit goes in
   `isolation.contact` and the run does not count. (The second scan is only in #73; test
   `test_a_transcript_that_touched_the_benchmark_or_another_checkout_does_not_count`.)
6. **A fresh HOME.** `--fresh-home` must be empty or new, and the record says whether the run had one.
   [loop/driver.py](../loop/driver.py); tests `test_a_fresh_home_is_empty_and_is_recorded`,
   `test_a_fresh_home_that_exists_and_is_not_empty_is_refused` in
   [tests/test_loop_record.py](../tests/test_loop_record.py).
7. **No key reaches an agent, on either auth route.** In the container, the API key goes in on standard
   input, never as a process argument, and every output file is scanned and the key redacted; when a
   file cannot be scanned, the runner says so with "do not publish", and exits 3 before `host.json` is
   written, so those outputs are never taken as clean
   ([runner/run_trial.sh](../runner/run_trial.sh); tests `test_api_key_is_never_a_process_argument`,
   `test_outputs_are_scanned_and_the_key_is_redacted_without_printing_it` in
   [tests/test_runner.py](../tests/test_runner.py)). The two routes for a host that cannot hold a key:
   `proxy` (the host's proxy adds the credentials; `--auth proxy` sends no key, refuses a proxy URL with
   a user, a password or a path, and never prints it) and `oauth-file` (the operator's one OAuth
   credential file copied into the fresh HOME and nothing else). (The container side of `proxy` is the
   draft #70: [runner/run_trial.sh](../runner/run_trial.sh), `runner/proxy_relay.py`,
   `runner/net_guard.sh`; test `test_auth_proxy_refuses_a_proxy_url_with_a_credential_and_never_prints_it`
   in [tests/test_runner.py](../tests/test_runner.py) on that branch.) (The host side of both routes is
   only in #73: `scripts/host_trial.py`, the driver's `--auth` and `isolation.auth`; tests
   `test_the_fresh_home_gets_exactly_what_the_auth_route_needs`,
   `test_the_agent_environment_carries_no_api_key_or_token` in `tests/test_host_trial.py`.)

## Caps

8. **A one-shot has a guard cap and a harness arm only a backstop.** A one-shot without `--agent-timeout`
   gets the default of 3600 s; the runner refuses `--agent-timeout 0` on a one-shot, a guard cap on a
   harness arm, and a backstop or a spend limit on a one-shot; a harness arm must have a backstop. The
   backstop is the class's measured one or the default in [runner/pipeline/caps.json](../runner/pipeline/caps.json). [runner/run_trial.sh](../runner/run_trial.sh),
   [scripts/pipeline_trial.py](../scripts/pipeline_trial.py) (`harness_backstop`); tests
   `test_only_a_one_shot_has_a_guard_cap_and_only_a_harness_a_backstop` in
   [tests/test_runner.py](../tests/test_runner.py), `test_a_one_shot_gets_the_guard_cap_and_no_backstop`
   and `test_a_harness_arm_gets_its_class_backstop_or_the_default` in
   [tests/test_pipeline_trials.py](../tests/test_pipeline_trials.py). The rule itself is criteria v2,
   section 5.3 ([docs/method/criteria-v2.md](method/criteria-v2.md)).

## The hold-out and contamination

9. **P4 is the hold-out, behind `--holdout`, and never in `golden/cadence/`.** `loop.driver` and
   `scripts/pipeline_trial.py` refuse `--task P4` without `--holdout`; its spec is no saved golden input;
   its pins stay a subset of the shared image's. [loop/driver.py](../loop/driver.py) (`HOLDOUT_TASKS`),
   [scripts/pipeline_trial.py](../scripts/pipeline_trial.py), [golden/pipeline/README.md](../golden/pipeline/README.md);
   tests `test_the_driver_refuses_p4_without_holdout`, `test_p4_is_fingerprinted_and_is_no_golden_cadence_input`
   in [tests/test_pipeline_p4.py](../tests/test_pipeline_p4.py),
   `test_the_trial_script_refuses_p4_without_holdout_before_building_anything`,
   `test_p4_pins_are_a_subset_of_the_shared_images_locks` in
   [tests/test_pipeline_p4_runner.py](../tests/test_pipeline_p4_runner.py).
10. **Fingerprints, and no reference text under the golden inputs.** `loop.fingerprints` hashes the
    reference material and the golden inputs, and writes hashes only, so Cadence's contract test can show
    it carries none of them; no golden input shares a fingerprint with the answer key, the hidden tests or
    the reference solutions. [loop/fingerprints.py](../loop/fingerprints.py);
    [tests/test_loop_fingerprints.py](../tests/test_loop_fingerprints.py),
    `test_no_reference_material_sits_under_golden_cadence` in
    [tests/test_golden_cadence.py](../tests/test_golden_cadence.py).

## Findings and the trace

11. **A finding cites runs, has an owner, and closes by script.** A row with no run id, with a run id
    that has no record, or without `owner` (`{"session", "branch"}`, both null while nobody fixes it) is
    refused; `status` is computed from later counted runs on a cadence commit that carries the fix, never
    set by hand. [loop/findings.py](../loop/findings.py); tests `test_a_row_without_run_ids_is_refused`,
    `test_a_row_without_an_owner_is_refused_and_an_unowned_one_says_so`,
    `test_a_hand_set_close_is_refused_and_update_writes_the_computed_status` in
    [tests/test_loop_findings.py](../tests/test_loop_findings.py).
12. **Evidence and finding trailers on cadence commits.** A cadence commit names the finding it fixes
    with `Finding: F-n` and the run it rests on with `Evidence: <run id>`; `loop.findings` finds the fix by
    the first trailer, and `loop.trace` lists, per run, the commits and pull requests that cite it by the
    second, from a snapshot that walks a fixed set of refs and keeps no commit text.
    [loop/findings.py](../loop/findings.py) (`fix_commits`), [loop/trace.py](../loop/trace.py),
    [citations.json](../citations.json); tests `test_the_trailer_finds_the_fix` in
    [tests/test_loop_findings.py](../tests/test_loop_findings.py) and
    [tests/test_loop_trace.py](../tests/test_loop_trace.py).

## The scoreboard and the gate

13. **The gate bars are the counted one-shots.** A cadence commit passes for a model when, on every task
    in the set, it has at least three scored runs whose mean checks passed is above the best counted
    Sonnet one-shot and at least the best counted Opus one-shot of that task; the time ratio is reported
    against the stretch goal, not gated. [loop/scoreboard.py](../loop/scoreboard.py) (`baseline`, `gate`);
    tests `test_the_baselines_are_the_15_october_one_shots`, `test_the_gate_compares_the_mean_with_sonnet_and_opus`,
    `test_the_gate_needs_n_runs_per_task` in [tests/test_loop_reports.py](../tests/test_loop_reports.py).
    Today the counted one-shots are the 15 October runs.
14. **A run that stopped early has no time ratio.** The speed ratio counts only runs that reached the
    end of the pipeline or passed a check. [loop/scoreboard.py](../loop/scoreboard.py) (`reached_end`);
    test `test_a_run_that_stopped_early_with_no_check_passed_has_no_ratio` in
    [tests/test_loop_reports.py](../tests/test_loop_reports.py).

## Postmortems and merges

15. **Every run is in a committed postmortem, and the committed files are the generators' output.**
    Every counted run and every run a finding cites is in a postmortem under `postmortems/`; each
    committed postmortem equals what the generator writes from its notes; `scoreboard.md` equals what
    the scoreboard writes; the driver writes both when it records a run. Only in #78 (`loop/check.py`,
    `postmortem_problems`; `loop/postmortem.py`, `--all`; `tests/test_loop_postmortem_complete.py`). On
    main today: `test_the_committed_postmortem_is_what_the_generator_writes` and
    `test_the_committed_scoreboard_is_what_the_generator_writes` in
    [tests/test_loop_reports.py](../tests/test_loop_reports.py).
16. **The after-merge rule.** After every merge the reviewer runs `scripts/ci_local.sh` on `origin/main`,
    and a pull request that touches the findings, the citations, the records or the generators
    regenerates the postmortems and the scoreboard in the same commit.
    [runs/README.md](../runs/README.md), "After a merge". Its enforcement is rule 15.
17. **A postmortem's hand-written line cites a run.** A ledger, root-cause, decision or action line
    without a run id that has a record is refused. [loop/postmortem.py](../loop/postmortem.py)
    (`notes_problems`); test `test_a_hand_written_line_without_a_resolvable_run_id_is_refused` in
    [tests/test_loop_reports.py](../tests/test_loop_reports.py).

## Three more, found in the code

18. **A run id is never reused.** The driver refuses a run id whose folder exists.
    [loop/driver.py](../loop/driver.py); test `test_the_driver_refuses_a_run_id_that_exists` in
    [tests/test_loop_record.py](../tests/test_loop_record.py).
19. **A grade needs a clean grader checkout.** With `--grade`, the driver refuses a grader repository
    whose `golden/pipeline/pipetask` has local changes, because no commit would name the grader that
    scored the run. [loop/driver.py](../loop/driver.py) (`grader_identity`); test
    `test_a_grade_from_the_benchmark_grader_becomes_a_score_with_the_grader_identity` in
    [tests/test_loop_record.py](../tests/test_loop_record.py).
20. **The P4 key reaches a trial only inside `grader-p4.pyz`.** The starting repository holds the
    skeleton and the P4 data only, and the grader bundle reads the key from its own archive into memory;
    nothing key-like is on disk while the candidate's build runs.
    [golden/pipeline/pipetask/bundle.py](../golden/pipeline/pipetask/bundle.py); tests
    `test_the_starting_repository_holds_the_skeleton_and_the_p4_data_only` in
    [tests/test_pipeline_p4.py](../tests/test_pipeline_p4.py),
    `test_grader_p4_pyz_grades_the_reference_from_a_clean_directory_and_never_puts_the_key_on_disk` in
    [tests/test_pipeline_p4_runner.py](../tests/test_pipeline_p4_runner.py).

## Where the rules live

| Rule | Code | Tests | State |
|---|---|---|---|
| 1 entry prompt and spec sha | `loop/driver.py` | `tests/test_loop_record.py` | #73 |
| 2 counting by kind | `loop/record.py`, `loop/check.py` | `tests/test_loop_record.py` | main |
| 3 append-only records | `loop/check.py` | `tests/test_loop_record.py` | main |
| 4 clean published plugin | `loop/driver.py` | `tests/test_loop_record.py` | main |
| 5 two isolation scans | `loop/driver.py` | `tests/test_loop_record.py` | checkout scan main; contact scan #73 |
| 6 fresh HOME | `loop/driver.py` | `tests/test_loop_record.py` | main |
| 7 no key to the agent; auth routes | `runner/run_trial.sh`, `scripts/host_trial.py` | `tests/test_runner.py`, `tests/test_host_trial.py` | container key rules main; `proxy` container side #70 (draft); host routes #73 |
| 8 cap per arm | `runner/run_trial.sh`, `scripts/pipeline_trial.py` | `tests/test_runner.py`, `tests/test_pipeline_trials.py` | main |
| 9 P4 hold-out | `loop/driver.py`, `scripts/pipeline_trial.py` | `tests/test_pipeline_p4.py`, `tests/test_pipeline_p4_runner.py` | main |
| 10 fingerprints | `loop/fingerprints.py` | `tests/test_loop_fingerprints.py`, `tests/test_golden_cadence.py` | main |
| 11 findings with owner, closed by script | `loop/findings.py` | `tests/test_loop_findings.py` | main |
| 12 trailers and the trace | `loop/findings.py`, `loop/trace.py` | `tests/test_loop_findings.py`, `tests/test_loop_trace.py` | main |
| 13 gate bars | `loop/scoreboard.py` | `tests/test_loop_reports.py` | main |
| 14 no ratio for an early stop | `loop/scoreboard.py` | `tests/test_loop_reports.py` | main |
| 15 postmortems complete and current | `loop/check.py`, `loop/postmortem.py`, `loop/driver.py` | `tests/test_loop_postmortem_complete.py` | #78 |
| 16 after-merge rule | `runs/README.md` | rule 15 | main (text), #78 (check) |
| 17 cited hand-written lines | `loop/postmortem.py` | `tests/test_loop_reports.py` | main |
| 18 run ids never reused | `loop/driver.py` | `tests/test_loop_record.py` | main |
| 19 a grade needs a clean grader | `loop/driver.py` | `tests/test_loop_record.py` | main |
| 20 the P4 key only in `grader-p4.pyz` | `golden/pipeline/pipetask/bundle.py` | `tests/test_pipeline_p4.py`, `tests/test_pipeline_p4_runner.py` | main |
