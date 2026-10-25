# Review eval: review skills scored on stored run trees

The owner's rule (2026-10-25): review skills are built and revised with skill-creator, and every revision is
scored against the current version on existing diffs. A revision ships only if it does not regress on that set.
A new skill replaces or merges into `/pr-review-local` only where it is measurably better than both baselines:
the current `/pr-review-local` and Claude Code's built-in `code-review` skill.

## The eval set

`cases.json`: the 11 stored trees of batch `2026-10-24-shapes-r2` (P1 full-5 was lost and has no tree). Case
names are a fixed shuffle (`review-01` to `review-11`), so a reviewer's paths do not name the run.

Known answers, and how each is verified:

- 6 defect cases: the grader's `stream_ok` is false (`runs/<id>/scores.jsonl`, grader c344bea, code). The
  consumer does not get past the replay's invalid frame (F5): it reconnects without end or crashes, so
  `make stream` never reaches the end of its input. Three of them have the mechanism from the postmortem log
  (P1 core-4 and P2 core-5 loop, P2 core-4 crashes at engine/stream.py:63).
- 5 control cases: `stream_ok` is true. A must-fix claim that the consumer loops or crashes on that frame is
  a false finding.
- review-01 (P1 core-6) also carries the survivability pilot's 9 HIGH and MEDIUM findings (H1, H2, M1 to M7),
  each reproduced by the pilot's consolidation. The pilot reviewed the same tree (git tree 9305aa39).
  HIGH items must be reported as must-fix; MEDIUM items count at any severity.

## Steps

The agent steps are Agent-tool subagents of a Claude Code session. Never start `claude -p` or another agent
CLI, and never change permission modes (owner limit, 2026-10-25).

```bash
W=/var/tmp/revieweval            # outside any checkout: reviewers must not see golden/ or cases.json
python -m revieweval.prepare --out $W                    # blinded trees from runs-store (no run is re-run)
python -m revieweval.build --work $W                     # one build per tree, one at a time (port 8099 free)
python -m revieweval.compare layout --work $W --iteration <name> --cadence <cadence checkout> \
  --config new_skill=<skill>@<sha>[#variant] --config old_skill=pr-review-local@<sha> \
  --config builtin_code_review=code-review --baseline old_skill --baseline builtin_code_review --runs 3
```

`layout` writes `$W/<name>/dispatch.jsonl`: one line per subagent, with the run folder, the step, the steps it
waits for (`after`), the diff, the prompt and the output path. Naming cases after the options re-lays only
those cases: their lines are replaced and every other case's lines are kept (the configurations must match).
For each run folder:

1. `python -m revieweval.compare setup <run>` (its own clone of the prepared tree, which has `review` and `base`).
2. Dispatch each step when its `after` steps are done; steps with the same `after` go in the same turn. A line
   with `output` ending in `.md` takes the subagent's final report as that file.
3. Write `<run>/timing.json` as `{"steps": {"<step>": {"duration_ms": n, "total_tokens": n}}}` from each
   Agent-tool notification. The wall time is the longest path through the steps; the tokens are the sum.
4. Dispatch the `grade` line (skill-creator's agents/grader.md): it writes `<run>/grading.json`.
5. `python -m revieweval.compare cleanup <run>`.

Then `python -m revieweval.compare collect --work $W --iteration <name> --skill-creator <skill-creator dir>`
runs skill-creator's `aggregate_benchmark.py` (benchmark.json, benchmark.md) and writes `comparison.json`.

## The rule in comparison.json

For each configuration that is not a baseline, against each baseline: recall (defect answers found as must-fix)
and false findings (control answers broken, plus must-fix claims the grader refuted), each as the mean and
stddev over the repeats, and wall time and tokens per review. `measurably_better` holds only when the recall
gain is larger than the larger stddev, false findings are not worse beyond their stddev, and time and tokens
are at most 1.25 times the baseline's (the postmortem's speed SLO). `beats_every_baseline` is the per-part
answer. The variants of `antagonistic-review` are the parts: `#single` (one antagonistic reviewer), `#three`
(three reviewers, no consolidation) and `#full` (with consolidate-and-verify and explain).
