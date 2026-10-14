# Benchmark criteria (v2)

Status: **pre-registered** for the next run set. These criteria are fixed before the outcome runs that
they judge. A change to them is a new version with a changelog entry. Results are reported against the
version that was in force when the runs started. Results that come out against a harness are reported
the same way as results that come out for it. [Criteria v1](criteria.md) stays as history. Runs that
started under v1 are reported against v1.

This document is complete by itself. Each rule names its source in square brackets. The source keys are
in the table below. A rule marked **[v2]** is an operational definition that this document adds, so that
an owner decision can be computed. Each [v2] rule is listed in §11 for owner confirmation before the first
v2 run set.

| Key | Source | Date |
|---|---|---|
| [v1] | [criteria v1](criteria.md) | 2026-10-10 |
| [OD] | [next steps: owner decisions](next-steps.md#owner-decisions-for-this-design-2026-10-12) | 2026-10-12 |
| [CAP] | [next steps: decision rule, "Caps (owner decision)"](next-steps.md#decision-rule-for-this-question) | 2026-10-12 |
| [DR] | [next steps: decision rule for this question](next-steps.md#decision-rule-for-this-question) | 2026-10-12 |
| [PRE] | [next steps: prerequisites](next-steps.md#prerequisites-stage-0) | 2026-10-12 |
| [TS] | [next steps: task selection, calibrated against the bar](next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13) | 2026-10-13 |
| [TC] | [next steps: two task classes (revised)](next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13) | 2026-10-14 |
| [CR] | [process: clean room](process.md#clean-room) | 2026-10-12 |
| [#16] | [harness-benchmark#16](https://github.com/jtouley/harness-benchmark/issues/16): adopt the quality model as criteria v2 | 2026-10-13 |
| [QM] | [quality model](quality-model.md) (adopted by [#16]) | 2026-10-13 |
| [OC] | [quality model: owner criteria](quality-model.md#owner-criteria-2026-10-14-dry-solid-extensible-traceable-cheap) | 2026-10-14 |
| [PF] | [pipeline family](tasks/pipeline-family.md): success criteria, arms, deferral review, prompt hygiene, isolation, audit protocol | 2026-10-14 |
| [FU] | [follow-up task](tasks/pipeline-followup.md) | 2026-10-14 |
| [WP] | [whitepaper](whitepaper.md) | 2026-10-14 |
| [#10] | [harness-benchmark#10](https://github.com/jtouley/harness-benchmark/issues/10): one isolated container per trial | 2026-10-14 |

## 1. The question

**What is the cheapest model that, inside a harness, matches or beats the Opus 5.5 one-shot, and leaves
an audit trail that a one-shot run cannot?** [OD]

v1 asked whether a harness on model M is worth its cost against M alone [v1]. v2 keeps that comparison,
so the harness effect and the model effect stay separate [DR]. v2 adds the comparison with the bar: the
Opus 5.5 one-shot [OD].

"Worth it" is not "solves the task" [v1]. A harness may use many more tokens than the bar. What counts
is the dollar cost per defect-free delivered run, the defects that reach the delivered code, the
reliability over repeated runs, and the evidence that the run leaves behind [OD] [WP].

For the long tasks, the owner's success question is: **which arm comes closest to a DRY, SOLID and
extensible system, whose path we can understand, and at what cost** [OC] [PF].

## 2. Arms

### 2.1 Arms in the v2 run set

| Arm | Model | What runs | Role | Source |
|---|---|---|---|---|
| **Opus one-shot (the bar)** | Opus 5.5 | Opus alone, no harness | The reference for checks, defects, reliability and design. Not a harness arm | [OD] [PF] |
| Haiku one-shot | Haiku 5.5 | Haiku alone | The baseline of every harness arm (same model) | [v1] [PF] |
| Sonnet one-shot | Sonnet 5.5 | Sonnet alone | Context: a mid-price model alone | [PF] |
| Review loop | Haiku 5.5 works, Haiku 5.5 reviews | The cheap model works; an independent reviewer subagent checks the running result; the cheap model fixes | Harness arm | [PF] |
| Verification harness | Haiku 5.5 | A contract writer writes executable checks before any code; a stop gate runs them and blocks the end of the session while one fails; no model reviewer | Harness arm | [PF] [WP] |
| Cadence, all Haiku | Haiku 5.5 | Full Cadence with `peer_models: {"default": "haiku"}`, after jtouley/cadence#63–#66 are fixed | Harness arm | [PF] |

**Haiku-only harness arms.** Every harness arm runs on Haiku 5.5, reviews included, unless the arm says
otherwise. A harness may spend many tokens if each token is cheap [PF] [OD]. Opus never orchestrates a
harness run and never runs a harness arm [OD].

### 2.2 Named comparison arms

These arms are run only where named. They are reported for context and are not part of the decision rule.

| Arm | Where | Why | Source |
|---|---|---|---|
| Review loop with a Sonnet 5.5 or Opus 5.5 reviewer (Haiku 5.5 or Sonnet 5.5 works) | B01 only | Shows what a stronger reviewer adds, per dollar | [PF] [TS] |
| Haiku one-shot and Sonnet one-shot on calibration tries | Every candidate task | Classify a task as lift or beyond (§3) | [TC] [PF] |

The 2026-10-12 design also named Cadence with Opus reviews, Haiku 4.5, Cursor CLI and OpenAI arms [OD].
The 2026-10-14 arm list [PF] does not include them, so they are **not** in the v2 run set. A later
version can add them with a changelog entry [v2].

Sonnet 5.5 runs no harness arm [OD]. Each harness arm has a one-shot arm on the same model [v1].

### 2.3 Neutral baseline prompt (rule)

The baseline prompt is the task text and nothing else [v1]. The environment comes from the task image,
not from the prompt [v1]. The baseline gets nothing that tells it how to work: no TDD, no tests, no plan,
no review, no quality words [v1]. In `frameworks.lock.json` the baseline `drive_prompt` is exactly
`{issue}` [v1]. Committing is not asked for: grading reads the working tree [v1].

"One-shot" means one agent session with the same tools as the harness arms (read, edit, run). It does not
mean a single completion without tools [v1].

### 2.4 Prompt hygiene

The prompts must not poison any run [PF]:

1. Every arm gets the same request text, word for word. No arm's prompt adds hints, quality adjectives
   ("staff level", "production quality") or knowledge of the traps, checks or follow-up [PF].
2. A harness arm differs only by its installed harness (plugin, hooks, skill) and one line that names it
   (for example "Use the review-loop skill."). The harness's own instructions are generic. None names a
   task, its data or its traps [PF].
3. The follow-up request is not visible to any arm until its base task is frozen [PF] [FU].
4. The trap catalog, the answer key and the task's grading documents are not in any arm's environment
   [PF].
5. The staff-level bar is applied by the grading (checks, quality model, audit), not by the prompt [PF].

### 2.5 Deferral review

In every harness arm, each deferral (work that the harness decides not to do now) goes to an independent
Haiku 5.5 reviewer at the moment it is proposed [PF]:

- The reviewer judges the deferral against the request. **Accept:** the work is outside the request, or
  blocked, with a reason. **Reject:** the work is part of the request [PF].
- A rejected deferral is implemented before the run may finish [PF].
- The log of proposals and verdicts is part of the run record and of the audit (§7) [PF].
- A part of the request that a run drops without a recorded, accepted deferral is a defect (M2) [WP] [v2].

This rule comes from B01, where a cheap one-shot diagnosed a second defect, decided to leave it out, and
then reported nothing [PF] [WP]. Cadence does not do this yet (jtouley/cadence#68) [PF].

## 3. Tasks and task classes

### 3.1 Calibration

A task is "hard" only when the bar fails it, not when it looks hard [TS]. Every candidate task gets
calibration tries before it is admitted [TS]:

- The Opus one-shot, and each cheap one-shot (Haiku 5.5, Sonnet 5.5), run on the task in a clean,
  isolated environment (§5) [TS] [PF].
- The task's own acceptance check grades each try [TS].
- A calibration record is kept per task: each try, its cost, its time and the grader output [TS].
- The untouched starting state fails every check [PF] [v1].

### 3.2 The two task classes

Classes S, L and O of v1 describe a task's shape [v1]. In v2 they stay as descriptions only. The class
of a claim is set by calibration [TC]:

| Class | Admitted when | Question | Source |
|---|---|---|---|
| **Lift** | The Opus one-shot is reliable and the cheap one-shots are not | Does a harness lift the cheap model to the bar's reliability, and at what cost? | [TC] |
| **Beyond** | The Opus one-shot is unreliable | Does a harness raise reliability above the bar? | [TS] [TC] |

Operational thresholds [v2]:

- **Beyond:** the Opus one-shot passes at most 1 of 3 calibration tries [TS].
- **Lift:** the Opus one-shot passes 5 of 5 tries, and at least one cheap one-shot arm fails 1 or more of
  its 5 tries [v2].
- A task that is in neither class is dropped, however large it looks [TS]. A task that the bar fails gets
  the harness arms; a task that the bar passes and every cheap one-shot also passes 5 of 5 does not [TS]
  [v2].

### 3.3 Task sources

1. **Private brownfield tasks.** Real repositories that cannot be published. The benchmark publishes the
   scores and the grader design, not the code [TS]. B01 is the first: a private brownfield bug in a
   multi-service application.
2. **Review-caught defects from Cadence's own history.** The task is the original request. The hidden
   check is the behavior that the review added [TS].
3. **A published hard set** (for example the public SWE-bench Pro split), for comparison with outside
   numbers, filtered by the same calibration rule [TS].
4. **The pipeline family** (P1, P2, P3): one request on three stacks, each with a follow-up task [PF] [FU].
   Each stack is classified separately, from 5 Opus one-shot runs and 5 runs of each cheap one-shot
   [PF].

Each task starts from a symptom or a product request, as a user would write it [TS]. Grading is
implementation-agnostic: the acceptance check observes the product outcome in the running system, never
function names that one fix happened to use [TS].

T04–T06 (v1 class S) run only as a contrast set, to test whether the harness matters more on hard tasks
than on easy ones [OD] [DR]. T05 is the pilot task [OD].

### 3.4 Freezing the task list

The task list of a run set is frozen before the first run. Its sha256 over `golden/tasks/` is recorded in
the run set's results. A task added later starts a new run set [v1]. A public task enters a run set only
once it is committed under `golden/tasks/` with its starting state, hidden oracle and reference solution
[v1]. A private task enters with the sha256 of its private task folder recorded in the results; its
contents are not published [TS] [v2].

## 4. Measures

Each measure is computed on the state that the run leaves, by a script in this repository, or from the
recorded reviewer outputs under §6 [v1]. Claims in an agent's own summary are never evidence for a measure
[v1]. A measure that has no script at the start of a run set is not reported for that run set [v1].

The quality measure is the [quality model](quality-model.md), in three layers [#16] [QM]. No layer
replaces another, and there is no single blended score: each arm gets one table with the layers side by
side [QM].

### 4.1 Layer 1: it does what the request says

| # | Measure | How it is computed | Role | Source |
|---|---|---|---|---|
| M1 | **Acceptance** | The hidden checks (or the oracle) on the delivered working tree, in the running system where the task has one | Gate: a run that fails M1 is not delivered | [v1] [TS] |
| M1f | **Hidden-suite pass fraction** | The fraction of the hidden checks that pass (30 or more per task where the task has a suite) | Reported | [QM] |
| M2 | **Reproduced defects** | Blind reviewers (§6) list defects. Each needs a command and its output, re-run by a script in a clean copy. Severity: critical (data loss, wrong result reported as success), major (crash, spec violation), minor. A test-confirmed defect (a reproduction test that fails on the run's code and passes on the reference solution) needs no severity call to count as confirmed | **Primary** | [v1] [QM] |
| M3 | **False success** | Places where the run reports success but M1 or M2 shows failure. A harness that stops with a recorded reason is not a false success | **Primary** for beyond tasks; reported for all | [v1] [DR] |
| M8 | **Completion** | Finished without a human answer. A hard stop or a question to the user counts as not complete | Reported | [v1] |

### 4.2 Layer 2: the tool gate

Computed by [`scripts/quality_metrics.py`](../scripts/quality_metrics.py), with the tools pinned in the
lockfile. A finding counts only on a line that the change added, or in a function whose body holds one. A
tool that fails leaves its measure unmeasured, and the gate then fails [QM].

| Measure | Threshold | Source |
|---|---|---|
| New-code line and branch coverage | ≥ 80% | [QM] (Sonar way gate) |
| Cognitive complexity per new function | ≤ 15 | [QM] (SonarSource) |
| Cyclomatic complexity per new function | ≤ 10 | [QM] (McCabe) |
| New bug-class static findings | 0 | [QM] |
| New type errors (mypy, `--check-untyped-defs`) | 0 | [QM] |
| Test strength: the run's own tests against mutants of the reference solution | ≥ 80%, joins the gate when built | [QM] |
| Mutation kill rate on the changed lines (M4) | Reported | [v1] [QM] |
| Maintainability index; code smells per 100 new lines | Reported, not gated | [QM] |

The tool gate is reported for every arm. It does not rank arms [QM].

### 4.3 Layer 3: design fit and the owner criteria

| Part | Measure | How | Role | Source |
|---|---|---|---|---|
| DRY | **Duplicated lines on new code** | `jscpd`, minimum block 5 lines | Gate: ≤ 3% | [OC] |
| SOLID: single responsibility, dependency inversion | **Module coupling**: efferent and afferent coupling and instability per module, from the import graph | An import-graph script per language | Reported, not gated | [OC] |
| SOLID: open for extension | **Edit radius** of the follow-up: the existing files that the follow-up changes, and their changed lines | From the follow-up diff against the frozen base | Ranks design | [OC] [FU] |
| Extensible | **Follow-up success and cost**: the follow-up's hidden checks, its dollars and its wall time | §4.5 | Ranks design | [OC] [FU] |
| Design checklist | Each item yes or no, with a file and line, by two blind reviewers | §6 | Ranks design | [QM] [OC] |
| Traceable | **Audit scores**: diagnosis accuracy, origin accuracy, audit cost, repair cost | §7 | Ranks after design | [OC] [PF] |

Design checklist items [QM] [OC]:

- The change follows the existing module boundaries.
- It adds nothing that the request did not ask for, or each addition is recorded as a decision.
- Names say what the code does; no dead code; no duplicated logic.
- Tests check behavior through the public interface and cover the failure paths that the request names.
- Each module has one reason to change (sources, transforms, sinks, orchestration and configuration are
  separate).
- Sources and sinks sit behind one interface each; adding one does not edit the others.
- Configuration, not code, holds what differs between pipelines where the request asks for it (P2).
- No logic is copied between the batch and the stream paths where one shared function fits.

v1's 1–10 rubric (M7) is replaced by layers 2 and 3. Pairwise judging (two or three LLM judges, each pair
twice with positions swapped) is a tie-breaker only, where the measures above tie [#16] [QM].

### 4.4 Reliability (pass^k)

A one-shot that passes once says nothing about the next run. Reliability is measured over repeated runs
[TC] [WP].

- **n per cell.** Each (task, arm) cell runs exactly **5 times** in the run set [v1] [PF]. The number is
  fixed before the run set and is not raised after results are seen [v1]. Calibration tries (§3.1) are
  not part of the run set.
- **pass^k.** For a cell with c passing runs out of n, pass^k = C(c, k) / C(n, k): the estimated chance
  that k fresh runs all pass [v2]. Report pass^1 and pass^5 per cell. A pass means M1 passes and M2 has no
  critical or major defect [v2].

### 4.5 Follow-up tasks

Each long task has a follow-up task [OC] [PF]. For the pipeline family it is a new data mart and a
dashboard [FU].

- The arm that built the base task gets the follow-up on its own delivered repository, in a new session,
  after the base task is graded [FU].
- The base result is frozen first, so the follow-up cannot change the base score [FU].
- The follow-up checks include every base check (no regression) and the edit radius [FU].

### 4.6 Cost (M9)

| Rule | Source |
|---|---|
| Input, output and cache tokens of the whole session, nested subagents and the harness's peers included, from the host's own accounting | [v1] [PRE] |
| Dollars from token counts at list prices in `pricing.json`, with the source and date of each price. The host's own dollar figure is not used for models that it does not price | [OC] [WP] |
| The session's tokens are split by model, so each model's tokens are priced at its own price | [PRE] |
| Cost of a long task is build + follow-up + repairs | [OC] |
| The decision rule uses **cost per defect-free delivered run**: dollars divided by the attempted runs that pass M1 with no critical or major M2 defect. An arm with no defect-free run has no finite value; that is reported as such | [v1] [DR] |
| Wall time is reported | [v1] |

### 4.7 Auditability (M10)

A checklist per run: a plan; a spec check; a plan review, an adversarial review and a PR review, each by
an agent other than the implementer; a findings ledger where each must-fix finding has a verification; a
closure record that names the delivered head; the deferral log (§2.5). Report the share of items present
[DR] [PF]. M10 is reported per framework. It is not scored against one-shot arms [v1].

### 4.8 Measures that v2 drops

| v1 measure | v2 | Source |
|---|---|---|
| M5 test-first evidence | Reported where the run commits; not a decision input | [v1] |
| M6 changed-line coverage | Folded into the tool gate (layer 2). It did not separate arms in v1 data or in iteration 4 | [v1] [QM] |
| M7 code quality rubric | Replaced by layers 2 and 3 | [#16] [QM] |

## 5. Running a trial

### 5.1 Full isolation

Every trial runs fully isolated from the owner's machine [PF] [#10]:

- The agent process, its tools, every virtual environment and package cache, the database and broker
  containers, and anything that the agent starts live in one disposable environment. That environment is
  deleted after grading [PF].
- Each trial gets its own container with its own Docker daemon inside (Docker-in-Docker or a sysbox
  runtime). A process that an agent leaves running dies with the container [PF].
- The host is a remote Linux machine (x86-64, at least 8 cores, 32 GB RAM), one trial per machine at a
  time [PF].
- Harbor runs the trials. The task images are built once and pinned by digest [PF].
- Nothing runs on the host but the orchestration that starts and collects trials [PF].

### 5.2 Clean-room gating

A run counts only if it saw and used nothing but its own arm's tools [CR]:

- Each run gets a clean `HOME` with only its arm's harness installed: no user-level skill, rule, command or
  memory [CR] [PRE].
- [`scripts/clean_room_check.py`](../scripts/clean_room_check.py) reads the run's transcripts, nested
  agents included. A run is graded only when the check returns `clean` [CR] [OD].
- A run with any other verdict (`exposed`, `contaminated`, `unassessable`) is not graded. It is recorded
  with its verdict as an infrastructure error, not as a failure, and it is run again [CR] [WP] [v2].
- The built-in skill list is pinned per Claude Code version [CR].

### 5.3 Caps and the run-set budget

| Rule | Source |
|---|---|
| **Harness arms have no per-trial time cap and no per-trial dollar cap. A harness run is never cut off** | [OD] [CAP] |
| Spend is controlled by **one budget for the whole run set**. Its value is recorded in this section before the first run. When the budget is spent, the run set stops scheduling new trials. It never stops a trial in progress | [CAP] |
| One-shot arms keep a generous time cap, only as a guard against a hung session. Its value is recorded in this section before the first run. A one-shot that hits it is reported separately, not mixed with other failures | [OD] |
| A trial lost to the infrastructure (for example the container runtime fails) is recorded as an infrastructure error, not as a failure, and is run again | [WP] |

Values, to be filled before the first v2 run set and then fixed:

- Run-set budget: **not yet recorded**.
- One-shot guard time cap: **not yet recorded**.

The v1 caps (1800 s timeout, $1.00 and $3.00 dollar caps) do not apply to v2 run sets. The code that
carries them (`cbench/harbor.py`, `scripts/live.sh`, `tests/test_criteria.py`) must change to the v2
caps before the first v2 run set [CAP] [v2].

## 6. Blind review protocol

- **Two independent reviewers per task.** Each sees every arm's final source and test files and its diff
  from the base commit, as anonymous folders. They do not see commit history, plans, review records,
  `.context/`, `.cursor/` or any process file. Framework names, ticket ids and process notes are removed
  from comments. The label map is stored outside the folders [v1].
- **Defects (M2).** A reviewer lists each defect with a repro command and its expected and observed output.
  A script re-runs every repro command in a clean copy of that arm's tree. A defect counts only if the
  script reproduces it. Reproduced defects from both reviewers are merged by root cause. When both list a
  defect, it takes the lower of their two severities [v1]. A reviewer may file a test-confirmed defect
  instead (§4.1) [QM].
- **Design checklist (layer 3).** Each reviewer answers each item yes or no, with a file and line as
  evidence [QM] [OC]. An item where the two reviewers differ goes to a third reviewer, and the majority
  stands [v2].
- The audit (§7) is separate from the blind review: the auditor sees the run record on purpose [PF].

## 7. Traceability: the audit protocol

For tasks with seeded ground truth (the pipeline family), each failed run is audited [PF]:

1. The grader first explains each failed check from the answer key, which stores the wrong answer that
   each single trap produces [PF].
2. A blind auditor gets only the run's record and the symptom. It does not get the trap id. The auditor
   is a fixed agent (the same model and prompt for every arm), with a human spot check on a sample [PF].
   - One-shot arms: the repository, the transcript and the arm's own summary.
   - Harness arms: the same, plus the harness artifacts (spec notes, plan, phase commits, reviews,
     decisions, deferral log).
3. The auditor answers: which cause; where it first went wrong; the cheapest fix point; how much of the
   delivered work must be redone [PF].
4. Scores: diagnosis accuracy, origin accuracy, audit cost (wall time and tokens), repair cost (an
   arm-matched repair agent fixes the run from the auditor's answer: its time, tokens, and whether the
   checks then pass) [PF].

## 8. Decision rule (pre-registered)

### 8.1 Units and interval

- **Units.** Every measure is per **attempted** run. A run that does not deliver (fails M1 or M8) counts as
  one critical defect for M2, and as one false success for M3 if it reports success. M3 is a per-run rate
  [v1].
- **Attempted run.** A graded run (§5.2). Runs set aside as infrastructure errors are not attempted runs
  [WP] [v2].
- **Interval.** For a difference between two arms, resample runs with replacement within each (task, arm)
  cell, 10,000 times, seed 20261010. Report the 5th and 95th percentiles (a 90% percentile interval).
  Tasks are not resampled, so a claim covers the tasks run [v1].
- **Claims per class.** A class claim needs at least **3 tasks** of that class. With fewer, the class
  result is "not enough tasks", and results are reported per task [v1].

### 8.2 Comparison A: the harness effect (same model)

Each harness arm H on Haiku 5.5 is compared with the Haiku one-shot on the same tasks [v1] [DR]. H is
**worth its cost** on a task class when all of these hold [v1]:

1. **Fewer defects:** mean critical + major M2 per attempted run is lower than the one-shot's by at least
   0.5, and the 90% interval of the difference is entirely above 0.
2. **No more false success:** H's M3 rate is not higher than the one-shot's, with a tolerance of 0.05.
3. **Delivery is not worse:** H's M1 pass rate per attempted run is at least the one-shot's minus 10
   points.
4. **Cost:** cost per defect-free delivered run is reported. It is not a pass/fail line. An arm that meets
   1–3 at more than 10× the cost per defect-free run is reported as "better, at a cost".

If 1–3 do not all hold, the result is "not shown".

### 8.3 Comparison B: matches the bar (lift tasks)

A harness arm H **matches the bar** on a lift class when all of these hold [DR]:

1. **Defects (non-inferiority):** H's mean critical + major M2 per attempted run is at most the Opus
   one-shot's plus a margin of **0.25**, and the 90% interval of the difference stays under that margin
   [DR]. When both arms have no defects the interval is [0, 0], which counts as "not worse"; the per-run
   counts are reported beside it [DR].
2. **No more false success:** H's M3 rate is not higher than the bar's, with a tolerance of 0.05 [DR].
3. **Delivery:** H's M1 pass rate per attempted run is at least the bar's minus 10 points [DR].
4. **Reliability:** H's pass^5 (§4.4) is reported beside the bar's and the Haiku one-shot's [TC] [v2].

### 8.4 Comparison C: beyond the bar (beyond tasks)

A harness arm H **goes beyond the bar** on a beyond class when all of these hold [TC] [v2]:

1. H's pass rate (§4.4) is higher than the bar's, and the 90% interval of the difference is entirely
   above 0.
2. Conditions 1 and 2 of §8.3 hold.

### 8.5 The answer: cheapest in the top design tier

Among the arms that match the bar (§8.3) or go beyond it (§8.4) [OC] [DR]:

1. Rank on design: duplication, the design checklist, edit radius and follow-up success (layer 3) [OC].
2. The **top design tier** is the best arm, plus each arm whose design measures are not worse than the
   best arm's beyond the noise of the run set (for each measure, the 90% interval of the difference with
   the best arm includes 0) [v2].
3. Within the top design tier, rank on traceability (§7) [OC].
4. **The answer is the cheapest arm in the top design tier**, by cost per defect-free delivered run
   (build + follow-up + repairs where the task has them). It is not the cheapest arm overall [OC].

The tool gate (layer 2) and auditability (M10) are reported beside the answer. They do not decide [QM]
[DR]. If no arm matches, the answer is "none yet", and the harness case rests on auditability and
enforcement [DR].

## 9. Disclosure

The owner of this benchmark also wrote one of the harnesses (Cadence) and supplied the private tasks and
the pipeline family. Because of that, the criteria, the task list (by hash) and the sample size are fixed
before any run set; results are published whichever way they fall; every reviewer in §6 is blind to the
arm; and results that do not favor Cadence are stated first [v1] [WP].

## 10. Evidence that shaped v2

- **Iteration 4** (T04–T06, n = 1 per cell): Opus 5.5 alone scored 8.00 against 7.33 for Cadence on Opus,
  in about 1/30 of the time. Cadence shipped no crash; each one-shot shipped two. Opus alone was the only
  arm to pass the tool gate on every task. Cadence runs took 54–68 minutes, so v1's 1800 s cap would have
  scored every one as not delivered [WP] [OD] [QM].
- **Pilot** (T05, n = 1 per arm): the Opus one-shot delivered in 111 s for $0.40. Cadence orchestrated by
  Haiku 5.5 delivered nothing: it stopped in its own planning loop or failed its own gates
  (jtouley/cadence#63–#66). A task that the bar finishes in 2 minutes cannot show what a harness is for
  [WP] [TS].
- **B01**, a private brownfield bug in a multi-service application: the Opus one-shot passed 10 of 10. The
  Haiku 5.5 and Sonnet 5.5 one-shots were not reliable (0 of 5 and 1 of 5 on the full grade). A review loop
  with an independent reviewer passed in 3 of 3 valid runs, at about the bar's cost. B01 is a lift task
  [TS] [WP]. A cheap one-shot dropped part of the request without reporting it; that gave the deferral
  review rule (§2.5) [PF].
- **Contamination incident:** processes left running by agents on the host shared state with later runs
  and the grader. All runs were regraded with an isolated grader and no grade changed. That gave the full
  isolation rule (§5.1) [WP] [#10].
- **SWE-bench Pro** (20 Python tasks): the Opus one-shot passed 17 on the first try; two tasks passed only
  2 of 5 tries. Beyond candidates, subject to §3.2 [WP].
- **Clean room** (iteration 4, checked after the fact): all 9 one-shot runs were `exposed` to
  user-installed skills, and the harness runs were not assessable. That gave clean-room gating (§5.2)
  [CR].

## 11. Open before the first v2 run set

These items must be filled or confirmed by the owner, with a changelog entry, before the first run:

1. The run-set budget and the one-shot guard time cap (§5.3) [CAP] [OD].
2. The non-inferiority margin of 0.25 (§8.3). It was proposed, not decided [DR].
3. Each [v2] operational definition: the lift and beyond thresholds (§3.2), the private-task hash (§3.4),
   pass^k (§4.4), the dropped-part-of-request defect (§2.5), non-clean runs as infrastructure errors
   (§5.2, §8.1), the third design reviewer (§6), the beyond rule (§8.4) and the top design tier (§8.5).
4. The code that pins v1 caps changes to v2 (§5.3).
5. Scripts for every measure that a run set reports (§4): test-confirmed defects, test strength,
   `jscpd` duplication, the import-graph coupling script, the edit radius, the audit scores [QM] [OC].

## Changelog from v1

| # | Change | Date | Decided in |
|---|---|---|---|
| 1 | The question adds the bar: the cheapest model that, inside a harness, matches or beats the Opus 5.5 one-shot (§1) | 2026-10-12 | [next steps: owner decisions](next-steps.md#owner-decisions-for-this-design-2026-10-12) |
| 2 | No per-trial time or dollar cap for harness arms; one budget for the run set; one-shots keep a guard time cap, reported separately (§5.3). Replaces v1 §6 "Caps" | 2026-10-12 | [next steps: decision rule, Caps](next-steps.md#decision-rule-for-this-question) |
| 3 | Clean-room gating: a clean `HOME` per run, and grading only when `clean_room_check.py` returns `clean` (§5.2) | 2026-10-12 | [process: clean room](process.md#clean-room), [next steps: owner decisions](next-steps.md#owner-decisions-for-this-design-2026-10-12) |
| 4 | Task admission by calibration against the bar (§3.1) | 2026-10-13 | [next steps: task selection](next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13) |
| 5 | Claims by lift and beyond classes; v1 classes S, L and O stay as descriptions; T04–T06 only for contrast (§3.2, §3.3) | 2026-10-14 | [next steps: two task classes](next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13) |
| 6 | Task sources: private brownfield tasks (scores published, code not), review-caught defects, a published hard set, the pipeline family (§3.3) | 2026-10-13 | [next steps: task selection](next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13), [pipeline family](tasks/pipeline-family.md) |
| 7 | Reliability over repeats: pass^k per cell, n = 5 per cell (§4.4) | 2026-10-14 | [next steps: two task classes](next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13), [whitepaper](whitepaper.md) |
| 8 | The quality model is the quality measure: three layers, a tool gate with published thresholds, a design checklist; v1's M7 rubric is replaced, M6 folds into the tool gate (§4) | 2026-10-13 | [harness-benchmark#16](https://github.com/jtouley/harness-benchmark/issues/16), [quality model](quality-model.md) |
| 9 | Owner success criteria: DRY (duplication ≤ 3%), SOLID (coupling, checklist, edit radius), extensible (follow-up success and cost), traceable (audit scores), cheapest in the top design tier (§4.3, §8.5) | 2026-10-14 | [quality model: owner criteria](quality-model.md#owner-criteria-2026-10-14-dry-solid-extensible-traceable-cheap), [pipeline family](tasks/pipeline-family.md#success-criteria-owner-2026-10-14) |
| 10 | Haiku-only harness arms, reviews included; the Opus one-shot is the bar; Haiku and Sonnet one-shots; named comparison arms only where named (§2.1, §2.2). The 2026-10-12 Cursor, OpenAI, Haiku 4.5 and Opus-review arms are not in the v2 run set | 2026-10-14 | [pipeline family: arms](tasks/pipeline-family.md#arms), [next steps: owner decisions](next-steps.md#owner-decisions-for-this-design-2026-10-12) |
| 11 | Follow-up tasks on the arm's own frozen code (§4.5) | 2026-10-14 | [follow-up task](tasks/pipeline-followup.md) |
| 12 | Prompt hygiene: five rules beside the neutral baseline (§2.4) | 2026-10-14 | [pipeline family: prompt hygiene](tasks/pipeline-family.md#prompt-hygiene) |
| 13 | Deferral review in real time by an independent Haiku reviewer (§2.5) | 2026-10-14 | [pipeline family: arms](tasks/pipeline-family.md#arms) |
| 14 | Full isolation of every trial in its own container, on a remote host (§5.1) | 2026-10-14 | [pipeline family: runner and isolation](tasks/pipeline-family.md#runner-and-isolation), [harness-benchmark#10](https://github.com/jtouley/harness-benchmark/issues/10) |
| 15 | Traceability audit protocol (§7) | 2026-10-14 | [pipeline family: audit protocol](tasks/pipeline-family.md#audit-protocol) |
| 16 | Cost from token counts at `pricing.json` list prices, split by model; long-task cost is build + follow-up + repairs (§4.6) | 2026-10-12, 2026-10-14 | [next steps: prerequisites](next-steps.md#prerequisites-stage-0), [quality model: owner criteria](quality-model.md#owner-criteria-2026-10-14-dry-solid-extensible-traceable-cheap) |
| 17 | M10 auditability as a checklist share per run, with the deferral log (§4.7) | 2026-10-12, 2026-10-14 | [next steps: measures](next-steps.md#measures), [pipeline family: arms](tasks/pipeline-family.md#arms) |
| 18 | Decision rule restated: comparison A (v1 rule, same model), comparison B (non-inferiority to the bar, margin 0.25), comparison C (beyond the bar), and the answer as the cheapest arm in the top design tier (§8) | 2026-10-12, 2026-10-14 | [next steps: decision rule](next-steps.md#decision-rule-for-this-question), [quality model: owner criteria](quality-model.md#owner-criteria-2026-10-14-dry-solid-extensible-traceable-cheap) |
| 19 | Operational definitions that v2 adds, each marked [v2] and listed in §11 for owner confirmation | 2026-10-14 | this document |

## Changelog

- v2 (2026-10-14): this version. Changes from v1 in the table above.
- v1 (2026-10-10): first version ([criteria v1](criteria.md)).
