# How results are graded

What decides each number in this repository, who or what produces it, and what it does not tell you.
The short version: pass or fail comes from scripts and tests you can read here. The headline quality
score of the exploratory rounds came from a model acting as grader. That score is an opinion, not a
measurement, and it does not say whether code is fit to ship.

## The kinds of grading used

- Scripted tests: hidden tests or checks that a script runs on the delivered code. Same input, same
  answer, and you can rerun them.
- Answer key: the expected results are computed independently from frozen inputs, and a script compares
  the candidate's output with them.
- Static analysis tools: published tools with fixed thresholds (coverage, complexity, bug findings).
- Model as grader: an AI model reads the code and gives scores. It can be blinded to which setup wrote
  the code, but its scores are still judgment, and two runs of the grader can disagree.
- Private grading: the grader exists but is not published, so you cannot check it.

## Round by round

### Live-tier tasks T01 to T06 (built, not run)

- Pass or fail: the hidden tests in each task's `hidden/` folder, run on the delivered code. T01 has 3
  tests, T02 6, T03 7, T04 6, T05 7, T06 6. The tests are committed, for example
  [the budgets tests](../../golden/tasks/T05-ledgerlite-budgets/hidden/test_hidden_budgets.py). Each task
  also has a reference solution, and `python -m cbench golden-check` shows the hidden tests fail before
  it and pass after it.
- Quality: [criteria v1](criteria.md#4-measures) makes reproduced defects the primary measure and a
  1-to-10 rubric a secondary one. Both come from a blind reviewer, which can be a model. So under v1
  the primary measure would be judgment, not a script. [Criteria v2](criteria-v2.md#6-defect-checks),
  the draft for the next run set, removes that: defects come from edge checks and probe inputs frozen
  before the runs, and from tests a fixed, blind reviewer proposes, which count only when code confirms
  them. No model or person decides a measure by judgment.

What a hidden test looks like (from T05, budgets):

```python
def test_non_positive_limit_is_an_error(cli):
    assert cli("budget", "set", "groceries", "5")[0] == 0
    assert cli("budget", "set", "groceries", "0")[0] == 2
    assert cli("budget", "set", "groceries", "-5")[0] == 2
```

It checks behavior the task statement asks for. It cannot check anything the statement does not mention,
such as a NaN amount, which is how the Opus one-shot shipped a crash and still passed every hidden test.

### Iterations 3 and 4 (exploratory)

- Delivered: the same hidden tests as T04 to T06, run by
  [the iteration 4 grading script](../evidence/2026-10-12-iteration-4/grade.py).
- Blind quality, the 8.00 against 7.33: one Opus model per task scored every anonymous solution from
  1 to 10 on design, correctness, readability and tests, and the score is the mean of the four. It had to
  reproduce each defect it reported with a command. Scores, defects and notes are committed in
  [the grader's output](../evidence/2026-10-12-iteration-4/blind_scores/), and the map from letters to
  setups is in [the blind mapping](../evidence/2026-10-12-iteration-4/blind_mapping.json).
  The grader's prompt is not committed; it is only described in the
  [iteration 3 write-up](../evidence/2026-10-10-harness-vs-oneshot.md). One grader, one run per task.
- Defect severity: the owner assigned it from the grader's text by a written rule
  ([defect records](../evidence/2026-10-12-iteration-4/defects.json)). Criteria v1 asks for a script and
  two reviewers; this round had neither.
- Tool gate: [the quality model](quality-model.md) measured new-code coverage, complexity, new bug
  findings and new type errors with published tools and SonarQube "Sonar way" thresholds. It was
  reported, not used to rank, because the task authors' own reference solutions fail it on two of three
  tasks.

### Pilot (exploratory)

- Delivered: the iteration 4 hidden tests and the tool gate, by script
  ([grading script](../evidence/2026-10-13-pilot/grade_arm.sh)). No model grader.

### Multi-cause bug B01 (private)

- Pass or fail: a script runs the real services and checks two product outcomes: the main path and a
  second entry point. The task, its grader and its transcripts belong to a third party and are not
  published. Only the scores are. You cannot check this grading.

### SWE-bench Pro sample (calibration)

- Pass or fail: the benchmark's own tests (the tests the fix must make pass, and the existing tests it
  must not break), run by Harbor in each task's container. Grading is the benchmark's, not this
  repository's. Per-task results: [round 2](../../calibration/swebench-pro/round2.md).

### Pipeline tasks P1 to P3 (exploratory)

- Reward: seven checks on the published data marts, scored against an
  [answer key](../../golden/pipeline/key/answer_key.json) computed from frozen inputs. Every check has a
  sha256 of its expected answer and a list of seeded traps, each of which must change that check's
  answer when a candidate falls for it. A build must also give identical outputs when run twice. No
  model and no reviewer is involved. This is the strongest grading in the repository.
- Limit: some checks have more than one reasonable reading of the spec, listed as open readings in the
  [trials write-up](../evidence/2026-10-15-pipeline-trials.md).

#### Grader v3

The owner's rules (postmortem front matter, Grading, 2026-10-24): the custom tasks stay the primary
benchmark, graded by accepted-benchmark practice: code only, the final state, answers not form, every rule
derivable from the task prompt. A grader that only reads the hidden reference's shape is an opinion mismatch,
not a failure. A mapping entry that names a table and columns and states its operation in plain words is a
valid answer, applied by a fixed, model-free parser; an entry the parser cannot resolve fails, with the
reason logged, identically for every arm; nobody reviews unresolved entries. Stream and idempotency rules
stay as they are.

What v3 changes, all in how an `oracle_map.yml` entry is read (prompt.md:41: "the table and column (or SQL
view) that answers it"). The answer key, the comparison with it (money to the cent, counts exact, the same
accepted readings and traps), `stream_ok`, idempotency and the reward are unchanged.

- **An operation stated in words** beside the table and columns (`how:`, `note:`, `aggregation:`, `rows:`,
  `filter:`, `group_by:`) is read by [`pipetask/ops.py`](../../golden/pipeline/pipetask/ops.py), a fixed
  grammar: filter, group, sum, count, divide, and a count of groups whose sum is below zero. Columns must be
  the mart's own. The plan runs on the mart's rows and the check reads the result, as it reads any table.
  Division is exact decimal arithmetic, as the key's, and the divisor must hold one value per group.
- **Ordering and cutting are the check's own.** `order by`, `sort`, `take ten`, `limit` are recognised and
  not applied: checks 2 and 6 rank the whole result themselves, as they always have.
- **Check 4 keeps the published grain.** The month it reads is the answer key's and the roll-up (county to
  state to source) is what the check does, so an entry's month filter and roll-up are not applied; among
  the columns the entry names, the month, county and state columns are each found by their values.
