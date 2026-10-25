# Skill review R2: `skills/test-benchmark/SKILL.md` and `scripts/test_benchmark_gate.py` (dispatch item 3)

Date: 2026-10-25. Read only. I made no network calls, launched no agents and pushed nothing.
Tags: **[V]** means I checked it with my own tool call. **[I]** means I inferred it.

## Sources and heads

- **#231** is `fix/enforcement-gate` @ `4c437ca`. Source: the Oct 25 04:45 log entry, read from the local copy of the doc at `scratchpad/pm_now_plain.txt` (rev 316).
- The front matter came from the same local copy, so I made no Docs call.
- The two R2 files are byte-identical at `2100c6e`, on #228 (`9314a61`), #229 (`4d36756`), #231 (`4c437ca`) and on `feat/antagonistic-review` (same sha1) **[V]**. Neither PR touches R2. The diff below applies to every one of these heads.
- **Transcripts:** the 11 shapes-r2 transcripts come from `work/runs-store/blobs`, through each `record.json`. The core-6 sha256 is 870ecb7c…, which matches its record **[V]**.
- **Line numbers:** they are 1-based lines of each transcript.

## Q1. Did R2 catch any of the 28? It flagged one, after creating it, and fixed none.

Core-6 R2 has two scorecards: the Write at line 2119 (round 1, after the dispatch at 2044) and the Write at line 2479 (round 2, after the dispatch at 2402) **[V]**.

| R2 item | Maps to the final review (`final-review-t1.md`) | Outcome |
|---|---|---|
| spec-F01: the live-replay test is flaky and skips | none (the review says the suite has "49 tests OK incl. live-replay") | fixed `30fe1d1`; not a reviewer finding |
| spec-F02: row counts are checked for 2 of 5 tables | none | fixed `7c9cc90` |
| spec-F03: `check_rerun.py` is not run by discovery | near L2 (the rerun check covers one mart) but not the same | its fix `75b8993` **added `tests/test_rerun.py` = L6** |
| spec-F04 (round 2): `test_rerun.py` runs `make build` inside the unit suite | **L6, first bullet**, which R2 itself caused | left open; hard stop at R2 |
| spec-F05: the live-replay test checks only a prefix | none | left open |

**What R2 saw and cleared** **[V]** (the `adversarial_inputs` at line 2119):
- **H1.** The "offline" entry ran the consumer against `127.0.0.1:9`. It wrote **expected** "Returns at DURATION without an exception; no event landed" and **observed** "exit 0, no event landed". That is exactly H1's silent exit 0, recorded as correct.
  - This came from the skill's offline class, which is written for Cadence ("an offline host without `gh`", `review-rigor.md:64-66`).
  - It also came from an expected value that the model wrote itself, with no spec line behind it.
- **M6.** The malformed-input entry tried only `length` and `timestamp`, the two fields MF-1 named. Namespace, type and bot were never tried.
- **H2.** "Restart" was a clean stop. Nothing killed the process between normalize and load.

**What R2 never looked at** **[V]** (the `scope` field on both cards):
- Both cards say "dbt singular tests under transform/tests/ were not run in this block and are not scored."
- That puts the test-side defects out of R2's reach:
  - M2: `test_late_events_count` is never selected.
  - M3: the `dim_date` key tests never run.
  - M5: the check-4 oracle is not independent, because `test_county_state_source_reconcile` reads from model tables.
- The skill only says "score tests that exist" (`SKILL.md:17-18`). It does not require every test runner, and it does not require proof that a runner selects each test.

## Q2. What the floor cost across the 11 runs [V]

Method:
- An R2 dispatch is an Agent or Task call whose prompt starts with `/test-benchmark` (code mode).
- Gate outcomes are the `test-benchmark-gate-code` result lines.
- "Peer min" comes from the record's `timing.blocks["test-benchmark-pr"]`.
- "R2 span" runs from the first R2 dispatch to the last R2 scorecard or gate result, so it includes the fix rounds between scorings.

