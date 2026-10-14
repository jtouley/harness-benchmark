> Superseded for new run sets by [criteria v2](criteria-v2.md). This version stays as history.

# Benchmark criteria (v1)

Status: **pre-registered**. These criteria are fixed before the outcome runs that they judge.
A change to them is a new version with a changelog entry, and results are reported against
the version that was in force when the runs started. Results that come out against a harness
are reported the same way as results that come out for it.

## 1. The question

Is running a harness worth its cost, compared with the same model, or a cheaper one, doing
the same task alone?

"Worth it" is not "solves the task". In the one exploratory round (§7), a tool-using model alone passed every hidden test
on T04–T06, one run each. A harness is worth its cost
only if it delivers **fewer defects** or **more trustworthy evidence**, at a cost the decision
rule in §6 accepts.

## 2. Arms

| Arm | What runs | Prompt |
|---|---|---|
| Framework arm | A harness, installed as its README says, on model M | The framework's drive prompt plus the task text |
| `oneshot-M` | Model M alone, same tools, no framework | The neutral baseline prompt (below) |
| `oneshot-cheap` | A cheaper model alone | The neutral baseline prompt |

Every framework arm needs a `oneshot-M` arm on the **same model**. Without it, a result cannot
separate the harness from the model. `oneshot-cheap` is reported for context (what a cheaper
model alone delivers) and is not part of the decision rule.

### Neutral baseline prompt (rule)

The baseline prompt is the task text and nothing else. The environment (the repository, no
remote, nobody to answer questions) is the same for every arm and comes from the task image, not
from the prompt. The baseline gets **nothing** that tells it how to work: no TDD, no tests, no plan, no review, no quality words. Anything a framework arm's
prompt says beyond the task text is the framework's contribution and must not leak into the
baseline. In `frameworks.lock.json` the baseline `drive_prompt` is exactly `{issue}` (the same as
the superpowers arm). Committing is not asked for: grading reads the working tree.

"One-shot" means one agent session with the same tools as the framework arms (read, edit,
run). It does not mean a single completion without tools.

## 3. Task classes

| Class | What it is | Examples | Why it exists |
|---|---|---|---|
| **S** exact spec | The spec fixes every output and a hidden suite decides. T01–T03 touch one module; T04–T06 change several modules of one small app | T01–T06 | Control: a model alone should do well. A harness that loses here costs more for nothing |
| **L** repo-scale, open | Many modules, the agent must discover the design, the spec leaves choices open, other work is in flight | see below | Where a harness should earn its cost |
| **O** oracle-hard | Correctness needs an independent oracle; a plausible wrong answer passes a shallow check | see below | Measures false success, the most expensive failure |

Class L and O tasks come from real requests in the owner's repositories (October 2026). A
task is admitted only with a reference solution, an oracle the agent cannot see, and the
property that the untouched repository fails the oracle. The task list of a run set is frozen
before the first run: its sha256 (over `golden/tasks/`) is recorded in the run set's results,
and a task added later starts a new run set. A class L or O task enters a run set only once it is
committed under `golden/tasks/` (repository snapshot, hidden oracle, reference solution), so the
hash covers it. A script that records this hash is required before the first v1 run set.

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

Each measure is computed on the state the run leaves, by a script in this repository or, for
M2 and M7, from the recorded reviewer outputs under the protocol in §5. In v1, M1, M6, M8 and
M9 have scripts; M3, M4, M5 and M10 scripts are to be written before the first v1 run set, and
a run set without them does not report those measures. Claims in an agent's own summary are
never evidence for a measure.

| # | Measure | How it is computed | Role |
|---|---|---|---|
| M1 | **Acceptance** | Hidden tests (or the class O oracle) on the delivered working tree | Gate: a run that fails M1 is not delivered |
| M2 | **Reproduced defects** | A blind reviewer (§5) lists defects; each needs a command and its output that show it. Severity: critical (data loss, wrong result reported as success), major (crash, spec violation), minor | **Primary** |
| M3 | **False success** | Count of places where the run reports success but M1 or M2 shows failure (for example "all tests pass", "production-ready", or a wrong answer marked successful) | **Primary** for class O; reported for all |
| M4 | **Mutation kill rate** | Mutants on the changed lines only, run against the run's own tests; equivalent mutants removed by a second reviewer. A run that adds no tests scores 0 | Secondary |
| M5 | **Test-first evidence** | Replay the branch: a commit that adds tests counts as test-first when those tests fail on its parent commit and pass after the commit that adds the code. Uncommitted or single-commit work scores 0. A run that keeps red-run logs gets credit only when the log matches a replay | Secondary; reported, not assumed |
| M6 | **Changed-line coverage** | Line and branch coverage of the changed lines by the run's own tests | Reported only: in v1 data every arm scored 87–98%, so it does not separate arms |
| M7 | **Code quality rubric** | Blind rubric (§5): design, correctness, readability, tests; 1–10 each with anchored levels | Secondary |
| M8 | **Completion** | Finished without a human answer; a hard stop or a question to the user counts as not complete | Reported |
| M9 | **Cost** | Wall time; input, cache and output tokens **including nested subagents**, taken from the host's own accounting of the whole session, not from one agent's summary. Whether Harbor's `result.json` counts nested subagents is not yet checked; until it is, harness token counts are reported as lower bounds; dollars from `pricing.json` | Denominator |
| M10 | **Auditability** | Plan, independent reviews (a reviewer that is not the implementer, checked by attestation where the framework has it), and a closure record exist and match the delivered head | Reported per framework; not scored against one-shot arms |

