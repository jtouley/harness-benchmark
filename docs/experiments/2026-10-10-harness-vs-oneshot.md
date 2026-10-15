# Experiment: two harnesses vs. one-shot Haiku and Sonnet on three feature tasks

Date: 2026-10-09 to 2026-10-10. Status: exploratory, one run per cell (n=1), run outside this harness. It shaped
[criteria v1](../criteria.md); it is not a v1 result.

> **Iteration 4** ([write-up](2026-10-12-iteration-4.md)) adds the missing Opus one-shot control. It shows no
> quality gain from a harness over Opus alone. Read it, and [the findings](../findings.md), before citing this round.

## Question

On a multi-module feature, does a plan-to-PR harness give better code than a model that
gets the same prompt and works alone? And at what cost?

## Arms

| Arm | Model | Process | What the agent got |
|---|---|---|---|
| `with_skill` (Cadence) | Opus 5.5 subagent | Cadence at jtouley/cadence `main` 6abc622: A1–R7, peers for reviews | Template H (below) with `/cadence <task>` |
| `old_skill` (ship-feature) | Opus 5.5 subagent | `~/.cursor/skills/ship-feature`, Stages 0–6 | Template H with `/ship-feature <task>` |
| `sonnet_oneshot` | Sonnet 5.5 subagent | none | Template B (below) |
| `haiku_oneshot` | Haiku 4.5 subagent | none | Template B |

All agents had the same tools (Claude Code general-purpose subagent: shell, file edit) and
started from the same commit ("ledgerlite baseline", the fixture in this folder's source
workspace, identical to harness-benchmark `golden/tasks/T0[456]*/repo`).

### Template H (harness arms)

```
Execute this task:
- Skill path: <skill dir> (read SKILL.md there and follow it end to end[; set CADENCE_HOME to that path for every script])
- Task: /<skill> <TASK TEXT>
- Repository: <repo> (git; branch main; origin is a local bare repo). Do all work there.
- Save outputs to: <outputs>/
- Outputs to save: summary.md (what you did, each pipeline stage and its result), PR.md (the PR title and body)
- Environment (same for every run): there is no GitHub and no Linear. Where the skill creates, updates, or comments on a PR or ticket, write that text to outputs/PR.md (append comments) and continue as if it succeeded. Nobody will answer questions: work autonomously to the end of the skill's pipeline. If writing an output file is blocked, put its full text in your final report.
```

### Template B (one-shot arms): Template H with the skill line, the slash command and every pipeline reference removed. Nothing added.

```
Execute this task:
- Task: <TASK TEXT>
- Repository: <repo> (git; branch main; origin is a local bare repo). Do all work there.
- Save outputs to: <outputs>/
- Outputs to save: summary.md (what you did), PR.md (the PR title and body)
- Environment: there is no GitHub and no Linear. Write PR text to outputs/PR.md. Nobody will answer questions: work autonomously to the end. If writing an output file is blocked, put its full text in your final report.
```

`<TASK TEXT>` is the `prompt` of each task in `evals.json`, word for word, for every arm.

## Measurement