| Run | R2 dispatches | Re-scores | Cards (FAIL) | Final | Peer min | R2 span min | Min after first FAIL card | Stop |
|---|---|---|---|---|---|---|---|---|
| P1 core-4 | 2 | 1 | 2 (2) | FAIL | 6.1 | 13.9 | 11.2 | **R2: hard stop on the floor** |
| P1 core-5 | 0 | – | – | – | – | – | – | E4 |
| P1 core-6 | 2 | 1 | 2 (2) | FAIL | 5.8 | 16.4 | 14.1 | **R2: hard stop on the floor** (mean 6.33) |
| P1 full-4 | 4 | 3 | 4 (3) | PASS | 36.2 | 55.4 | 42.0 | R7 |
| P1 full-6 | 8 | 7 | 10 (9) | PASS | 43.5 | 95.0 | 90.2 | E4 |
| P2 core-4 | 1 | 0 | 1 (0) | PASS | 9.0 | 8.9 | 0 | E4 |
| P2 core-5 | 3 | 2 | 3 (2) | PASS | 7.8 | 9.1 | 6.0 | R7 |
| P2 core-6 | 2 | 1 | 2 (1) | PASS | 16.0 | 29.2 | 22.4 | R7 |
| P2 full-4 | 4 | 3 | 4 (3) | PASS | 9.1 | 28.8 | 26.8 | R7 |
| P2 full-5 | 3 | 2 | 3 (2) | PASS | 12.2 | 22.2 | 17.6 | R5 |
| P2 full-6 | 1 | 0 | 1 (1) | FAIL | 3.6 | 3.2 | 0 | R5 |
| **Total** | **30** | **20** | **32 (25)** | | **149.3** | **282** | **230** | |

**The stops.**
- Two hard stops at R2 (P1 core-4 and core-6) came from the score floor alone: their record `stop_point` names only scores **[V]**.
- P2 full-5's R5 stop names "spec-F01 to spec-F03 check scripts/test_benchmark_gate.py". These are P7 *plan-mode* must-fix rows, created by the same SKILL.md floor text ("dry 6"), with `check` set to the gate script. That script does not exist in the project repo **[V]**.

**What the FAIL cards were made of.**
- Every one of the 25 FAIL cards has at least one score below 7. None failed only because of a concrete finding **[V]**.
- 17 must-fix findings have the score itself as their evidence, for example "Mean 6.5 is below floor 7" (P1 full-6 ×9, P2 full-5 ×5, P1 core-6 ×2, P1 full-4 ×1). At least three of them carry `"check": "manual"` **[V]**.

**The floor dimensions are the reviewer's reading.**
- No run ran a mutation tool: zero `cosmic-ray` or `mutmut` calls in the 11 transcripts. Every card says "mutation not run".
- Yet `assertion_strength`, a must-fix floor dimension, is by `docs/tool-gates.md:73` meant to be "the mutation score on the changed lines" **[V]**.
- P1 full-6 had a commit before every re-score, yet its scores moved both ways. `assertion_strength` went 6,6,6,7,7,7,6,6,7,7, and `layer_correctness` went 7,7,7,7,7,7,6,6,7,7 **[V]**. The score is a model's reading, not a measurement.

**The verdict does not track the grade.**
- R2 ended FAIL on core-6, the best run at 4/7.
- It ended PASS on five runs that scored 0/7 (P1 full-4, P2 core-4, P2 core-5, P2 full-4 and P2 full-5).
- Scores are from the postmortem front matter's numbers section.

**Under #229's 2-dispatch cap [I].** Only P2 core-4 and P2 core-6 reach PASS within two scorecards. The other 8 R2 runs would end in a recorded R2 FAIL. The cap turns the floor from a time sink into a FAIL signal that does not track the grade. It does not fix the floor.

## Q3. Is a model-written score a lawful gate input under the front matter? No.

