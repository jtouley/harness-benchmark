# Benchmark criteria (v1)

Status: **pre-registered**. These criteria are fixed before the outcome runs that they judge.
A change to them is a new version with a changelog entry, and results are reported against
the version that was in force when the runs started. Results that come out against a harness
are reported the same way as results that come out for it.

## 1. The question

Is running a harness worth its cost, compared with the same model, or a cheaper one, doing
the same task alone?

"Worth it" is not "solves the task". A tool-using model alone already passes every hidden test
on the current small tasks (see [§7](#7-evidence-that-shaped-v1)). A harness is worth its cost
only if it delivers **fewer defects** or **more trustworthy evidence**, at a cost the decision
rule in §6 accepts.

## 2. Arms

| Arm | What runs | Prompt |
|---|---|---|
| Framework arm | A harness, installed as its README says, on model M | The framework's drive prompt plus the task text |
| `oneshot-M` | Model M alone, same tools, no framework | The neutral baseline prompt (below) |
| `oneshot-cheap` | A cheaper model alone | The neutral baseline prompt |

Every framework arm needs a `oneshot-M` arm on the **same model**. Without it, a result cannot
separate the harness from the model.

### Neutral baseline prompt (rule)

The baseline gets the task text, the repository location, where to put outputs, and the facts
of the environment (no remote, nobody answers questions). It gets **nothing** that tells it how
to work: no TDD, no tests, no plan, no review, no quality words. Anything a framework arm's
prompt says beyond the task text is the framework's contribution and must not leak into the
baseline. The exact template is versioned in this repository with each task set.

"One-shot" means one agent session with the same tools as the framework arms (read, edit,
run). It does not mean a single completion without tools.

## 3. Task classes

| Class | What it is | Examples | Why it exists |
|---|---|---|---|
| **S** small, exact | A few files, the spec fixes every output, a hidden suite decides | T01–T06 | Control: a model alone should do well. A harness that loses here costs more for nothing |
| **L** repo-scale, open | Many modules, the agent must discover the design, the spec leaves choices open, other work is in flight | see below | Where a harness should earn its cost |
| **O** oracle-hard | Correctness needs an independent oracle; a plausible wrong answer passes a shallow check | see below | Measures false success, the most expensive failure |

Class L and O tasks come from real requests in the owner's repositories (October 2026). A
task is admitted only with a reference solution, an oracle the agent cannot see, and the
property that the untouched repository fails the oracle.

- **L1 (headless runtime):** make an app with a UI run fully through a CLI and an API for
  testing, while open pull requests already cover part of the work. Tests overlap detection,
  design discovery, and integration with other branches.
- **L2 (PR sweep):** review every open pull request, merge the findings into one document,
  and ship the fixes. Tests review depth and fix scope across branches.
- **O1 (golden questions):** build verifiable question sets per dataset and make a natural
  language + SQL engine answer them. The real failure observed: 400 templated questions passed,
  15 hard questions failed, and 12 of those reported success with the wrong number. The oracle
  is a SQL answer key the agent cannot see.

## 4. Measures

All measures are computed by scripts in this repository on the state the run leaves.
Claims in an agent's own summary are never evidence for a measure.

| # | Measure | How it is computed | Role |
|---|---|---|---|
| M1 | **Acceptance** | Hidden tests (or the class O oracle) on the delivered working tree | Gate: a run that fails M1 is not delivered |
| M2 | **Reproduced defects** | A blind reviewer (§5) lists defects; each needs a command and its output that show it. Severity: critical (data loss, wrong result reported as success), major (crash, spec violation), minor | **Primary** |
| M3 | **False success** | Count of places where the run reports success but M1 or M2 shows failure (for example "all tests pass", "production-ready", or a wrong answer marked successful) | **Primary** for class O; reported for all |
| M4 | **Mutation kill rate** | Mutants on the changed lines only, run against the run's own tests; equivalent mutants removed by a second reviewer | Secondary |
| M5 | **Test-first evidence** | Replay the branch: a commit that adds tests counts as test-first when those tests fail on its parent commit and pass after the commit that adds the code. Uncommitted or single-commit work scores 0. A run that keeps red-run logs gets credit only when the log matches a replay | Secondary; reported, not assumed |
| M6 | **Changed-line coverage** | Line and branch coverage of the changed lines by the run's own tests | Reported only: in v1 data every arm scored 87–98%, so it does not separate arms |
| M7 | **Code quality rubric** | Blind rubric (§5): design, correctness, readability, tests; 1–10 each with anchored levels | Secondary |
| M8 | **Completion** | Finished without a human answer; a hard stop or a question to the user counts as not complete | Reported |
| M9 | **Cost** | Wall time; input, cache and output tokens **including nested subagents**; dollars from `pricing.json` | Denominator |
| M10 | **Auditability** | Plan, independent reviews (a reviewer that is not the implementer, checked by attestation where the framework has it), and a closure record exist and match the delivered head | Reported per framework; not scored against one-shot arms |

## 5. Blind review protocol

- One reviewer per task sees every arm's final tree and its diff from the base commit, as
  anonymous folders. Framework names, ticket ids and process notes are removed from comments
  and paths; the label map is stored outside the folders.
- The reviewer may read and run code. A defect is counted only with a reproduction.
- Rubric anchors: 9–10 no defect found, idiomatic, tests cover failure paths; 7–8 minor
  issues; 5–6 a major defect or clear over- or under-engineering; 3–4 several major defects;
  1–2 data loss or wrong results.
- Each task is reviewed twice by independent reviewers. Disagreement over 2 points on any
  dimension sends the task to a third review, and the median is reported.

## 6. Decision rule (pre-registered)

Run each (task, arm) cell at least **3 times**. For each framework F on model M, compare with
`oneshot-M` on the same tasks.

A framework is **worth its cost on a task class** when all of these hold:

1. **Fewer defects:** the mean count of critical + major reproduced defects (M2) per delivered
   run is lower than `oneshot-M` by at least 1, and the 90% bootstrap interval of the
   difference does not include 0.
2. **No more false success:** M3 for F is not higher than for `oneshot-M`.
3. **Delivery is not worse:** F's M1 pass rate is at least `oneshot-M`'s minus 10 points.
4. **Cost:** cost per defect-free delivered run (M9 / runs with M1 pass and zero critical or
   major defects) is reported. It is not a pass/fail line, but a framework that wins 1–3 at
   more than 10× the cost per defect-free run is reported as "better, at a cost".

If 1–3 do not all hold, the result for that class is "not shown". Class S results are reported
but are not expected to show a difference.

## 7. Evidence that shaped v1

The criteria above come from one exploratory round (2026-10-09/10, n = 1 per cell, outside
this harness; see `.context/experiments/harness-vs-oneshot-2026-10-10/` in the owner's copy).
Three ledgerlite features (T04–T06), four arms: Cadence and ship-feature on Opus, Sonnet and
Haiku alone.

- Every arm that wrote code passed every hidden test (M1 does not separate).
- Coverage was 87–98% in every arm (M6 does not separate).
- One-shot arms committed once or not at all, so no test-first evidence exists for them (M5).
- The blind review found defects that the hidden tests missed: Haiku alone lost data after an
  undo and accepted NaN rates while passing all hidden tests (M2 separates).
- Blind quality means: ship-feature 7.75 (2 of 3 tasks delivered), Cadence 7.42, Sonnet alone
  7.08, Haiku alone 4.08. The harness arms ran on Opus and there was no Opus-alone arm, so this
  round cannot attribute the difference to the harness. v1 makes `oneshot-M` mandatory.

## Changelog

- v1 (2026-10-10): first version.
