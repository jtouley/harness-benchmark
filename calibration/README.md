# Calibration and harness arms

Task selection is calibrated against the bar ([next steps](../docs/next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13)).
This folder holds the calibration runs' scripts and summaries, and the minimal harnesses used as arms.

## Layout

| Path | What | Tracked |
|---|---|---|
| `swebench-pro/` | SWE-bench Pro (Harbor `scale-ai/swe-bench-pro`) calibration: sample lists, the round script, the results collector, `results.json` | yes |
| `swebench-pro/jobs/`, `swebench-pro/tasks/` | Harbor job outputs and downloaded task definitions | no (machine-local, large) |
| `../harnesses/reviewloop/` | Review loop: the session model works, an independent `reviewer` subagent (Opus) checks the running result, the session model fixes until it approves (max 3 reviews) | yes |
| `../harnesses/reviewloop-sonnet-reviewer/` | The same, with the reviewer on Sonnet | yes |
| `../harnesses/verifyloop/` | Verification harness: a `contract-writer` subagent writes an executable `CONTRACT.md` before any code; a Stop hook runs it and blocks the session from finishing while a check fails | yes |
| `../private/` | Private tasks (B01, a brownfield bug from a third-party interview repository): prompt, grader, runner, run copies | **no**: this repository is public. Only scores are published, in [next steps](../docs/next-steps.md) |

Each harness is a Claude Code plugin, loaded for one session with `claude --plugin-dir <harness>`. Its
instructions are generic: none names a task, its data or its traps ([prompt hygiene](../docs/tasks/pipeline-family.md#prompt-hygiene)).

## SWE-bench Pro, so far (Opus 5.5 one-shot, Harbor, Claude Code in the task container)

- Round 1: 20 sampled Python tasks, one try each: 17 passed, 2 failed, 1 did not start (setup timeout).
- Round 2: three more tries on the two failures and the one that did not start:
  - `ansible-d2f80991`: 2 of 5 passed (a **beyond** candidate: the bar is unreliable);
  - `openlibrary-30bc73a1`: 2 of 5 passed (a **beyond** candidate);
  - `ansible-d9f18662`: 4 of 4 passed (the round 1 miss was infrastructure).
- Round 2 also runs one Sonnet 5.5 and one Haiku 5.5 try on all 20, to find **lift** candidates (the bar
  passes, a cheap one-shot does not).
- Two earlier attempts of round 2 lost every trial to Docker Desktop failures (emulated x86 images on an
  arm64 laptop); they are kept in `results.json` as `infra_error`, not as failures.

Reproduce: `./swebench-pro/make_samples.sh`, then `./swebench-pro/round2.sh`, then `./swebench-pro/collect.py`.

## Known defects of this calibration (tracked as issues in this repository)

- Agents ran on the host, not in a container, for B01. Workers they started outlived their runs and
  shared one Redis port with later runs and the grader. The grader now uses a private Redis database and
  kills stray workers; the fix in full is one isolated container per trial.
- The B01 runner script was edited while a run executed it, which lost that run's timing (recovered from
  Claude Code's own `duration_ms`).
- One SWE-bench Pro trial hung for over 30 minutes with no API traffic (agent idle in the container); it is
  recorded as a hang, not as a pass or fail.