- **"Enforcement is live in the runs … decided by code."** The front matter says the deterministic gates "decide from observed outputs (exit code, the consumer's own input accounting, end of input, non-empty named outputs), never from text a model wrote" (Oct 25).
- **The gate decides on model text.** `_score_problems` (`test_benchmark_gate.py:106-137` @ `4c437ca`) fails R2 on `scores` and `verdict`, both of which the peer writes.
- **"Gates run once on a block's output … Any further work is a new dispatch, counted against the block's one fix round."** The floor's own message tells the run to "Fix the tests, then score again" (`:130`). That message produced the 20 re-scores.
- **The runs predate the rule.** They ran Oct 24 and the rule dates from Oct 25, so they did not break it at the time. Under the current rule, the floor cannot stay.
- **What does stay lawful:**
  - the computed `test_shape` lists (code);
  - the ledger rule (each must-fix has a ledger row);
  - a must-fix decided by its `check` command's observed result. `ledger_verify.py`/R5 runs that command; the gate never reads the prose.
- **The open edge case [I].** The `adversarial_inputs` form check is still model text checked for form only. It does not decide correctness, but the owner may want it named.

## Proposed change (diff against #231 `4c437ca`)

What the diff does:
1. **Removes the score floor and the verdict from the gate.** The scores must still be numbers, and they are reported.
2. **Requires each must-fix to name a check command.** It must not be empty or `manual`, so a weak test blocks only through a failing check that R5 runs.
3. **SKILL.md: R2 scores once.** A re-score counts against the one fix round.
4. **SKILL.md: every test runner is in scope.** That includes dbt, with **selection proof** quoted from `pytest --collect-only` or `dbt ls --resource-type test --select …`. A test that is not selected is a must-fix. This would have caught M2 and M3.
5. **SKILL.md: domain-neutral adversarial classes.** Missing, malformed (every field), empty, unreachable (local stub), kill at a stage boundary, fresh clone, and resume or repeat. Each `expected` must quote a spec line. "Exit 0, nothing written" does not count as expected for missing, empty or unreachable input, unless the spec says so. This would have put H1, H2, M1, M2's empty-mart row and M6 in R2's reach.
6. **Updates `error-recovery.md` and the gate tests.**

**Verified [V]:**
- The diff applies cleanly to a `git archive 4c437ca` export.
- `tests/gates/test_test_benchmark_gate.py` passes (48 tests).
- The 33 test files that mention test-benchmark, error-recovery or SCORE_FLOOR all pass.
- I did not run the full `ci_local`.

**Not in the diff:**
- `review-rigor.md:64-66` still holds the Cadence-CLI list for R1. That belongs to dispatch item 1, and the two should share one list.
- `docs/tool-gates.md:68` heading "floor 7" also needs editing.

```diff
diff --git a/references/error-recovery.md b/references/error-recovery.md
index 751d93d..3fa645b 100644
--- a/references/error-recovery.md
+++ b/references/error-recovery.md
@@ -145,7 +145,7 @@ A slash command goes to the block's peer through the Agent tool, as the lean pro
 | R1 | `pr-review-local: no peer-written review of this run's PR` | No review of the run's PR | `/pr-review-local <PR>` |
 | R1 | `pr-review-local: <file>: missing sections [...]` | The review has no `## Reuse and extension` or another section | `/pr-review-local <PR>` |
 | R1 | `pr-review-local: no git HEAD in the run's worktree` | The worktree has no commit | `git -C <worktree> log -1`, then commit the work |
-| R2 | `test-benchmark-pr: ... must-fix dimensions below 7` or `mean score ... is below 7` | The tests are weak | Fix the tests, then `/test-benchmark <PR>` |
+| R2 | `test-benchmark-pr: ... must-fix finding <id> has no check command` | A must-fix finding has no command that fails on HEAD | Add the failing command as `check`, or make the finding a nit |
 | R2 | `test-benchmark-pr: ... helpers_reimplemented` or `thin_files` | A test copies a conftest helper, or a test file is thin | Import the helper from `tests/conftest.py`, or merge the file. Then `/test-benchmark <PR>` |
 | R2 | `test-benchmark-pr: ... must-fix finding <id> has no must-fix row` | The scorecard names a finding that the ledger does not hold | `python3 "$C/findings_io.py" append --json '{"id": "<id>", ...}'` |
 | R2 | `test-benchmark-pr: test shape cannot be measured` | No base ref, or a test file does not parse | `git fetch origin`, then `python3 "$C/test_shape.py" --change` |
