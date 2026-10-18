# Plan: grade with accepted benchmarks, not a model

Status: proposed, 18 October 2026. Only the no-model smoke checks below have run.

The goal is to judge harnesses with no model as grader and no reviewer in the loop: only published
benchmarks whose grading is code, and published tools with fixed thresholds. How results are graded
today, and where a model's judgment decides a number: [how results are graded](../method/grading.md).

## Why passing tests is not enough

- METR (10 March 2026) had 4 maintainers of scikit-learn, Sphinx and pytest review 296 agent pull
  requests that pass SWE-bench Verified. Roughly half would not be merged. After adjusting for the
  maintainers' own noise (they merge about 68% of the original human fixes), the automated grader is
  about 24.2 points higher than the maintainers' decision
  ([METR note](https://metr.org/notes/2026-03-10-many-swe-bench-passing-prs-would-not-be-merged-into-main/);
  checked against the source).
- Adding stronger tests rejects a share of patches that passed: 15.7% on SWE-bench Verified in UTBoost
  ([arXiv 2506.09289](https://arxiv.org/abs/2506.09289)) and 19.7% in SWE-ABS
  ([arXiv 2603.00520](https://arxiv.org/abs/2603.00520)). These figures are as reported by the papers;
  not re-checked here.
- In this repository, the Opus one-shot passed every budgets hidden test and still crashed on a NaN
  amount ([defect records](../evidence/2026-10-12-iteration-4/defects.json)).

No automated measure has been shown to match a maintainer's merge decision. So the plan uses several
measures computed by code, reports each separately, and never blends them into one score.

## Layer 1: correctness on accepted benchmarks

Run through Harbor, which this repository already uses. Each benchmark is graded by its own tests.

| Benchmark | What it is | In Harbor's registry | Why it fits |
|---|---|---|---|
| SWE-bench Pro (Scale AI) | 731 public bug-fix tasks, held-out sets for contamination | Yes (`swebenchpro` 1.0) | Already sampled here; choose the tasks where the Opus one-shot is unreliable, since the random 20 were nearly saturated |
| FeatureBench | 200 feature-implementation tasks in 24 Python projects (30 in the lite split); fail-to-pass and pass-to-pass tests | Yes (`featurebench` 1.0, `featurebench-lite` 1.0) | The same kind of work as tasks T04 to T06, at real-project scale. 44 tasks need a GPU and are left out |
| Terminal-Bench 2.0 | 89 tasks graded on the container's final state | Yes (`terminal-bench` 2.0) | Long, multi-step work outside a single code change |
| SWE-rebench (Nebius) | Fresh tasks; each model is scored only on tasks created after its release | Not in the registry file; a hub listing exists, to be confirmed before use | The answer to contamination |

Report pass rates over repeated trials (pass^k, k at least 3) with confidence intervals, per setup.
SWE-bench Verified is left out: it is widely reported as contaminated, and its tests are the ones the
studies above found weak.

## Layer 2: does the code hold up under change

SlopCodeBench ([arXiv 2603.24755](https://arxiv.org/abs/2603.24755), 36 problems, 196 checkpoints):
agents extend their own code as the specification changes, and the benchmark measures how the code
degrades (structural erosion and verbosity). The best agent passes 14.8% of checkpoints, so it is far
from saturated. This is the closest published test of what a harness claims to buy: plans and reviews
should keep code from eroding. Its grading is confirmed to use no model (see the smoke check below):
each checkpoint runs held-out pytest tests, the earlier checkpoints' tests run again as regression
tests, and erosion and verbosity come from a pinned static analyzer (`scb-check` 0.1.3) installed in
the task image. It downloads from the Harbor hub as `gabeorlanski/slopcodebench` (36 tasks).

### What erosion and verbosity measure, and how far to trust them

From the analyzer's source (`scb-check` 0.1.3) and the paper:

- Erosion: each function's complexity mass is its cyclomatic complexity times the square root of its
  lines of code. Erosion is the share of the total mass held by functions with cyclomatic complexity
  above 10. It is a share, so it can fall when simple code is added, and it does not grow with size alone.
- Verbosity: the share of lines flagged by any of three detectors: ast-grep pattern rules, structural
  clones (3 or more lines), and functions that only wrap another call.

Checked on the `cfgpipe` reference solution (6 checkpoints, 148 to 928 lines in one file):

- The reference scores worse than the paper's average agent. At checkpoint 6 it has verbosity 0.556
  and erosion 0.782. The paper reports agents at 0.44 and 0.68 on average, and 473 human Python
  repositories at 0.19 and 0.34. The absolute values are not a quality bar.
- The Harbor version is not the paper's version. The paper describes 137 ast-grep rules;
  `scb-check` 0.1.3 ships 197. Scores from Harbor cannot be compared with the paper's human baseline.
- Verbosity mostly counts validation the spec asks for. 73% of the lines the ast-grep rules flag at
  checkpoint 6 (424 of 581, before the analyzer's own thresholds) come from the "defensive" rules, and
  one rule, `defensive-fstring-raise-heavy`, flags 359 lines. Those rules flag a whole function once
  it has three `raise` statements with f-string messages, or several `isinstance` guards, on the
  reasoning that validation belongs at the program's boundary. But the spec requires it: "The error
  must identify the parameter, the source, and the parse-failure reason." In a command-line program
  that reads untrusted files, that code is the boundary.
- Erosion does not rise steadily: 0.555, 0.668, 0.528, 0.794, 0.766, 0.782. It jumps when a
  checkpoint adds a large feature (checkpoint 4 doubled the code).
- The analyzer fails quietly. It runs `sg` from the PATH; on Debian `/usr/bin/sg` is an unrelated
  system command, and with that one first the analyzer logs a warning and counts zero pattern lines.
  The benchmark's grading script sets the PATH correctly; any other use must too.
- Prior evidence on the harness question: the paper tested a "plan-first" prompt. It lowered the
  starting erosion and verbosity, but the code degraded at the same rate, solve rates fell and cost per
  checkpoint rose about 12%.

How to use it here, then:

- Compare setups only against each other, on the same task and checkpoint, never against a fixed
  threshold or the paper's numbers. Report the change from checkpoint to checkpoint, since that is
  what a harness claims to slow.
- Use erosion as the main measure of code holding up under change. Report verbosity twice: with all
  rules, and without the defensive rules, so that a setup is not rewarded for dropping error handling
  the spec asks for.
- Read the checkpoint pass rate next to both. Lower verbosity bought by failing tests is not better code.

## Layer 3: a tool gate on every delivered change

Computed on the diff, with pinned tool versions, and reported next to the pass rate as a "gated pass"
(tests pass and the change is clean), never folded into it. Most of it is already built in the
[quality model](../method/quality-model.md).

- No new security findings of medium severity or higher: Semgrep Community Edition with a pinned rule set.
- No new bug-class findings: ruff and pylint error rules (already measured).
- No function the change takes over cognitive complexity 15 (already measured).
- Duplicated lines on new code at most 3%: jscpd (already measured; the SonarQube "Sonar way" condition).
- New-code coverage at least 80% (already measured; the Sonar way condition).
- Test strength: the mutation score of the change's own tests on the changed lines, with mutmut.
  Criteria v1 already lists it (M4); it is not built.

Not used: ISO/IEC 5055 has no open-source implementation that claims conformance; CodeScene and CAST are
commercial; the Sonar way condition on reviewing security hotspots needs a person.

## Layer 4: what the process did, commit by commit

For the same feature, a one-shot and a harness can ship code of the same shape. What differs is the
path: a one-shot hands a reviewer one change with all of the complexity at once; a harness spends extra
cost and time to build the feature in steps, review it, and clean it up. Layers 1 to 3 judge what ships.
This layer judges the path, and puts the harness's extra cost next to what it bought. It is reported
separately and never blended into the others.

[`scripts/commit_replay.py`](../../scripts/commit_replay.py) replays the commits between two points
(for SlopCodeBench, between checkpoints) and measures each one by code:

- change size: lines added and deleted;
- complexity added and removed: the change in cyclomatic complexity per function (pinned radon), and
  the functions the commit takes over 10;
- green: whether the tests pass at that commit (the earlier checkpoints' held-out tests, and the
  run's own);
- time between commits.

Per checkpoint and setup it reports the largest and median commit, the share of green commits, the
clean-up commits (more complexity removed than added), the total churn, the elapsed time, and the
final state. Next to it go the run's tokens and dollars for that checkpoint.

Reading it:

- A setup's largest commit is the most a reviewer had to take in at once. For a one-shot it is the
  whole change.
- Small commits count only when they are green. A broken commit is noise, not a reviewable step.
- Total churn is the cost of drafting and cleaning up. A harness can pass more lines and complexity
  through review than a one-shot and still end at the same code; the checked example in the test does
  exactly that (largest commit 29 lines and +11 complexity, against the one-shot's whole change of 21
  lines and +9, and a clean-up commit that removed 6). So this layer does not assume a harness wins:
  it shows what its extra cost bought, which can be smaller reviewable steps, more review, or nothing.
- A commit whose code does not parse is reported as unmeasured and named, not scored.
- A run with no commits, or with uncommitted work, is reported as not measurable here. Its layers
  1 to 3 still count.

To run it on SlopCodeBench, each checkpoint's saved code must keep `.git`: the task configuration
excludes it today, one line per task. Nothing in the benchmark's grading changes.

## Smoke check, 18 October 2026 (no model, no cost)

Harbor 0.24.0 ran each benchmark's reference solution (the `oracle` agent) through the benchmark's own
grader, to show the grading runs end to end before any money is spent.

- SlopCodeBench, task `cfgpipe` (6 checkpoints): the reference passed every core test at every
  checkpoint, and regression tests from earlier checkpoints passed at 99.1% to 100%. Even the reference
  fails a few "strict" tests (strict pass rate 0.991 to 0.995), so the core pass rate is the one to gate
  on. Erosion rose from 0.555 to 0.782 and verbosity from 0.358 to 0.556 across the checkpoints, for
  the reference itself; two runs gave identical values to three decimals, so the analyzer is
  deterministic. Running the same pinned analyzer separately on the saved code at each checkpoint gave
  the same values; what those values mean is in the layer 2 section above. A first run lost two
  checkpoints to a full disk and was discarded.
- FeatureBench lite, task `pydantic ... test_deprecated_fields`: not run. Its prebuilt image used about
  25 GB, more than the test machine had free. FeatureBench needs a machine with large disk; its images
  are per repository, so the 30 lite tasks share 13 images.
- A model trial (the `claude-code` agent with a $1 cap) has not run: the test machine had no API key.

The run in a sandbox needed one change outside the benchmark: the test machine's HTTPS proxy
certificate had to be trusted inside the task image. That change was made to a local copy only and is
not part of any benchmark.

## What changes in the criteria

[Criteria v2](../method/criteria-v2.md) is still a draft, so these can go in before any run set:

- Drop the model rubric (M7) and model-found defects (M2) as measures.
- Make layer 1 pass rates the primary outcome, the layer 3 gated pass rate the primary quality measure,
  and layer 2 the measure of quality under change.
- Report layer 4 (the process, commit by commit, with its cost) next to them, never folded into a
  score. It is where a harness's extra cost and time is accounted for.
- Keep the repository's own tasks (T01 to T06 and the pipeline family) as small, fully published
  checks, graded by their hidden tests and answer key as now.

## What it would cost

The 20-task SWE-bench Pro sample cost about $0.29 per task with Opus 5.5, $0.13 with Sonnet 5.5 and
$0.03 with Haiku 5.5 as one-shots ([results per task](../../calibration/swebench-pro/round2.md)).
Harness runs take many times the tokens of a one-shot, so budget each setup separately. No other cost
figure here is measured yet.