1. **Hidden acceptance tests** (`hidden/`, same as harness-benchmark T04–T06 after PR #4):
   run on the delivered working tree. Pass = all hidden tests pass.
2. **Blind code-quality rubric** (`blind4_scores/*.json`): one Opus grader per task saw every
   solution side by side as anonymous folders (final `ledgerlite/`, `tests/`, and a diff
   from the baseline commit). Harness ids were scrubbed from comments; the label mapping
   (`blind4_mapping.json`) was outside the folders. Four dimensions, 1–10 each: design,
   correctness (the grader ran the CLI to reproduce defects), readability, tests. Mean of four.
3. **Cost**: wall time and the tokens reported by the subagent completion notice.
4. **Process checks** (`grade.py` C1–C10): apply to harness arms only. One-shot arms fail
   them by design and are not compared on them.

## Results

| Task | Arm | Hidden | Quality (mean) | Wall time | Tokens |
|---|---|---|---|---|---|
| multicurrency | Cadence | 6/6 | 6.75 | 3,554 s | 299,660 |
| multicurrency | ship-feature | 0/6 (stopped at Stage 3, no code) | – | 715 s | 143,214 |
| multicurrency | Sonnet one-shot | 6/6 | **8.00** | 60 s | 60,397 |
| multicurrency | Haiku one-shot | 6/6 | 5.25 | 250 s | 67,191 |
| budgets | Cadence | 7/7 | 7.00 | 4,964 s | 340,287 |
| budgets | ship-feature | 7/7 | **7.25** | 3,366 s | 288,021 |
| budgets | Sonnet one-shot | 7/7 | 7.00 | 60 s | 61,313 |
| budgets | Haiku one-shot | 7/7 | 4.75 | 224 s | 63,548 |
| audit-undo | Cadence | 6/6 | **8.50** | 751 s | 209,060 |
| audit-undo | ship-feature | 6/6 | 8.25 | 2,310 s | 266,247 |
| audit-undo | Sonnet one-shot | 6/6 | 6.25 | 55 s | 59,108 |
| audit-undo | Haiku one-shot | 6/6 | 2.25 | 310 s | 84,910 |

| Arm | Mean quality | Tasks with code | Mean wall time | Mean tokens |
|---|---|---|---|---|
| ship-feature | 7.75 | 2 of 3 | 2,130 s | 232k |
| Cadence | 7.42 | 3 of 3 | 3,090 s | 283k |
| Sonnet one-shot | 7.08 | 3 of 3 | 58 s | 60k |
| Haiku one-shot | 4.08 | 3 of 3 | 262 s | 72k |

## Findings

1. **Hidden tests do not separate the arms.** Every arm that wrote code passed every hidden
   test. Quality differences only showed under the blind rubric, where graders reproduced
   real defects in solutions that passed: Haiku audit-undo loses a re-added account after an
   undo and hides undone entries from `audit`; Haiku budgets alerts on refunds and crashes on
   `budget set x NaN`; Haiku multicurrency accepts NaN and negative rates and breaks on
   lowercase codes. A benchmark that scores only hidden tests would rank Haiku one-shot equal
   to the harnesses.
2. **The harnesses lift the cheap model the most, but a strong one-shot is close.** Sonnet
   one-shot (7.08) is within 0.3–0.7 of both harnesses at about 1/50 of the wall time and
   1/4 of the tokens. It won multicurrency outright (8.0 vs Cadence 6.75: the grader marked
   Cadence down for extra machinery and an inverse-rate fallback the spec did not ask for).
3. **Harness wins came on the task with the most hidden state.** On audit-undo (undo
   correctness, all-or-nothing writes), both harnesses scored 8.25–8.5 against Sonnet 6.25
   and Haiku 2.25. That is where review loops paid off.
4. **Harnesses tend to over-build.** Both harness arms added scope the spec did not ask for
   (limit caps, Decimal overflow handling, importer hardening, a rate fallback). Graders
   marked this down on design in 4 of 5 harness solutions.
5. **Completion differs.** Cadence finished 3 of 3; ship-feature stopped on multicurrency
   after its own plan-review limit (and a denied subagent launch, see Confounds).

## Confounds and limits (read before citing)

- **The one-shot baselines could see the user-level skill list** (the same host as iteration 4, where a
  transcript check found that no one-shot used a skill). This round's transcripts were not checked. See
  [the clean room](../process.md#clean-room).
- **"One-shot" means one tool-using agent, not one completion.** Each baseline was a Claude
  Code subagent that could read the repo, edit, and run tests in a loop (Sonnet 6–10 tool calls,
  Haiku 57–62). It had no plan, reviewers or gates. A single completion without tools was not tested.
- **The tasks are small and precisely specified.** ledgerlite is ~300 lines in five modules; each
  feature touches 4–5 files; the prompt fixes every output format; hidden suites have 6–7 tests.
  The results say nothing about large codebases, vague specs, or changes that do not fit in one
  context window, which is where a harness should matter most. harness-benchmark needs at least
  one task of that size before this comparison means much.
- **n = 1 per cell.** Differences under ~1 quality point are within single-run noise.
- **Models differ.** Harness arms ran on Opus 5.5; baselines on Sonnet 5.5 and Haiku 4.5.
  This experiment cannot separate "harness" from "Opus". The missing cell is an Opus one-shot.
  Port this as four arms plus `opus_oneshot`.
- **Token counts likely undercount the harness arms.** The completion notice reports the
  run agent's tokens. Cadence and ship-feature delegate reviews to nested subagents, whose
  tokens may not be included. Treat harness token counts as lower bounds; wall time is reliable.
- **Cadence audit-undo reviewed its own work** (no separate peers; jtouley/cadence#47). Its
  8.5 is not evidence for independent review.
- **ship-feature multicurrency**: its own plan review set a hard stop after two blocking
  cycles; its attempt to launch one more subagent was denied by the host permission system.
  Part environment, part skill behavior.
- **Grader**: one Opus grader per task, not repeated; graders saw all arms together, which
  helps calibration but lets one solution anchor the others.
- **Environment**: Claude Code subagents on macOS, no GitHub; PR flow simulated in `PR.md`.

## Files

Committed here: this summary and `2026-10-10-harness-vs-oneshot.json` (the results table as
data). The full run data (prompts per run, `grade.py`, hidden tests, per-run grading and
timing, blind rubric files with reproduced defects, label map) is kept in the owner's
workspace (`.context/evals/harness-vs-oneshot-2026-10-10/` in the cadence workspace; a copy is under `.context/experiments/` of this repository's owner checkout). The hidden tests are the same as
`golden/tasks/T0[456]*/hidden/` after PR #4.

## What this round changed in the benchmark

Historical: these were the recommendations at the time. [Criteria v1](../criteria.md) supersedes them where they differ (for example, n = 5 per cell).

- Tasks T04–T06 already exist there with the same hidden tests.
- Add arms `sonnet_oneshot`, `haiku_oneshot`, `opus_oneshot` with Template B as the drive
  prompt (no framework install), next to the existing framework arms.
- Add the blind rubric as a scored tier: per task, anonymize final trees + diff, one grader
  sees all arms, four 1–10 dimensions, defects must be reproduced. Report it beside hidden
  pass rate, because hidden tests alone did not separate the arms here.
- Run each cell at least 3 times before ranking.
