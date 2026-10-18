# Calibration and harness arms

Task selection is calibrated against the bar ([next steps](../docs/plans/next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13)).
This folder holds the calibration runs' scripts and summaries, and the minimal harnesses used as arms.

## Layout

| Path | What | Tracked |
|---|---|---|
| `swebench-pro/` | SWE-bench Pro (Harbor `scale-ai/swe-bench-pro`) calibration: sample lists, the round script, the results collector, `results.json` | yes |
| `swebench-pro/jobs/`, `swebench-pro/runs/`, `swebench-pro/tasks/`, `swebench-pro/sample20/`, `swebench-pro/hard3/` | Harbor job outputs, downloaded task definitions, and the sample directories `make_samples.sh` builds from the lists | no (machine-local, large) |
| `../harnesses/reviewloop/` | Review loop: the session model works, an independent `reviewer` subagent (Opus) checks the running result, the session model fixes until it approves (max 3 reviews) | yes |
| `../harnesses/reviewloop-sonnet-reviewer/` | The same, with the reviewer on Sonnet | yes |
| `../harnesses/verifyloop/` | Verification harness: a `contract-writer` subagent writes an executable `CONTRACT.md` before any code; a Stop hook runs it and blocks the session from finishing while a check fails | yes |
| `../private/` | Private tasks (B01, a brownfield bug from a third-party interview repository): prompt, grader, runner, run copies | **no**: this repository is public. Only scores are published, in [next steps](../docs/plans/next-steps.md) |

Each harness is a Claude Code plugin, loaded for one session with `claude --plugin-dir <harness>`. Its
instructions are generic: none names a task, its data or its traps ([prompt hygiene](../docs/plans/tasks/pipeline-family.md#prompt-hygiene)).

## SWE-bench Pro, so far (one-shot Claude Code, Harbor 0.24.0, Claude Code in the task container)

- Round 1 (Opus 5.5): 20 sampled Python tasks, one try each: 17 passed, 2 failed, 1 did not start (setup timeout).
- Repeats on the Opus misses:
  (each count includes the round 1 try, or its retry when the round 1 try never started)
  - `ansible-d2f80991`: 2 of 5 passed (a **beyond** candidate: the bar is unreliable);
  - `openlibrary-30bc73a1`: 2 of 5 passed (a **beyond** candidate);
  - `ansible-d9f18662`: 5 of 5 passed (the round 1 try died in setup; its retry passed).
- Round 2: one Sonnet 5.5 and one Haiku 5.5 try on all 20, to look for **lift** candidates (the bar passes,
  a cheap one-shot does not). Trials that died in container setup (the model never ran) were rerun once:
  Haiku 10, Sonnet 4, Opus 1. Result, with the Opus round 1 try ([table per task](swebench-pro/round2.md)):

  | Model (one try per task) | Passed | Cost (list prices) | Per task |
  |---|---|---|---|
  | Opus 5.5 | 18/20 | $5.79 | $0.290 |
  | Sonnet 5.5 | 18/20 | $2.57 | $0.129 |
  | Haiku 5.5 | 17/20 | $0.54 (lower bound) | $0.027 |

  On this sample, a one-shot Haiku 5.5 is within one task of Opus 5.5 at about one tenth of the cost. Only
  one task (`qutebrowser-9ed748ef`) passed on Opus and failed on both cheaper models, once each; that is
  not enough to call it a lift task. So this sample has no clear lift candidates. What stays open is the
  two beyond candidates and reliability over repeats (pass^k), which one try per model does not measure.
- Limits: 20 tasks, one try per model, setup failures rerun. Two Opus tries hit the agent timeout; one of
  them still passed the verifier and counts as a pass, the other counts as a fail. Cost is computed from
  token counts at [`pricing.json`](../pricing.json) list prices, because Claude Code misprices Haiku 5.5.
  `collect.py` prices each trial's total tokens at the base rate. Haiku 5.5 costs 5 times more for a
  request above 100K prompt tokens, and Harbor keeps no per-request counts, so the Haiku 5.5 cost is a lower
  bound. `collect.py` also prices cache writes as plain input (Harbor does not split them out), so every
  model's cost is somewhat low. The planned fix is in
  [next steps](../docs/plans/next-steps.md#cost-accounting-price-each-request-at-its-own-tier-planned-2026-10-16).
- Earlier attempts of round 2 lost all or most of their trials to Docker Desktop failures (emulated x86 images on an
  arm64 laptop); they are kept in `results.json` as `infra_error`, not as failures.

Reproduce: `./swebench-pro/make_samples.sh`, then `./swebench-pro/round2.sh`, then rerun each setup failure as job
`<model>-sample20-retry` (a manual step; `round2.sh` does not do it), then `./swebench-pro/collect.py` (writes `results.json` from the machine-local `jobs/`), then `./swebench-pro/round2_summary.py` (merges the
first tries with the setup retries into `round2.json` and `round2.md`).

## Known defects of this calibration (tracked as issues in this repository)

- Agents ran on the host, not in a container, for B01. Workers they started outlived their runs and
  shared one message broker with later runs and the grader. The grader now uses a private broker database and
  kills stray workers; the fix in full is one isolated container per trial.
- The B01 runner script was edited while a run executed it, which lost that run's timing (recovered from
  Claude Code's own `duration_ms`).
- One SWE-bench Pro trial hung for over 30 minutes with no API traffic (agent idle in the container); it is
  recorded as a hang, not as a pass or fail.