## 5. Blind review protocol

- **Two independent reviewers per task.** Each sees every arm's final source and test files
  and its diff from the base commit, as anonymous folders. They do not see commit history,
  plans, review records, `.context/`, `.cursor/` or any process file. Framework names,
  ticket ids and process notes are removed from comments; the label map is stored outside
  the folders.
- **Defects (M2).** A reviewer lists each defect with a repro command and its expected and
  observed output. A script re-runs every repro command in a clean copy of that arm's tree;
  a defect counts only if the script reproduces it. Reproduced defects from both reviewers are
  merged by root cause (two entries with the same failing command and cause are one defect).
  When both reviewers list a defect, it takes the lower of their two severities; when one does,
  its severity stands.
- **Rubric (M7).** Each reviewer scores four dimensions 1–10 with these anchors: 9–10 no
  defect found, idiomatic, tests cover failure paths; 7–8 minor issues; 5–6 a major defect or
  clear over- or under-engineering; 3–4 several major defects; 1–2 data loss or wrong results.
  A dimension where the two reviewers differ by more than 2 goes to a third reviewer, and the
  median of the three is reported; otherwise the mean of the two.

## 6. Decision rule (pre-registered)

**Sample.** Each (task, arm) cell runs exactly **5 times**. The number is fixed before the run
set and is not raised after results are seen. A class claim needs at least **3 tasks** of that
class; with fewer, the class result is "not enough tasks".

**Caps.** Each trial runs under fixed caps, recorded here and pinned by `tests/test_criteria.py`:
an agent timeout of **1800 s** (`cbench/harbor.py`, `timeout_sec`), and a dollar cap of **$1.00**
for Haiku arms and **$3.00** for the Sonnet baseline (`scripts/live.sh` defaults). A trial that hits
a cap is not delivered. The caps are part of the run set and do not change after results are seen.
*Open owner decision before the first run set:* in the exploratory round harness runs took
3,366–4,964 s (Opus, another host), so a 1800 s timeout may stop harness arms early and count them
as not delivered. Raising the caps raises the worst-case spend; the chosen values are recorded here
before the run set starts.

**Units.** Every measure is per **attempted** run. A run that does not deliver (fails M1 or M8)
counts as one critical defect for M2 and as one false success for M3 if it reports success.
M3 is a per-run rate (false-success events / attempted runs).

**Interval.** For a difference between two arms on a class, resample runs with replacement
within each (task, arm) cell, 10,000 times, with seed 20261010; compute `mean(oneshot-M) −
mean(F)` over the class each time, so a positive value favors F; report the 5th and 95th
percentiles (a 90% percentile interval). Tasks are not resampled, so a claim covers the tasks run.

For each framework F on model M, compare with `oneshot-M` on the same tasks. F is **worth its
cost on a task class** when all of these hold:

1. **Fewer defects:** mean critical + major M2 per attempted run is lower than `oneshot-M` by
   at least 0.5, and the 90% interval of the difference is entirely above 0.
2. **No more false success:** F's M3 rate is not higher than `oneshot-M`'s (a tolerance of 0.05 absorbs about one event per 20 attempted runs; with 15 runs per arm it absorbs none).
3. **Delivery is not worse:** F's M1 pass rate per attempted run is at least `oneshot-M`'s
   minus 10 points.
4. **Cost:** cost per defect-free delivered run (M9 / attempted runs that pass M1 with zero
   critical or major defects) is reported. It is not a pass/fail line; a framework that meets
   1–3 at more than 10× the cost per defect-free run is reported as "better, at a cost". An arm
   with no defect-free run has no finite cost per defect-free run; that is reported as such.

If 1–3 do not all hold, the class result is "not shown". Class S results are reported but are
not expected to show a difference.

**What v1 can decide today.** Only class S has 3 or more tasks (T01–T06). Classes L (2 named) and
O (1 named) need at least 3 committed tasks each before a class claim is possible. Until then, v1
can show whether a harness reduces defects on exactly specified tasks, and not yet on the open
tasks where a harness should matter most.

## Disclosure

The owner of this benchmark also wrote one of the harnesses (Cadence) and supplied the class L
and O tasks. Because of that, the criteria, the task list (by hash) and the sample size are
fixed before any run set, results are published whichever way they fall, and every reviewer
is blind to the arm.

## 7. Evidence that shaped v1

The criteria above come from one exploratory round (2026-10-09/10, n = 1 per cell, outside
this harness; summary and data in [`docs/experiments/2026-10-10-harness-vs-oneshot.md`](experiments/2026-10-10-harness-vs-oneshot.md)).
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