diff --git a/scripts/test_benchmark_gate.py b/scripts/test_benchmark_gate.py
index 51baf3a..4b2c068 100644
--- a/scripts/test_benchmark_gate.py
+++ b/scripts/test_benchmark_gate.py
@@ -64,7 +64,7 @@ def _adversarial_input_problems(path: Path) -> list[str]:
     problems = [] if complete else [
         f"no adversarial_inputs entries with {list(_ENTRY_KEYS)} (references/review-rigor.md)"
     ]
-    return problems + _score_problems(path) + _must_fix_ledger_problems(path)
+    return problems + _score_problems(path) + _must_fix_check_problems(path) + _must_fix_ledger_problems(path)
 
 
 DRY_MEASUREMENT_KEYS = ("helpers_reimplemented", "helpers_reused", "thin_files")
@@ -103,15 +103,11 @@ def _dry_mismatch(path: Path, shape: dict | str) -> list[str]:
     return notes
 
 
-SCORE_FLOOR = 7
-MUST_FIX_DIMENSIONS = ("layer", "dry", "assert")
-
-
 def _score_problems(path: Path) -> list[str]:
-    """R2 passes only on a passing scorecard: every dimension >= 7, no FAIL verdict.
+    """The scorecard has numeric scores. Their values and `verdict` are a model's reading: no gate decides on them.
 
