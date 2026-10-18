# Smoke check: SlopCodeBench and FeatureBench on Harbor (18 October 2026)

Status: no model ran. Harbor 0.24.0 ran each benchmark's reference solution (the `oracle` agent)
through the benchmark's own grader, to check the grading works end to end before money is spent. Why
these benchmarks: [grade with accepted benchmarks](../plans/accepted-benchmarks.md).

Data, committed here:

- [grader output per checkpoint](2026-10-18-smoke-check/grader/) (`reward_details.json` from each
  SlopCodeBench checkpoint of task `cfgpipe`);
- [analyzer report per checkpoint](2026-10-18-smoke-check/scb-check/) (`scb-check` 0.1.3 `--report`,
  rerun on the saved code with the grader's PATH);
- [ast-grep matches at checkpoint 6](2026-10-18-smoke-check/scb-check/ast-grep-rules-checkpoint_6.txt.gz)
  and [the script that counts them](2026-10-18-smoke-check/count_rule_lines.py).

The reference solution's code itself belongs to SlopCodeBench and is not copied here; it downloads with
`harbor download gabeorlanski/slopcodebench`.

## Results

- SlopCodeBench, task `cfgpipe` (6 checkpoints): the reference passed every core test at every
  checkpoint, and regression tests from earlier checkpoints passed at 99.1% to 100%. Even the reference
  fails a few "strict" tests from checkpoint 3 on (strict pass rate 0.991 to 0.995; 1.0 at checkpoints 1 and 2), so the core pass rate is the one to gate
  on. Erosion rose from 0.555 to 0.782, and verbosity from 0.358 to a peak of 0.586 at checkpoint 4 and 0.556 at
  checkpoint 6, for
  the reference itself. Rerunning the same pinned analyzer on the saved code at each checkpoint gave the
  same values to every digit (both are committed), so the analyzer is deterministic; what the values
  mean is in the section below. An earlier run lost two checkpoints to a full disk and was discarded.
- FeatureBench lite, task `pydantic ... test_deprecated_fields`: not run. Its prebuilt image used about
  25 GB, more than the test machine had free. FeatureBench needs a machine with large disk; its images
  are per repository, so the 30 lite tasks share 13 images.
- A model trial (the `claude-code` agent with a $1 cap) has not run: the test machine had no API key.

The run in a sandbox needed one change outside the benchmark: the test machine's HTTPS proxy
certificate had to be trusted inside the task image. That change was made to a local copy only and is
not part of any benchmark.

## What erosion and verbosity measure

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
