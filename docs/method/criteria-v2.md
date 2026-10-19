# Benchmark criteria (v2)

Status: **draft**. It becomes pre-registered for the next run set when every item in §11 is closed.
Once pre-registered, these criteria are fixed before the outcome runs that they judge. A change to them is a new version with a changelog entry. Results are reported against the
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
| [OD] | [next steps: owner decisions](../plans/next-steps.md#owner-decisions-for-this-design-2026-10-12) | 2026-10-12 |
| [CAP] | [next steps: decision rule, "Caps (owner decision)"](../plans/next-steps.md#decision-rule-for-this-question) | 2026-10-12 |
| [DR] | [next steps: decision rule for this question](../plans/next-steps.md#decision-rule-for-this-question) | 2026-10-12 |
| [PRE] | [next steps: prerequisites](../plans/next-steps.md#prerequisites-stage-0) | 2026-10-12 |
| [TS] | [next steps: task selection, calibrated against the bar](../plans/next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13) | 2026-10-13 |
| [TC] | [next steps: two task classes (revised)](../plans/next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13) | 2026-10-14 |
| [CR] | [process: clean room](process.md#clean-room) | 2026-10-12 |
| [#16] | [harness-benchmark#16](https://github.com/jtouley/harness-benchmark/issues/16): adopt the quality model as criteria v2 | 2026-10-13 |
| [QM] | [quality model](quality-model.md) (adopted by [#16]) | 2026-10-13 |
| [#41] | [harness-benchmark#41](https://github.com/jtouley/harness-benchmark/issues/41): grading by code; a reviewer only proposes tests that code confirms | 2026-10-19 |
| [OC] | [quality model: owner criteria](quality-model.md#owner-criteria-2026-10-14-dry-solid-extensible-traceable-cheap) | 2026-10-14 |
| [PF] | [pipeline family](../plans/tasks/pipeline-family.md): success criteria, arms, deferral review, prompt hygiene, isolation, audit protocol | 2026-10-14 |
| [FU] | [follow-up task](../plans/tasks/pipeline-followup.md) | 2026-10-14 |
| [WP] | [whitepaper](../whitepaper.md) | 2026-10-14 |
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
| Cadence, all Haiku | Haiku 5.5 | Full Cadence with `peer_models: {"default": "haiku"}`, after jtouley/cadence#63–#66 and jtouley/cadence#68 (deferral review, §2.5) are fixed | Harness arm | [PF] [v2] |

**Haiku-only harness arms.** Every harness arm runs on Haiku 5.5, reviews included, unless the arm says
otherwise. A harness may spend many tokens if each token is cheap [PF] [OD]. No arm in the run set runs Opus 5.5 or
Sonnet 5.5 inside a harness, except the §2.2 review-loop comparison arm [v2]. Opus never orchestrates a Cadence
run [OD].

### 2.2 Named comparison arms

These arms are run only where named. They are reported for context and are not part of the decision rule.

| Arm | Where | Why | Source |
|---|---|---|---|
| Review loop with a Sonnet 5.5 or Opus 5.5 reviewer (Haiku 5.5 or Sonnet 5.5 works) | B01 only | Shows what a stronger reviewer adds, per dollar | [PF] [TS] |
| Haiku one-shot and Sonnet one-shot on calibration tries | Every candidate task | Classify a task as lift or beyond (§3) | [TC] [PF] |

The 2026-10-12 design also named Cadence with Opus reviews, Haiku 4.5, Cursor CLI and OpenAI arms [OD].
The 2026-10-14 arm list [PF] does not include them, so they are **not** in the v2 run set. A later
version can add them with a changelog entry [v2].

Sonnet 5.5 runs no Cadence arm [OD]. Sonnet 5.5 and Opus 5.5 work or review inside a harness only in the
§2.2 review-loop arm, which is a minimal harness, not Cadence [OD] [v2]. Each harness arm has a one-shot
arm on the same model [v1].

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
- A part of the request that a run drops shows as a failing acceptance or edge check (M1, M2). The
  deferral log is evidence for the audit (§4.7, §7), not a grade [WP] [v2].

This rule comes from B01, where a cheap one-shot diagnosed a second defect, decided to leave it out, and
then reported nothing [PF] [WP]. Cadence does not do this yet (jtouley/cadence#68) [PF].

**Who provides the deferral reviewer** (proposed, owner to confirm in §11) [v2]: the deferral review is a
harness requirement. Each harness arm provides it in its own installed harness. The benchmark does not
inject a reviewer, so §2.4 rule 2 holds. The Cadence arm is therefore admitted only after
jtouley/cadence#68 is fixed, as well as #63–#66 (§2.1).

## 3. Tasks and task classes

### 3.1 Calibration

A task is "hard" only when the bar fails it, not when it looks hard [TS]. Every candidate task gets
calibration tries before it is admitted [TS]:

- **Try count.** Each calibration arm gets exactly **5 tries** per task, the same n as a run-set cell
  (§4.4) and as the pipeline family (§3.3). The count is fixed before calibration and is not raised after
  results are seen [PF] [v2]. (Proposed, owner to confirm in §11: the source [TS] names three tries.)

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

Both thresholds are over the 5 calibration tries of §3.1.

- **Beyond:** the Opus one-shot passes at most **2 of 5** calibration tries [TS] [v2].
- **Lift:** the Opus one-shot passes **5 of 5** calibration tries, and at least one cheap one-shot arm fails
  1 or more of its 5 calibration tries [v2].
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

Each measure is computed by a script in this repository on the state that the run leaves [v1]. **No
measure is decided by a model's or a person's judgment**: no judge or rubric score enters a measure, a
ranking or a tie-break. A model may act only as a reviewer kept in line, proposing tests that code then
confirms (§6) [#41]. Claims in an agent's own summary are never evidence for a measure
[v1]. A measure that has no script at the start of a run set is not reported for that run set [v1].

The quality measure is the [quality model](quality-model.md), in three layers [#16] [QM]. No layer
replaces another, and there is no single blended score: each arm gets one table with the layers side by
side [QM].

### 4.1 Layer 1: it does what the request says

| # | Measure | How it is computed | Role | Source |
|---|---|---|---|---|
| M1 | **Acceptance** | The hidden checks (or the oracle) on the delivered working tree, in the running system where the task has one | Gate: a run that fails M1 is not delivered | [v1] [TS] |
| M1f | **Hidden-suite pass fraction** | The fraction of the hidden checks that pass (30 or more per task where the task has a suite) | Reported | [QM] |
| M2 | **Detected defects** | Found by code (§6): each failing check of the task's edge suite; each crash (an uncaught exception or a non-zero exit with a traceback) on the task's fixed probe inputs; in a follow-up, each base check that no longer passes; and each failing reviewer-proposed test that code has confirmed. Severity comes from labels committed with the task before the run set, or by rule for reviewer-proposed tests (§6): critical (data loss, a wrong result reported as success), major (a crash, a sentence of the request not met), minor. Failures with the same check id count once | **Primary.** Only critical and major defects count in the decision rule (§8); minor ones are reported | [v1] [QM] [DR] [#41] |
| M3 | **False success** | A run that ends as completed (no recorded stop, no question to the user) while M1 fails or M2 has a critical or major defect. A harness that stops with a recorded reason is not a false success | Decision rule input (§8.2–§8.4), beside M2 | [v1] [DR] [#41] |
| M8 | **Completion** | Finished without a human answer. A hard stop or a question to the user counts as not complete | Reported | [v1] |

### 4.2 Layer 2: the tool gate

Computed by [`scripts/quality_metrics.py`](../../scripts/quality_metrics.py), with the tools pinned in the
lockfile. A lint or type finding counts only on a line that the change added. For both complexity measures,
one rule applies: a function is flagged when the change takes it over the threshold, that is, it is new and
over the threshold, or it was at or under the threshold in the baseline and is over it now (output keys
`cognitive_newly_over_15` and `cyclomatic_newly_over_10`). A tool that fails leaves its measure
unmeasured, and the gate then fails [QM].

| Measure | Threshold | Gate key in `quality_metrics.py` | Source |
|---|---|---|---|
| The run's own tests pass | All pass, and at least one runs | `tests_pass` | [QM] |
| New-code line coverage | ≥ 80% | `new_code_coverage_at_least_80` | [QM] (Sonar way gate) |
| Line and branch coverage of the whole package | Reported, not gated | none | [QM] |
| Functions that the change takes over cognitive complexity 15 | 0 | `no_function_newly_over_cognitive_15` | [QM] (SonarSource) |
| Functions that the change takes over cyclomatic complexity 10 | 0 | `no_function_newly_over_cyclomatic_10` | [QM] (McCabe) |
| New bug-class static findings | 0 | `no_new_bug_findings` | [QM] |
| New type errors (mypy, `--check-untyped-defs`) | 0 | `no_new_type_errors` | [QM] |
| Duplicated lines on new code (`jscpd`, §4.3) | ≤ 3% | `new_code_duplication_at_most_3` | [QM] (Sonar way gate) |
| Test strength: the run's own tests against mutants of the reference solution | ≥ 80%, joins the gate when built | none yet | [QM] |
| Mutation kill rate on the changed lines (M4) | Reported | none | [v1] [QM] |
| Maintainability index; code smells per 100 new lines | Reported, not gated | none | [QM] |

The tool gate is reported for every arm. It does not rank arms [QM].

### 4.3 Layer 3: design fit and the owner criteria

| Part | Measure | How | Role | Source |
|---|---|---|---|---|
| DRY | **Duplicated lines on new code** | `jscpd`, minimum block 5 lines (`new_code_duplication` in `quality_metrics.py`) | Both a layer-2 gate condition (≤ 3%, §4.2) and a layer-3 ranking measure (§8.5). Whether an arm over 3% leaves the top design tier or only ranks lower (§8.5) is open (§11) | [OC] [QM] |
| SOLID: single responsibility, dependency inversion | **Module coupling**: efferent and afferent coupling and instability per module, from the import graph | An import-graph reader per language (`module_coupling` in `quality_metrics.py`; Python is built) | Reported, not gated | [OC] |
| SOLID: open for extension | **Edit radius** of the follow-up: the existing files that the follow-up changes, and their changed lines | From the follow-up diff against the frozen base (`edit_radius.package` in `quality_metrics.py`) | Ranks design | [OC] [FU] |
| Extensible | **Follow-up success and cost**: the follow-up's hidden checks, its dollars and its wall time | §4.5 | Ranks design | [OC] [FU] |
| Traceable | **Audit scores**: diagnosis accuracy, origin accuracy, audit cost, repair cost | §7 | Ranks after design | [OC] [PF] |

v1's 1–10 rubric (M7), the design checklist and pairwise judging are not used: each is a model's or a
person's opinion of code that no test can confirm. Two arms that tie on every measure above stay tied [#41].

### 4.4 Reliability (pass^k)

A one-shot that passes once says nothing about the next run. Reliability is measured over repeated runs
[TC] [WP].

- **n per cell.** Each (task, arm) cell runs exactly **5 times** in the run set [v1] [PF]. The number is
  fixed before the run set and is not raised after results are seen [v1]. Calibration tries (§3.1) are
  not part of the run set.
- **pass^k.** For a cell with c passing runs out of n, pass^k = C(c, k) / C(n, k): the estimated chance
  that k fresh runs all pass [v2]. Report pass^1 and pass^5 per cell. A pass means M1 passes and M2 has no
  test-confirmed critical or major defect [v2].
- **What pass^k does.** pass^k selects tasks (§3.2) and describes each cell. It does not decide whether an
  arm matches the bar: that is the decision rule (§8.3), on M1 delivery and M2 defects. pass^k is reported
  beside it [TC]. pass^1 is the pass rate that decides "beyond the bar" (§8.4) [v2].

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
| M7 code quality rubric | Dropped: no model or reviewer score is reported (§4) | [#16] [#41] |
| Blind review (v1 §5) | Replaced: frozen checks, and a reviewer that may only propose tests, which code confirms (§6) | [#41] |

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
- [`scripts/clean_room_check.py`](../../scripts/clean_room_check.py) reads the run's transcripts, nested
  agents included. A run is graded only when the check returns `clean` [CR] [OD].
- The other verdicts are split by their cause (proposed, owner to confirm in §11) [CR] [v2]:
  - **Setup faults** are infrastructure errors: `exposed` and `unassessable`. The run is not graded and
    not counted as a failure. It is run again, at most **2 reruns per cell** in the run set.
    Infrastructure losses under §5.3 (for example a container-runtime failure) share the same 2 reruns. A
    cell that has used its 2 reruns and still has **fewer than 5 graded runs** is reported as
    **"unassessable"**, and that cell is short of n = 5 (§8.1) [WP] [v2].
  - **Every `contaminated` verdict** counts against the arm: it is an **attempted run that is not
    delivered** (§8.1). It is not run again. It is also tallied separately per arm. There is no
    exception for instruction files that the host loads, because the check does not report them apart
    from the agent's own contacts; stage 0 allowlists them instead [v2].
- **Stage-0 smoke run.** Before the run set, stage 0 adds **each arm's host-loaded instruction paths**
  (the CLAUDE.md and AGENTS.md files, and memory files if any, that the host loads for that arm's setup) to its
  `--allow-path`. Each arm then runs one smoke run in the Harbor container, with its allowlists
  (`--allow`, `--allow-path`) as they will be used in the run set. The arm is admitted only when that run
  gets a **`clean` verdict**. The clean smoke run checks that the allowlists cover the setup, and a later
  `contaminated` verdict is treated as coming from the agent. It also catches a missing skill listing and an allowlist
  that leaves out the harness's own skills or paths [CR] [v2].
- The built-in skill list is pinned per Claude Code version [CR].

### 5.3 Caps and the run-set budget

| Rule | Source |
|---|---|
| **Harness arms have no per-trial time cap and no per-trial dollar cap. A harness run is never cut off** | [OD] [CAP] |
| Spend is controlled by **one budget for the whole run set**. Its value is recorded in this section before the first run. When the budget is spent, the run set stops scheduling new trials. It never stops a trial in progress | [CAP] |
| **Round-robin scheduling.** Run k of every cell starts before run k+1 of any cell, so a budget stop leaves every arm short by at most one run per cell, whatever its cost | [v2] |
| One-shot arms keep a generous time cap, only as a guard against a hung session. Its value is recorded in this section before the first run. A one-shot that hits it is an **attempted run that is not delivered** (§8.1). It is also reported separately, not mixed with other failures | [OD] [v2] |
| A trial lost to the infrastructure (for example the container runtime fails) is recorded as an infrastructure error, not as a failure, and is run again. It shares the cell's 2 reruns of §5.2 | [WP] [v2] |

Values, to be filled before the first v2 run set and then fixed:

- Run-set budget: **not yet recorded**.
- One-shot guard time cap: **not yet recorded**.

The v1 caps (1800 s timeout, $1.00 and $3.00 dollar caps) do not apply to v2 run sets. The code that
carries them (`cbench/harbor.py`, `scripts/live.sh`, `tests/test_criteria.py`) must change to the v2
caps before the first v2 run set [CAP] [v2].

## 6. Defect checks

Defects (M2) come from code. A model may help find them only as a reviewer kept in line: it proposes
tests, and code decides whether each one counts. No model or person decides by judgment what counts
[#41].

**Frozen checks**, written before the run set:

- **Edge suite.** Each task has hidden checks beyond its acceptance check: the edge cases, error paths and
  inputs that the request covers. Each edge check passes on the reference solution, fails on at least one
  wrong variant of it (a mutant or a known-wrong solution, committed with the task), and fails on the
  untouched starting state where the behavior is new [v1] [#41].
- **Probe inputs.** Each task has a fixed list of inputs, generated from a recorded seed, that a run's
  program must handle without crashing [#41].
- **Severity labels** are part of each check's definition, committed with the task [#41].
- The edge suites, probe inputs and labels are part of the frozen task list: their sha256 is recorded
  with the run set (§3.4). A check added after the first run starts a new run set [v1] [#41].

**Reviewer-proposed checks**, after the runs, to find defects that no frozen check anticipated [#41]:

- **A fixed instrument.** One reviewer model, prompt and token budget for every arm, recorded with the run
  set before the first run. It sees each arm's final source, tests and diff as anonymous folders, as v1's
  blind review did, and no process files [v1] [#41].
- **Tests only.** Its only output is executable reproduction tests. Prose, verdicts and scores are not
  read [#41].
- **Code confirms each test.** A proposed test is kept only when it passes on the reference solution and
  fails on the code of the arm it was written for. Every kept test then runs against every arm's code,
  so an arm is never penalized because the reviewer looked at it longer [#41].
- **Severity by rule.** A failing kept test is a major defect; it is critical when the run also ended as
  completed (M3). The reviewer's own words about severity are not used [#41].
- Kept tests are committed with the run set's results, and their defects are reported in a column of
  their own beside the frozen-check defects; both count in M2 [#41].

The limit is stated with every result: a defect that neither a frozen check nor a kept test catches is not
counted [#41].

## 7. Traceability: the audit protocol

For tasks with seeded ground truth (the pipeline family), each failed run is audited [PF]:

1. The grader first explains each failed check from the answer key, which stores the wrong answer that
   each single trap produces [PF].
2. A blind auditor gets only the run's record and the symptom. It does not get the trap id. The auditor
   is a fixed agent (the same model and prompt for every arm). It is the instrument being measured with,
   not a grader: a script scores its answers against the answer key, and no person or model scores
   them [PF] [#41].
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
- **Attempted run.** A graded run (§5.2), a `contaminated` run (§5.2) and a one-shot run that hits the
  guard time cap (§5.3). A `contaminated` run and a guard-cap run are attempted runs that are not
  delivered; each is also tallied separately. Runs set aside as infrastructure errors (§5.2, §5.3) are
  not attempted runs [WP] [v2].
- **Interval.** For a difference between two arms, resample runs with replacement within each (task, arm)
  cell, 10,000 times, seed 20261010. Report the 5th and 95th percentiles (a 90% percentile interval).
  Tasks are not resampled, so a claim covers the tasks run [v1].
- **Direction of each difference.** The order of the subtraction is fixed per comparison [v1] [v2]:
  - Comparison A (§8.2), defects: **mean(Haiku one-shot) − mean(H)**, as in v1. A positive value
    favors H.
  - Comparison B (§8.3), defects: **mean(H) − mean(bar)**. A positive value means H has more defects
    than the bar; the margin applies to this value.
  - Comparison C (§8.4), pass rate: **pass rate(H) − pass rate(bar)**. A positive value favors H.
- **Claims per class.** A class claim needs at least **3 tasks** of that class. With fewer, the class
  result is "not enough tasks", and results are reported per task [v1].
- **Complete cells.** A claim for a harness arm H on a class also needs H's cells and its comparator's
  cells of that class (the Haiku one-shot for comparison A, the bar for comparisons B and C) at n = 5
  attempted runs. If one of those cells is short (the budget ran out, §5.3, or the cell is
  "unassessable", §5.2), H's result for that comparison is **"incomplete"**, and the per-cell results are
  reported. A short cell of another arm does not block H's claim. §8.5 says how the answer treats an arm
  whose result is "incomplete" [v2].

### 8.2 Comparison A: the harness effect (same model)

Each harness arm H on Haiku 5.5 is compared with the Haiku one-shot on the same tasks [v1] [DR]. H is
**worth its cost** on a task class when all of these hold [v1]:

1. **Fewer defects:** mean critical + major M2 per attempted run is lower than the one-shot's by at least
   0.5, and the 90% interval of mean(Haiku one-shot) − mean(H) is entirely above 0.
2. **No more false success:** H's M3 rate is not higher than the one-shot's, with a tolerance of 0.05.
3. **Delivery is not worse:** H's M1 pass rate per attempted run is at least the one-shot's minus 10
   points.
4. **Cost:** cost per defect-free delivered run is reported. It is not a pass/fail line. An arm that meets
   1–3 at more than 10× the cost per defect-free run is reported as "better, at a cost".

If 1–3 do not all hold, the result is "not shown".

### 8.3 Comparison B: matches the bar (lift tasks)

A harness arm H **matches the bar** on a lift class when all of these hold [DR]:

1. **Defects (non-inferiority):** H's mean critical + major M2 per attempted run is at most the Opus
   one-shot's plus a margin of **0.25**, and the 90% interval of mean(H) − mean(bar) stays under that
   margin (its 95th percentile is below 0.25) [DR] [v2]. When both arms have no defects the interval is [0, 0], which counts as "not worse"; the per-run
   counts are reported beside it [DR].
2. **No more false success:** H's M3 rate is not higher than the bar's, with a tolerance of 0.05 [DR].
3. **Delivery:** H's M1 pass rate per attempted run is at least the bar's minus 10 points [DR].
4. **Reliability:** H's pass^5 (§4.4) is reported beside the bar's and the Haiku one-shot's [TC] [v2].

### 8.4 Comparison C: beyond the bar (beyond tasks)

A harness arm H **goes beyond the bar** on a beyond class when all of these hold [TC] [v2]:

1. H's pass rate (pass^1, §4.4) is higher than the bar's, and the 90% interval of
   pass rate(H) − pass rate(bar) is entirely above 0.
2. Conditions 1 and 2 of §8.3 hold.

### 8.5 The answer: cheapest in the top design tier

The answer is computed **per class**: arms that match the bar on the lift class and arms that go beyond
it on the beyond class are not pooled [v2]. Within a class, among the arms that match the bar (§8.3) or
go beyond it (§8.4) [OC] [DR]:

1. The design measures (layer 3) are taken in this **order**: follow-up success (higher is better), then
   edit radius (smaller is better), then duplicated lines on new code (lower is better). Two arms **tie** on a measure when the
   90% interval of their difference includes 0. A measure that the class's tasks do not have is skipped
   (proposed, owner to confirm in §11) [OC] [v2].
2. The **best arm** is chosen **step by step against the current leader**, not by sorting arms pair by
   pair (a tie is not transitive, so a pairwise sort can cycle). Start with every arm in the class. On
   each measure in order, the **leader** is the kept arm with the best point estimate; keep the leader
   and every kept arm that ties with the leader, and drop the others. When one arm is left, it is the
   best arm. If more than one is left after the last measure, the best arm is the leader of the last
   measure. Equal point estimates are broken by the next measure, then by the lower cost per
   defect-free delivered run (proposed, owner to confirm in §11) [v2].
3. The **top design tier** is the best arm, plus each arm
   that is not worse than the best arm beyond the noise of the run set on any measure. The test is
   **one-sided**: for each measure, take the 90% interval of (arm − best arm), oriented so that a positive
   value is worse for that measure; the arm stays in the tier when the **5th percentile of that interval
   is ≤ 0** for every measure. An arm that is better than the best arm on a later measure is never
   removed for it (proposed, owner to confirm in §11) [v2].
4. Within the top design tier, rank on traceability (§7) [OC].
5. **The answer is the cheapest arm in the top design tier**, by cost per defect-free delivered run
   (build + follow-up + repairs where the task has them). It is not the cheapest arm overall [OC].

An arm whose comparison B or C result is "incomplete" (§8.1) is not in the steps above. It is listed
beside the answer as "incomplete". If it could still change the answer, the answer is "incomplete"
(proposed, owner to confirm in §11) [v2].

The tool gate (layer 2) and auditability (M10) are reported beside the answer. They do not decide [QM]
[DR]. If no arm matches, the answer is "none yet", and the harness case rests on auditability and
enforcement [DR].

## 9. Disclosure

The owner of this benchmark also wrote one of the harnesses (Cadence) and supplied the private tasks and
the pipeline family. Because of that, the criteria, the task list (by hash) and the sample size are fixed
before any run set, with every defect check (§6); results are published whichever way they fall; no
measure is decided by a model's or a person's judgment, and the one reviewer (§6) can only propose
tests that code confirms and that run against every arm; and results that do not favor
Cadence are stated first [v1] [WP] [#41].

## 10. Evidence that shaped v2

- **Iteration 4** (T04–T06, n = 1 per cell): Opus 5.5 alone scored 8.00 against 7.33 for Cadence on Opus,
  in about 1/30 of the time. Cadence shipped no crash; each one-shot shipped two (all six on one task, budgets, from three inputs). Opus alone was the only
  arm to pass the tool gate on every task. Cadence runs took 54–68 minutes, so v1's 1800 s cap would have
  scored every one as not delivered [WP] [OD] [QM].
- **Pilot** (T05, n = 1 per arm): the Opus one-shot delivered in 111 s for $0.40. Cadence orchestrated by
  Haiku 5.5 delivered nothing: it stopped in its own planning loop or failed its own gates
  (jtouley/cadence#63–#66). A task that the bar finishes in 2 minutes cannot show what a harness is for
  [WP] [TS].
- **B01**, a private brownfield bug in a multi-service application: the Opus one-shot passed 10 of 10. The
  Haiku 5.5 and Sonnet 5.5 one-shots were not reliable (0 of 5 and 1 of 5 on the full grade). A review loop
  with an independent **Opus 5.5** reviewer (2 Haiku 5.5 runs, 1 Sonnet 5.5 run) passed in 3 of 3 valid
  runs, at about the bar's cost. These are interim, private runs. The v2 review-loop arm uses a Haiku 5.5
  reviewer, which these runs did not test. B01 is a lift task [TS] [WP]. A cheap one-shot dropped part of the request without reporting it; that gave the deferral
  review rule (§2.5) [PF].
- **Contamination incident:** processes left running by agents on the host shared state with later runs
  and the grader. All runs were regraded with an isolated grader and no grade changed. That gave the full
  isolation rule (§5.1) [WP] [#10].
- **SWE-bench Pro** (20 Python tasks): the Opus one-shot passed 17 on the first try; two tasks passed only
  2 of 5 tries. Under §3.2 (at most 2 of 5) they are beyond candidates, once they are calibrated in a
  clean, isolated environment (§3.1) [WP] [v2].
- **Clean room** (iteration 4, checked after the fact): all 9 one-shot runs were `exposed` to
  user-installed skills, and the harness runs were not assessable. That gave clean-room gating (§5.2)
  [CR].

## 11. Open before the first v2 run set

These items must be filled or confirmed by the owner, with a changelog entry, before the first run:

1. The run-set budget and the one-shot guard time cap (§5.3) [CAP] [OD].
2. The non-inferiority margin of 0.25 (§8.3). It was proposed, not decided [DR].
3. **Proposed, owner to confirm** (from the PR #20 review):
   1. The calibration try count of 5 per arm and per task (§3.1), and the beyond threshold of at most 2 of
      5 (§3.2). The source [TS] names three tries.
   2. The split of non-clean verdicts: setup faults (`exposed`, `unassessable`) are infrastructure errors
      with at most 2 reruns per cell, shared with §5.3 infrastructure losses, then the cell is
      "unassessable"; every `contaminated` verdict is an attempted run that is not delivered (§5.2,
      §8.1). Also the stage-0 smoke run: each arm's host-loaded instruction paths go into its
      `--allow-path`, and the smoke run must get a `clean` verdict for each arm (§5.2).
   3. The budget stop: round-robin scheduling, and a result of "incomplete" when the arm's or its
      comparator's cell is short of n = 5 (§5.3, §8.1).
   4. A one-shot that hits the guard time cap is an attempted run that is not delivered, also tallied
      separately (§5.3, §8.1).
   5. The deferral reviewer is a harness requirement, not benchmark infrastructure, so the Cadence arm is
      also gated on jtouley/cadence#68 (§2.1, §2.5).
   6. The direction of each difference (§8.1).
   7. The top design tier: per class, with the measure order follow-up success, edit radius,
      duplication; a tie is a 90% interval that includes 0; the best arm is chosen step by step
      against the current leader; the tier test is one-sided, in each measure's worse direction; an arm
      with an "incomplete" result is listed beside the answer, and the answer is "incomplete" if that
      arm could still change it (§8.5).
4. **Open, no proposal yet:** whether an arm over the 3% duplication gate leaves the top design tier or
   only ranks lower (§4.3, §8.5).
5. Each other [v2] operational definition: the lift threshold (§3.2), the private-task hash (§3.4),
   pass^k (§4.4), the beyond rule (§8.4) and the scope of the §2.1 model rule (§2.1).
6. The code that pins v1 caps changes to v2 (§5.3).
7. Scripts for every measure that a run set reports (§4) and that is not built yet: test-confirmed
   defects (the edge suites, probe inputs and severity labels of each task, and the reviewer's model,
   prompt and budget, §6), test strength, an
   import-graph reader for each non-Python stack in the run set, the audit
   scores [QM] [OC]. (Duplication, Python coupling and the edit radius are built in
   `scripts/quality_metrics.py`.)

## Changelog from v1

| # | Change | Date | Decided in |
|---|---|---|---|
| 1 | The question adds the bar: the cheapest model that, inside a harness, matches or beats the Opus 5.5 one-shot (§1) | 2026-10-12 | [next steps: owner decisions](../plans/next-steps.md#owner-decisions-for-this-design-2026-10-12) |
| 2 | No per-trial time or dollar cap for harness arms; one budget for the run set; one-shots keep a guard time cap, reported separately (§5.3). Replaces v1 §6 "Caps" | 2026-10-12 | [next steps: decision rule, Caps](../plans/next-steps.md#decision-rule-for-this-question) |
| 3 | Clean-room gating: a clean `HOME` per run, and grading only when `clean_room_check.py` returns `clean` (§5.2) | 2026-10-12 | [process: clean room](process.md#clean-room), [next steps: owner decisions](../plans/next-steps.md#owner-decisions-for-this-design-2026-10-12) |
| 4 | Task admission by calibration against the bar (§3.1) | 2026-10-13 | [next steps: task selection](../plans/next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13) |
| 5 | Claims by lift and beyond classes; v1 classes S, L and O stay as descriptions; T04–T06 only for contrast (§3.2, §3.3) | 2026-10-14 | [next steps: two task classes](../plans/next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13) |
| 6 | Task sources: private brownfield tasks (scores published, code not), review-caught defects, a published hard set, the pipeline family (§3.3) | 2026-10-13 | [next steps: task selection](../plans/next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13), [pipeline family](../plans/tasks/pipeline-family.md) |
| 7 | Reliability over repeats: pass^k per cell, n = 5 per cell (§4.4) | 2026-10-14 | [next steps: two task classes](../plans/next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13), [whitepaper](../whitepaper.md) |
| 8 | The quality model is the quality measure: three layers, a tool gate with published thresholds, a design checklist; M2 (test-confirmed, critical or major) is the primary measure; v1's M7 rubric is replaced and kept only for comparison, M6 folds into the tool gate (§4) | 2026-10-13 | [harness-benchmark#16](https://github.com/jtouley/harness-benchmark/issues/16), [quality model](quality-model.md), [next steps: measures](../plans/next-steps.md#measures) |
| 9 | Owner success criteria: DRY (duplication ≤ 3%), SOLID (coupling, checklist, edit radius), extensible (follow-up success and cost), traceable (audit scores), cheapest in the top design tier (§4.3, §8.5) | 2026-10-14 | [quality model: owner criteria](quality-model.md#owner-criteria-2026-10-14-dry-solid-extensible-traceable-cheap), [pipeline family](../plans/tasks/pipeline-family.md#success-criteria-owner-2026-10-14) |
| 10 | Haiku-only harness arms, reviews included; the Opus one-shot is the bar; Haiku and Sonnet one-shots; named comparison arms only where named (§2.1, §2.2). The 2026-10-12 Cursor, OpenAI, Haiku 4.5 and Opus-review arms are not in the v2 run set | 2026-10-14 | [pipeline family: arms](../plans/tasks/pipeline-family.md#arms), [next steps: owner decisions](../plans/next-steps.md#owner-decisions-for-this-design-2026-10-12) |
| 11 | Follow-up tasks on the arm's own frozen code (§4.5) | 2026-10-14 | [follow-up task](../plans/tasks/pipeline-followup.md) |
| 12 | Prompt hygiene: five rules beside the neutral baseline (§2.4) | 2026-10-14 | [pipeline family: prompt hygiene](../plans/tasks/pipeline-family.md#prompt-hygiene) |
| 13 | Deferral review in real time by an independent Haiku reviewer (§2.5) | 2026-10-14 | [pipeline family: arms](../plans/tasks/pipeline-family.md#arms) |
| 14 | Full isolation of every trial in its own container, on a remote host (§5.1) | 2026-10-14 | [pipeline family: runner and isolation](../plans/tasks/pipeline-family.md#runner-and-isolation), [harness-benchmark#10](https://github.com/jtouley/harness-benchmark/issues/10) |
| 15 | Traceability audit protocol (§7) | 2026-10-14 | [pipeline family: audit protocol](../plans/tasks/pipeline-family.md#audit-protocol) |
| 16 | Cost from token counts at `pricing.json` list prices, split by model; long-task cost is build + follow-up + repairs (§4.6) | 2026-10-12, 2026-10-14 | [next steps: prerequisites](../plans/next-steps.md#prerequisites-stage-0), [quality model: owner criteria](quality-model.md#owner-criteria-2026-10-14-dry-solid-extensible-traceable-cheap) |
| 17 | M10 auditability as a checklist share per run, with the deferral log (§4.7) | 2026-10-12, 2026-10-14 | [next steps: measures](../plans/next-steps.md#measures), [pipeline family: arms](../plans/tasks/pipeline-family.md#arms) |
| 18 | Decision rule restated: comparison A (v1 rule, same model), comparison B (non-inferiority to the bar, margin 0.25), comparison C (beyond the bar), and the answer as the cheapest arm in the top design tier (§8) | 2026-10-12, 2026-10-14 | [next steps: decision rule](../plans/next-steps.md#decision-rule-for-this-question), [quality model: owner criteria](quality-model.md#owner-criteria-2026-10-14-dry-solid-extensible-traceable-cheap) |
| 19 | Operational definitions that v2 adds, each marked [v2] and listed in §11 for owner confirmation | 2026-10-14 | this document |
| 20 | No model or person decides a measure by judgment. M2 becomes defects detected by code: frozen edge checks and probe inputs with pre-committed severity, plus tests a fixed, blind reviewer proposes, kept only when they pass on the reference and fail on the arm, run against every arm, with severity by rule; M3 is decided by script; the design checklist, the M7 comparison column and pairwise judging are dropped; the audit is scored by script against the answer key, with no human spot check (§4, §6, §7, §8.5) | 2026-10-19 | [harness-benchmark#41](https://github.com/jtouley/harness-benchmark/issues/41) |

## Changelog

- v2 (2026-10-14; amended 2026-10-19, grading by code, a reviewer only proposes tests, #41): this version. Changes from v1 in
  the table above.
- v1 (2026-10-10): first version ([criteria v1](criteria.md)).
