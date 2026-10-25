37 regression tests fail on 9fafe09 and pass on the branch; 12 guards pass on both.

| Test | 9fafe09 | 9fafe09 + diagnosis diff | branch |
|---|---|---|---|
| `test_the_toy_plan_passes_p1` (test_shapes_r3_stops.py) *(guard)* | PASSED | PASSED | PASSED |
| `test_p1_gate_costs_each_timed_command_once[core-1]` (test_shapes_r3_stops.py)  | FAILED | FAILED | PASSED |
| `test_p1_gate_costs_each_timed_command_once[full-1]` (test_shapes_r3_stops.py)  | FAILED | PASSED | PASSED |
| `test_core_1_a_bare_value_is_not_a_command` (test_shapes_r3_stops.py)  | FAILED | PASSED | PASSED |
| `test_core_3_a_dry_run_and_a_chained_gate_use_the_row_of_their_timed_part` (test_shapes_r3_stops.py)  | FAILED | PASSED | PASSED |
| `test_an_uncosted_timed_part_of_a_chain_still_fails` (test_shapes_r3_stops.py)  | FAILED | PASSED | PASSED |
| `test_a_long_row_without_a_waiver_still_fails` (test_shapes_r3_stops.py) *(guard)* | PASSED | PASSED | PASSED |
| `test_after_p4_the_p1_gate_leaves_the_text_to_p4[core-1]` (test_shapes_r3_stops.py)  | FAILED | PASSED | PASSED |
| `test_after_p4_the_p1_gate_leaves_the_text_to_p4[full-2]` (test_shapes_r3_stops.py)  | FAILED | FAILED | PASSED |
| `test_after_p4_the_p1_gate_leaves_the_text_to_p4[full-3-core-3]` (test_shapes_r3_stops.py)  | FAILED | FAILED | PASSED |
| `test_before_p4_the_p1_gate_runs_the_text_checks` (test_shapes_r3_stops.py) *(guard)* | PASSED | PASSED | PASSED |
| `test_p4_gate_reads_the_text_checks_after_p4` (test_shapes_r3_stops.py)  | FAILED | PASSED | PASSED |
| `test_p1_fails_while_the_first_phase_does_not_write_the_specs_outputs` (test_shapes_r3_stops.py)  | FAILED | FAILED | PASSED |
| `test_the_specs_outputs_are_its_outputs_list_only` (test_shapes_r3_stops.py)  | FAILED | FAILED | PASSED |
| `test_the_first_phase_is_the_lowest_number` (test_shapes_r3_stops.py)  | FAILED | FAILED | PASSED |
| `test_full_3_a_read_only_poll_is_not_block_work` (test_shapes_r3_stops.py)  | FAILED | PASSED | PASSED |
| `test_full_2_a_gate_check_through_a_variable_is_not_block_work` (test_shapes_r3_stops.py)  | FAILED | FAILED | PASSED |
| `test_full_3_the_work_deny_does_not_read_as_the_max_tokens_hard_stop` (test_shapes_r3_stops.py)  | FAILED | PASSED | PASSED |
| `test_full_2_block_budgets_cover_the_slowest_observed_call` (test_shapes_r3_stops.py)  | FAILED | PASSED | PASSED |
| `test_core_2_a_stopped_return_with_phases_open_is_refused` (test_shapes_r3_e1.py)  | FAILED | FAILED | PASSED |
| `test_core_2_an_artifact_return_with_phases_open_is_refused_and_the_document_does_not_lock_e1` (test_shapes_r3_e1.py)  | FAILED | FAILED | PASSED |
| `test_the_third_refused_return_is_a_recorded_supervisor_stop` (test_shapes_r3_e1.py)  | FAILED | FAILED | PASSED |
| `test_e1_hands_back_when_its_phases_are_done` (test_shapes_r3_e1.py) *(guard)* | PASSED | PASSED | PASSED |
| `test_e1_hands_back_when_its_block_is_stopped` (test_shapes_r3_e1.py) *(guard)* | PASSED | PASSED | PASSED |
| `test_core_2_a_block_hands_back_after_its_document` (test_shapes_r3_e1.py)  | FAILED | FAILED | PASSED |
| `test_a_stopped_subagent_and_a_peer_of_a_closed_run_hand_back` (test_shapes_r3_e1.py)  | FAILED | FAILED | PASSED |
| `test_core_2_the_block_waits_for_its_gate_and_the_orchestrator_does_not` (test_shapes_r3_e1.py)  | FAILED | FAILED | PASSED |
| `test_the_wait_ends_when_the_log_says_the_run_ended` (test_shapes_r3_e1.py)  | FAILED | FAILED | PASSED |
| `test_the_wait_returns_at_its_bound_and_names_the_time` (test_shapes_r3_e1.py)  | FAILED | FAILED | PASSED |
| `test_the_wait_is_over_past_the_runs_own_time_and_then_repeats_itself` (test_shapes_r3_e1.py)  | FAILED | FAILED | PASSED |
| `test_an_over_wait_twice_is_a_repeat_that_the_supervisor_stops` (test_shapes_r3_e1.py) *(guard)* | PASSED | PASSED | PASSED |
| `test_a_wait_that_sees_the_run_go_on_is_progress` (test_shapes_r3_e1.py) *(guard)* | PASSED | PASSED | PASSED |
| `test_full_1_the_next_dispatch_above_max_tokens_is_not_a_stop` (test_shapes_r3_late_stops.py)  | FAILED | FAILED | PASSED |
| `test_full_1_a_free_form_agent_call_above_max_tokens_is_denied_without_a_hard_stop` (test_shapes_r3_late_stops.py)  | FAILED | FAILED | PASSED |
| `test_full_1_above_max_tokens_the_orchestrator_does_not_read[read-the-plan]` (test_shapes_r3_late_stops.py)  | FAILED | FAILED | PASSED |
| `test_full_1_above_max_tokens_the_orchestrator_does_not_read[read-cadence-source]` (test_shapes_r3_late_stops.py)  | FAILED | FAILED | PASSED |
| `test_full_1_above_max_tokens_the_orchestrator_does_not_read[grep-cadence-source]` (test_shapes_r3_late_stops.py)  | FAILED | FAILED | PASSED |
| `test_full_1_above_max_tokens_the_manifest_runs[headless-next]` (test_shapes_r3_late_stops.py) *(guard)* | PASSED | PASSED | PASSED |
| `test_full_1_above_max_tokens_the_manifest_runs[git]` (test_shapes_r3_late_stops.py) *(guard)* | PASSED | PASSED | PASSED |
| `test_full_1_above_max_tokens_the_manifest_runs[run-note]` (test_shapes_r3_late_stops.py) *(guard)* | PASSED | PASSED | PASSED |
| `test_full_1_above_max_tokens_the_manifest_runs[gate-output]` (test_shapes_r3_late_stops.py) *(guard)* | PASSED | PASSED | PASSED |
| `test_full_1_a_read_only_command_is_not_block_work[empty-argument]` (test_shapes_r3_late_stops.py)  | FAILED | FAILED | PASSED |
| `test_full_1_a_read_only_command_is_not_block_work[escaped-parenthesis]` (test_shapes_r3_late_stops.py)  | FAILED | FAILED | PASSED |
| `test_core_1_the_fix_round_packet_names_the_ledger_and_the_open_must_fix_ids` (test_shapes_r3_late_stops.py)  | FAILED | FAILED | PASSED |
| `test_core_1_before_the_review_e1_gets_the_plan_only` (test_shapes_r3_late_stops.py) *(guard)* | PASSED | PASSED | PASSED |
| `test_core_1_many_ids_are_named_by_the_ledger` (test_shapes_r3_late_stops.py)  | FAILED | FAILED | PASSED |
| `test_core_1_the_orchestrators_bare_fix_round_call_is_rewritten_to_the_pointer` (test_shapes_r3_late_stops.py)  | FAILED | FAILED | PASSED |
| `test_core_3_reading_a_report_with_python_flags_is_not_block_work` (test_shapes_r3_late_stops.py)  | FAILED | FAILED | PASSED |
| `test_core_3_no_context_deny_is_a_stop_in_the_skill` (test_shapes_r3_late_stops.py)  | FAILED | FAILED | PASSED |