-    Ported from ship-feature (benchmark_score_checks, min 7.0). A low score is
-    a must-fix: fix the tests, then score again.
+    The front matter: a gate decides from observed outputs, never from text a model wrote. A weak test
+    blocks R2 only as a must-fix finding whose check command fails on HEAD (ledger_verify.py runs it).
     """
     try:
         card = json.loads(path.read_text(encoding="utf-8"))
@@ -120,21 +116,19 @@ def _score_problems(path: Path) -> list[str]:
     scores = card.get("scores") if isinstance(card, dict) else None
     if not isinstance(scores, dict) or not scores:
         return ["no scores (skills/test-benchmark/SKILL.md: dimensions 1-10)"]
-    problems = []
     bad = {k: v for k, v in scores.items() if not isinstance(v, (int, float))}
-    if bad:
-        return [f"scores must be numbers: {bad}"]
-    # skills/test-benchmark/SKILL.md: below 7 is must-fix for layer, DRY and assertions.
-    must = {k: v for k, v in scores.items() if any(w in k.lower() for w in MUST_FIX_DIMENSIONS) and v < SCORE_FLOOR}
-    if must:
-        problems.append(f"must-fix dimensions below {SCORE_FLOOR}: {must}. Fix the tests, then score again")
-    mean = sum(scores.values()) / len(scores)
-    if mean < SCORE_FLOOR:
-        problems.append(f"mean score {mean:.1f} is below {SCORE_FLOOR} (ship-feature floor)")
-    verdict = card.get("verdict")
-    if isinstance(verdict, str) and verdict.strip().upper() != "PASS":
-        problems.append(f"verdict is {verdict}")
-    return problems
+    return [f"scores must be numbers: {bad}"] if bad else []
+
+
+def _must_fix_check_problems(path: Path) -> list[str]:
+    """Each must-fix names a check command. `manual` or no check is a nit (skills/test-benchmark)."""
+    findings = _card_value(path, "findings")
+    must = [f for f in findings if _is_must_fix(f)] if isinstance(findings, list) else []
+    return [
+        f"must-fix finding {f.get('id')!r} has no check command; write the command that fails on HEAD, or make it a nit"
+        for f in must
+        if str(f.get("check") or "").strip().lower() in ("", "manual", "n/a")
+    ]
 
 
 _MUST_FIX_SEVERITIES = {"must-fix", "high", "critical"}
diff --git a/skills/test-benchmark/SKILL.md b/skills/test-benchmark/SKILL.md
index f57a69a..a8b7f27 100644
--- a/skills/test-benchmark/SKILL.md
+++ b/skills/test-benchmark/SKILL.md
@@ -17,6 +17,22 @@ Load `$CADENCE_HOME/references/peer-contract.md` (code mode also loads
 - `/test-benchmark` or `--code` — score tests that exist.
 - `/test-benchmark <PR-number>` — R2 on a pull request: score the tests of its change.
 
+R2 runs once on the reviewed HEAD and writes one scorecard. A second scorecard
+is a new dispatch, and it counts against R2's one fix round.
+
+## Scope: every runner, and proof that the runner selects each test
+
+Score each test that the change adds or changes, and each test that the plan or
+DECISIONS names, in every test runner of the repo: `pytest` or `unittest`, dbt
+singular and generic tests, and any other runner the Makefile or the docs name.
+Do not leave a runner out of scope.
+
+For each such test, show that the command the repo uses for its gate selects
+it. Quote the captured output of `pytest --collect-only -q`, or of
+`dbt ls --resource-type test --select <the selection of the build target>`, under
+`selection` in the scorecard. A test that the gate command does not select is
+a must-fix finding. Its `check` is the selection command.
+
 ## Deliverable
 
 `.context/benchmarks/{task_id}_plan.json` (plan mode) or
@@ -27,18 +43,37 @@ only these paths. Top-level keys:
 {"RUN_BY_SKILL": "test-benchmark", "task_id": "<task_id>", "scores": {}, "findings": []}
 ```
 
-Code mode adds `adversarial_inputs`: one entry per input class in
-`review-rigor.md` (missing, corrupt, other ticket, resume, adjacent id,
-offline), each `{"input", "expected", "observed"}`, run for real. An input
-class that doesn't apply gets `"observed": "n/a: <reason>"`. The R2 gate fails
-without them.
+Code mode adds `adversarial_inputs`, each `{"input", "spec_rule", "expected",
+"observed"}`, run for real against each entry point of the change, in a
+throwaway clone. Use these input classes:
+
+- **missing**: an input file, table or directory that the entry point reads is absent.
+- **malformed**: a record with a wrong type in each field that the code reads.
+  Cover every field, not only the fields that an earlier finding named.
+- **empty**: an input with zero records. Read what each published output then holds.
+- **unreachable source**: a local stub that refuses the connection or answers non-200.
+- **kill at a stage boundary**: stop the process between two writes (for
+  example after normalize and before load), then restart it. Compare the output
+  with an uninterrupted run.
+- **fresh clone**: run each entry point in a new clone, with no build output.
+- **resume or repeat**: a restart, or the same input sent twice.
+
+Do not contact an external host. `spec_rule` quotes the spec line that sets
+`expected`. Exit 0 with nothing written is not an expected result for a missing,
+empty or unreachable input unless the spec line says so. An input class that does
+not apply gets `"observed": "n/a: <reason>"`. The R2 gate fails without the entries.
 
 Scorecard dimensions (1–10): coverage of behavior, assertion strength, DRY /
 no clone setups, layer correctness, failure paths, mutation resilience.
 
-A score below 7 on layer, DRY, or assertions is a must-fix finding. So is a
-mean score below 7. Set `verdict` to `FAIL` in those cases. The R2 gate fails
-on a `FAIL` verdict or on a score below that floor.
+The scores are your reading. They go into the report. No gate reads them, and a
+low score is not a finding. Leave out a dimension that you did not measure: with
+no mutants run, do not write `mutation_resilience`.
+
+A must-fix finding names one test defect. Its `check` is a command that fails on
+HEAD, and you quote that failing output in `evidence`. The fix makes the check pass.
+A finding whose evidence is a score ("mean 6.5 is below 7"), or whose check is
+`manual`, is not a must-fix finding. Write it as a nit.
 
 ## DRY measurement
 
diff --git a/tests/gates/test_test_benchmark_gate.py b/tests/gates/test_test_benchmark_gate.py
index ffaa5be..d3f3b8a 100644
--- a/tests/gates/test_test_benchmark_gate.py
+++ b/tests/gates/test_test_benchmark_gate.py
@@ -200,20 +200,24 @@ def test_code_mode_with_incomplete_entry_fails(tmp_path, capsys):
     pytest.param("plan", {}, 0, id="plan_mode_does_not_need_adversarial_inputs"),
     pytest.param("code", {"adversarial_inputs": [{"input": "missing ledger", "expected": 0, "observed": 0}],
                           "scores": PASSING}, 0, id="code_mode_accepts_numeric_exit_codes"),
-    # The deliverable carries the scores; a FAIL scorecard must not clear R2 (dcdd730c, 9a956068).
-    pytest.param("code", {"adversarial_inputs": [ENTRY], "scores": {**PASSING, "dry": 2}}, 1,
-                 id="code_mode_fails_when_a_score_is_below_seven"),
+    # Scores are a model's reading (front matter: never from text a model wrote). A weak test blocks R2
+    # as a must-fix finding with a failing check (dcdd730c, 9a956068 stay covered by the ledger rows).
+    pytest.param("code", {"adversarial_inputs": [ENTRY], "scores": {**PASSING, "dry": 2}}, 0,
+                 id="code_mode_does_not_decide_on_a_low_score"),
+    pytest.param("code", {"adversarial_inputs": [ENTRY], "scores": PASSING,
+                          "findings": [{"id": "cd-1-F1", "must_fix": True, "check": "manual"}]}, 1,
+                 id="code_mode_fails_on_a_must_fix_with_no_check_command"),
     pytest.param("code", {"adversarial_inputs": [ENTRY]}, 1, id="code_mode_fails_without_scores"),
-    pytest.param("code", {"adversarial_inputs": [ENTRY], "scores": PASSING, "verdict": "FAIL"}, 1,
-                 id="code_mode_fails_on_a_fail_verdict"),
+    pytest.param("code", {"adversarial_inputs": [ENTRY], "scores": PASSING, "verdict": "FAIL"}, 0,
+                 id="code_mode_does_not_decide_on_the_verdict_text"),
     # skills/test-benchmark: below 7 is must-fix for layer, DRY and assertions; the rest count in the mean.
     pytest.param("code", {"adversarial_inputs": [ENTRY],
                           "scores": {**PASSING, "coverage": 6, "failure_paths": 6, "mutation": 9}}, 0,
                  id="code_mode_follows_the_skill_contract_for_non_blocking_dimensions"),
     pytest.param("code", {"adversarial_inputs": [ENTRY],
                           "scores": {"coverage": 5, "assertions": 7, "dry": 7, "layer": 7, "failure_paths": 5,
-                                     "mutation": 5}}, 1,
-                 id="code_mode_fails_when_the_mean_is_below_seven"),
+                                     "mutation": 5}}, 0,
+                 id="code_mode_does_not_decide_on_the_mean"),
     # #30: a must-fix that lives only in the scorecard has no owner in the ledger.
     pytest.param("code", {"adversarial_inputs": [ENTRY], "scores": PASSING,
                           "findings": [{"id": "cd-1-F1", "must_fix": True}]}, 1,
@@ -233,7 +237,7 @@ def test_code_mode_must_fix_with_an_open_ledger_row_passes(tmp_path):
     _session_and_lean_record(tmp_path, mode="code")
     write_ledger(tmp_path / "findings.jsonl", ledger_row("cd-1-F1", **BENCH))
     _bench(tmp_path, "cd-1_code.json", adversarial_inputs=[ENTRY], scores=PASSING,
-           findings=[{"id": "cd-1-F1", "must_fix": True}, {"id": "cd-1-F2", "must_fix": False}])
+           findings=[{"id": "cd-1-F1", "must_fix": True, "check": BENCH["check"]}, {"id": "cd-1-F2", "must_fix": False}])
     assert run(tmp_path, mode="code", check=True) == 0
 
 
@@ -257,7 +261,7 @@ def test_code_mode_must_fix_closed_in_the_ledger_still_passes(tmp_path, status):
         row["fixed_in"] = "0" * 40
     write_ledger(tmp_path / "findings.jsonl", row)
     _bench(tmp_path, "cd-1_code.json", adversarial_inputs=[ENTRY], scores=PASSING,
-           findings=[{"id": "cd-1-F1", "severity": "must-fix"}])
+           findings=[{"id": "cd-1-F1", "severity": "must-fix", "check": BENCH["check"]}])
     assert run(tmp_path, mode="code", check=True) == 0
 
 
```