- **Unresolved fails.** A clause that names a column, another mart, a dotted name or an operation word that
  the grammar cannot read makes the entry unresolved: the check fails with `unresolved: <the clause>`. A
  clause with none of those (commentary) is skipped.
- **Two more shapes of the same answer:** a query nested one level down (`queries: {answer: ...}`: the one
  named `answer`, or the only one), and a path to a file inside a mart folder (`out/marts/<mart>/data.parquet`).
- **Golden samples:** [`golden/pipeline/fixtures/grader-v3/`](../../golden/pipeline/fixtures/grader-v3/) holds
  each stored tree's delivered map and the marts it names; `tests/test_pipeline_grader_v3.py` pins every
  entry's resolution and every check's result, and that v3 keeps every check the pinned grader passed.
- The regrade of every stored tree, with each change and why, and an independent recomputation of every
  point v3 gains: [docs/evidence/2026-10-25-grader-v3](../evidence/2026-10-25-grader-v3/README.md).

## Where a model's judgment decides a number

- The blind quality scores of iterations 3 and 4, including the headline 8.00 against 7.33.
- The defects those graders reported (each reproduced by a command, but found by the model).
- Under criteria v1, the primary measure of the live tier (reproduced defects) and its rubric. Criteria v2
  removes both: code decides every measure, and a reviewer may only propose tests that code confirms.

Everything else is scripted, an answer key, a published benchmark's tests, or private.

## What none of this measures

Passing hidden tests, or scoring well with a model grader, is not the same as code you would put into
production. No grade in this repository yet measures that directly. The plan to replace the model
grader with accepted benchmarks and tool-based checks: [grade with accepted benchmarks](../plans/accepted-benchmarks.md).
