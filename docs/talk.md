# Talk track: "Why a harness, when the model is this good?" (20 minutes)

A ready-to-present outline. Each section has a time box, a headline, what to show, and speaker
notes. Every number comes from the [whitepaper](whitepaper.md), the [findings](findings.md), the
[iteration 4 data](experiments/2026-10-12-iteration-4/), the [pilot](experiments/2026-10-13-pilot.md) and the
[pipeline trials](experiments/2026-10-15-pipeline-trials.md).
Each section states what the harness bought, then what it did not buy. The talk never claims more
than its sample sizes can show.

The story in one line: **where a harness earned its place, it was by verification, not by ceremony.**
Whether it can also save money is the open question.

The thesis, checked against the data (16 October 2026): **a harness buys verification and
accountability. It does not make a strong model write better code.** In iteration 4, no crash reached the
harness's delivered code. Each one-shot shipped two. On well-specified tasks a one-shot matched the
harness's code quality at about 1/30 of the time. An independent Opus agent's review of the running result recovered a
bug that the cheap models missed: 1 of 10 cheap one-shot runs fixed both B01 defects, against 3 of 3 with an
Opus review loop (Haiku and Sonnet pooled, Fisher exact test, one-sided, p ≈ 0.014, small samples). The
first round of separate reviewer agents found most of the confirmed defects ([review value](review-value.md)). A long planning
pipeline did not help: on a cheap model it stalled before it wrote code. Precise specs are why the
one-shot did well. Specs as executable contracts are not tested yet.

**Cost figures.** Haiku 5.5 dollar figures in this talk use the base price for every request, so they
are lower bounds: Haiku 5.5 costs 5 times more for a prompt above 100K tokens, and the scripts priced
session totals ([next steps](next-steps.md#cost-accounting-price-each-request-at-its-own-tier-planned-2026-10-16)).

---

## 1. The setup (0:00–1:00)

**Headline:** We gave the same request to strong and cheap models, alone and inside our harness. Then
we checked the result without knowing which setup (arm) made it.

**Show:** six rounds: iteration 4 (three small feature tasks), a pilot (Cadence on a cheap model), B01
(a real multi-cause bug), a sample of SWE-bench Pro, three long data pipelines, and Cadence reviewing its
own repository.

**The question:** today's strong models, Opus 5.5 among them, finish small work alone. So
what is a harness for now?

**What a harness is.** An AI coding model can write code from a request. A harness is the process
around the model: it makes a plan, runs tests, has separate agents review the work, and applies rules
that the model cannot skip. Cadence is the harness we built and measure here. A one-shot is the model alone, given the request once,
with no harness. An arm is one setup under test: a model alone, or a model inside a harness.

**Dark coding: no human in the loop.** A human starts each run. After that, agents do the work.
- **Benchmark runs.** Each run gets one prompt. In iterations 3 and 4 and the pilot, the prompt says:
  "Nobody will answer questions: work autonomously to the end." The pipeline and SWE-bench runs are
  headless (`claude -p`), so no one can answer during a run. No human answers, approves or fixes anything during a run. The graders (scripts and blind grader agents) run
  after the agent stops.
- **Cadence on its own repository.** Agents wrote the plans, reviewed them, wrote the code, reviewed the
  pull requests and fixed the findings. Separate agents did the reviews. The owner started the runs and
  set the rules.
- **The few human decisions are on the record.** Examples: to restart Docker after a crash, and to give
  the trial runs a test ticket number. A person did each of these. Each one happened between runs or
  after a run, never during a run.

**Notes:** **Disclosure:** I wrote Cadence. That is why the rules were written down before the runs,
why the graders were blind, and why the results against Cadence stay in.

## 2. The question, and why cost matters (1:00–2:30)

**Headline:** Is a harness worth its cost compared with one strong model alone?

**Show:**

- The rule from [criteria v1](criteria.md#6-decision-rule-pre-registered): a harness is worth it only if
  it gives **fewer defects** or **more trustworthy evidence** at an acceptable cost. "Solves the task"
  is not enough.
- Per-token list prices: Opus 5.5 $4 / $20 per million, Haiku 5.5 $0.10 / $0.50 (for prompts up to 100K
  tokens). **Up to a 40 times gap.** Above 100K prompt tokens it is $0.50 / $2.50, an 8 times gap, and
  that is where both pilot Cadence orchestrators ended (111,736 and 156,578 prompt tokens).

**Notes:** A harness can pay in two ways. It gives evidence that a one-shot cannot give. Or it lets a
cheap model reach the strong model's result: on a model at 1/40 of the price (1/8 above 100K prompt
tokens), extra tokens are cheap.
We test both.

## 3. How the grading works (2:30–2:55)

**Headline:** Pass or fail comes from deterministic tests. Only the quality score uses an LLM grader.

**Show:**

| Kind | What it does |
|---|---|
| **Deterministic: small tasks** | Iterations 3 and 4 (T04–T06) run a hidden test suite on the delivered code. Each task has 6 or 7 hidden tests. `grade.py` also runs the process checks of the harness arms. |
| **Deterministic: SWE-bench Pro** | Harbor's verifier runs the hidden tests of each task. A task passes at a reward of 1.0. |
| **Deterministic: pipelines (P1–P3)** | `grader.pyz` runs as root from a folder that the agent cannot read. It runs 7 checks (4 batch, 3 stream) against a hashed answer key. It builds twice and gives 0 when the second build changes an output. It gives 0 when no run read the replayed stream to the end. Each reference solution scores 7/7, and each untouched skeleton scores 0. |
| **B01 (private)** | B01's grader is private. It checks the product outcome in the running stack and a second defect on another entry point. |
| **Deterministic: footprint and enforcement** | The footprint tier counts tokens. The enforcement tier replays agent actions through each harness's installed hooks. `cbench verify` calculates each number again and compares it byte for byte. |
| **LLM: blind quality score** | One Opus grader per task sees the code of every arm in an anonymous folder. It scores design, correctness, readability and tests from 1 to 10. It must reproduce each defect with a command. No command, no defect. |
| **Rule: defect severity** | The authors (people, after the run) set severity from the reproduced defects by a written rule. Major is a traceback or a breach of a sentence in the spec. An undelivered run counts as one critical defect. |
| **LLM, planned: audit** | For the pipelines, a blind auditor agent gets the record of each failed run and must find where the run went wrong. |

**Notes:** One rule covers a grader change after we see an arm's output. When the merged grader
contract already accepts a shape and the code does not, we (people, after the run) fix the grader and grade every affected run
again. Any other reading stays as it is until the owner decides. One fix came after we saw the output of
Opus on P1. So Opus's P1 score of 6/7 is provisional.

Known weaknesses:

- One grader per task.
- One trial per cell in most rounds.
- [Criteria v2](criteria-v2.md) asks for two independent blind reviewer agents, a script that runs each
  reproduction again in a clean copy, and 5 runs per cell before a result counts.
- B01's grader is private, so nobody else can check it.

## 4. The tests at a glance (2:55–3:15)

**Headline:** Small tasks with a precise spec, real bug fixes, and long pipelines.

Size comes from the task class in the criteria. The table shows the strong model's own result next to it.

| Test | What it asks | Size | Opus 5.5 alone | How it is graded | What was done |
|---|---|---|---|---|---|
| T04 multi-currency (iteration 4) | Add a currency to each account and convert reports to a base currency. | Small, precise spec (class S) | 1 of 1 delivered, 6/6 hidden tests | 6 hidden tests and a blind grader | 5 arms ran once each: Cadence, ship-feature, and Opus, Sonnet and Haiku 4.5 alone. All arms passed 6/6 except Haiku (5/6). Opus alone had the top quality (8.75), Cadence 6.75. |
| T05 budgets (iteration 4) | Add monthly category budgets, a budget report and over-budget alerts. | Small, precise spec (class S) | 1 of 1 delivered, 7/7 hidden tests, 2 crashes shipped | 7 hidden tests and a blind grader | The same 5 arms ran once each. All passed 7/7. Each one-shot shipped two crashes, and the harnesses shipped none. Quality: Cadence 7.75, Opus 7.25. |
| T06 audit and undo (iteration 4) | Log each ledger change and add `undo N` to revert the last N changes. | Small, precise spec (class S) | 1 of 1 delivered, 6/6 hidden tests | 6 hidden tests and a blind grader | The same 5 arms ran once each. Cadence, Opus and Sonnet passed 6/6. ship-feature got 0/6 and Haiku 5/6. Quality: Opus 8.00, Cadence 7.50. |
| Pilot (T05, full Cadence on Haiku 5.5) | Do T05 again with the full Cadence procedure on a cheap model. | Small, precise spec (class S) | 1 of 1 delivered, 7/7 hidden tests, 111 s, $0.40 | 7 hidden tests, quality tools and a clean-room check | 3 arms ran once each. Cadence on Haiku stopped at P6 ($1.13, 75 min). Cadence on Haiku with Opus reviews stopped at P9 ($3.19, 27 min). Neither Cadence arm delivered code. |
| SWE-bench Pro, 20-task sample | Fix a real issue in an open-source Python repository. | Real bug fix, one repo (no class assigned) | 18 of 20 | Verifier reward 1.0 (hidden tests) | Opus, Sonnet and Haiku 5.5 alone, one try per task. Opus 18/20 ($5.79), Sonnet 18/20 ($2.57), Haiku 17/20 ($0.54, a lower bound). The sample has no clear lift task. |
| SWE-bench Pro hard 3 | Fix the 3 tasks that Opus missed or did not start in round 1. | Real bug fix, one repo (no class assigned) | 2/5, 2/5, 5/5 | Verifier reward 1.0 (hidden tests) | Opus alone, 5 tries per task. `ansible-d2f80991` 2/5, `openlibrary-30bc73a1` 2/5, `ansible-d9f18662` 5/5 (its round 1 try died in setup). |
| B01 (private multi-cause bug) | Fix a real bug with several stacked faults across services. | Real bug across services | 10 of 10, both defects fixed | Product outcome in the running stack, two defects | One-shots: Opus 10 runs, Sonnet 5, Haiku 5. Sonnet fixed both defects 1/5 and Haiku 0/5. An Opus review loop fixed both in 3 of 3 runs (Haiku 2, Sonnet 1), at $1.15 and $1.24 against $1.29 for Opus. Interim: the runs are private. |
| P1 DuckDB (pipeline family) | Build a batch and stream pipeline to Parquet marts with dlt and dbt-duckdb. | Long, many parts (class L) | 6/7 checks* | 7 checks against a hashed answer key | Opus, Sonnet and Haiku 5.5 alone, one try each. Opus 6/7 ($5.82), Sonnet 3/7, Haiku 0/7. Two check readings are open owner decisions. |
| P2 DataFusion (pipeline family) | Build the same pipeline with a config-driven engine on Arrow, Polars and DataFusion. | Long, many parts (class L) | 5/7 checks | 7 checks against a hashed answer key | Opus, Sonnet and Haiku 5.5 alone, one try each. Opus 5/7 ($7.84), Sonnet 3/7, Haiku 0/7. |
| P3 Spark (pipeline family) | Build the same pipeline with Scala 2.13 and Spark 3.5. | Long, many parts (class L) | 3/7 checks | 7 checks against a hashed answer key | Opus, Sonnet and Haiku 5.5 alone, one try each. Sonnet 5/7, Opus 3/7 ($7.92), Haiku 0/7. No model passed all 7 checks on P1 to P3. |
| Tier 1: context footprint | Count the tokens that each harness adds to the context. | n/a | n/a | Pinned proxy tokenizer, deterministic | 6 harnesses and a baseline, no agent. Cadence adds 671 tokens to each request and 9,078 to 62,141 tokens to load its workflow. |
| Tier 2: enforcement probes | Replay 10 actions and record which ones the hooks block. | n/a | n/a | Hook decision against the intent of each scenario | 8 harness and host rows. Cadence met the intent in 7 of 9 scenarios on Claude Code and on Cursor. The other harnesses met 2 to 4. |
| Review value (PR review rounds) | Count the real defects that each PR review round finds. | n/a | n/a | Script count of blocking findings that a later round marks fixed | 18 review reports. The first round found 40 of the 51 defects that a later round marked fixed (78%). Rounds 3 and later raised 10 findings, none of them blocking. |
| Cadence on its own repository | Count the must-fix findings that Cadence caught while it built itself. | n/a | n/a | Hand count of review and ledger records | 10 merged runs, 10 to 17 October. Cadence caught and closed 85 must-fix findings before merge, 62 (73%) of them before any code. Interim: the records are local. |

\* Provisional: the operator fixed the grader after the Opus output came in.

## 5. Iteration 4: no crash shipped, no quality gain (3:15–4:00)

**Headline:** On small, precise tasks, the harness shipped no crash. Its code was not better than the
model alone. It took about 30 times longer.

**The task.** Each agent adds one feature to `ledgerlite`, a Python CLI of about 300 lines. All arms get
the same task text and start from the same commit. T04 adds a currency to each account, and stored
exchange rates convert the reports to a base currency. T05 adds a monthly spending limit for each
category, a budget report and an over-budget alert. T06 records each change in an audit log, and
`undo N` reverts the last N changes. Hidden tests run on the delivered code. One blind Opus grader scores
each solution and must reproduce each defect with a command.

<details>
<summary>Original prompt (T05, budgets)</summary>

```text
Add monthly category budgets to ledgerlite. `budget set CATEGORY LIMIT` sets a monthly spending limit across all accounts (LIMIT must be positive, else exit 2); `budget list` prints `CATEGORY: LIMIT` sorted by category. `report budget YYYY-MM` prints one line per budgeted category: `CATEGORY: spent SPENT of LIMIT (PCT%)`, with ` OVER` appended when spent > limit. Spending is the sum of the negative amounts in that category and month, as a positive number (refunds do not reduce it); PCT is spent/limit*100 rounded to the nearest integer; money is shown with 2 decimals. When `tx add` or `import` pushes a category's spending for that month past its limit, the command also prints `alert: CATEGORY over budget for YYYY-MM (SPENT/LIMIT)`, once per category per command. SPENT in the alert is the month's spending after the whole command. Budgets persist in the store; existing stores without budgets keep working.
```

</details>

**Show:** three feature tasks on a 300-line Python ledger (T04–T06), one run per cell, one blind grader.

| Arm | Delivered | Blind quality | Crashes shipped | Time per task |
|---|---|---|---|---|
| Opus 5.5 one-shot | 3 of 3 | **8.00** | 2 | 2 min |
| ship-feature (Opus) | 2 of 3 | 7.88 | 0 | 42 min |
| Cadence (Opus) | 3 of 3 | 7.33 | 0 | 63 min |
| Sonnet 5.5 one-shot | 3 of 3 | 7.08 | 2 | 2 min |
| Haiku 4.5 one-shot | 1 of 3 | 3.50 | 2 | 4 min |

**Notes:** Say it plainly: on this test, our harness did not write better code. Per task, Opus alone minus
Cadence is +2.0, −0.5 and +0.5. Only the first is outside single-run noise. So the honest line is "no
gain shown", not "the harness made it worse".

## 6. Iteration 4: what the harness bought (4:00–5:30)

**Headline:** The harness shipped no crash and fewer serious defects. It closed every task or stopped
with a reason. It left a record, and it enforced its rules. The price was about 30 times the wall time.

**The task.** The same three `ledgerlite` tasks and the same T05 prompt as before.

**Show:** what the harness bought, measured.

| Bought | Measured |
|---|---|
| **No crash shipped.** | Cadence 0. Each one-shot shipped 2: Opus 5.5, Sonnet 5.5 and Haiku 4.5. |
| **Fewer serious defects per run.** | Major or critical defects per run: Cadence 0.67, Opus 5.5 1.00, Sonnet 5.5 1.33, Haiku 4.5 2.67. |
| **Every task delivered, or a recorded stop.** | Cadence delivered 3 of 3. Two tasks ran again (a person started the reruns) after a fix to a Cadence defect. Before the fix, both broken runs stopped with a recorded reason. Never confidently wrong: no run reported success when it failed. |
| **Defects caught before delivery.** | Cadence's reviewer agents raised 6 must-fix findings in 3 runs. A command verified each fix. |
| **An audit trail.** | Each run has a plan, independent reviews by 8–12 separate agents, a verified findings ledger and 12–23 attestation rows. A one-shot leaves at most one commit. |
| **Rules the model cannot skip.** | The hooks meet intent on 7 of 9 probes (at the pinned `e5c3a92`). They block a forged approval, a self-certified verdict, an edit before plan approval and a stop mid-run. A one-shot session enforces none of these. |

**What a crash is.** A crash is a Python traceback from a `ledgerlite` command. All six one-shot crashes
are on the budgets task. Opus and Sonnet crashed on a NaN amount and on the budget report for a tiny
limit. Haiku 4.5 crashed on a NaN amount and on a NaN limit. Cadence's own reviewer agents caught a similar crash
before delivery: a stored limit that crashed with a traceback. Cadence fixed it. So its delivered code
had 0 crashes.

**Why 0.67 when the crashes are 0.** "Major or critical defects per run" counts every serious defect.
A crash is one kind. Cadence had 2 major defects in 3 runs (0.67). Neither is a crash. Both break a
sentence of the spec. On budgets, a multi-month import gives two alerts for one category. On audit and
undo, an import of 0 rows writes no audit entry (the grader called it a judgment call). Opus alone had 3
major defects (1.00): the two crashes and the same double alert.

**What it did not buy:**

- **Speed or cost.** About 30 times the wall time and 4 times the tokens of a one-shot.
- **Better code.** Blind quality did not improve: Opus alone 8.00, Cadence 7.33.
- **Restraint.** The graders marked Cadence down for scope that the task did not ask for ("heavier than
  needed").
- **Host independence.** User-level skills with the same names replaced Cadence's reviewers.

**Notes:** Against Opus alone, the defect gap is 0.33 per run. Our pre-registered rule sets a bar of
0.5. So the rule does not count "fewer defects than Opus" as shown. The crash count is the clearest
signal. It comes from one task. Each cell ran once.

## 7. The pilot: full Cadence on a cheap model delivered nothing, and said why (5:30–7:30)

**Headline:** We put the whole harness on Haiku 5.5. It stopped in its own process before it wrote any
code. It did not claim success.

**The task.** The pilot uses T05 (budgets) from iteration 4, with the same prompt. In
iteration 4, each one-shot shipped a crash on this task. The pilot compares Cadence on Haiku 5.5 with an
Opus 5.5 one-shot. The 7 hidden tests of iteration 4, the quality-model tools and a clean-room check
grade each run.

**Show:** T05 (budgets), clean room, one run per arm ([pilot](experiments/2026-10-13-pilot.md)).

| Arm | Result | Time | Cost |
|---|---|---|---|
| Opus 5.5 one-shot | Delivered; 7/7 hidden tests; quality gate passed | 111 s | $0.40 |
| Cadence, all Haiku 5.5 | Hard stop at the adversarial review (P6) after four plan updates | 75 min | $1.13 (lower bound; up to $5.66) |
| Cadence, Haiku 5.5 + Opus reviews | Hard stop at the gate that checks delegation records (P9): no records | 27 min | $3.19 (lower bound; up to $4.50) |

**Notes:** The cheap arms spent about 3 and 8 times the dollars of the Opus one-shot (up to 14 and 11
times at the upper bound), and delivered nothing. Both orchestrators ended above 100K prompt tokens. Static
skill text explains only about 18K of that; one cause is that each peer returned a full report into the
orchestrator's context (Cadence now has one-line peer returns and a context budget; not yet rerun).
The causes: the adversarial review had no cycle limit and found new edge cases each round. In the other
arm, a gate depends on the orchestrator recording its own delegations, and the cheap orchestrator did not
record them. A full harness on a weak orchestrator adds places to stop. Both runs stopped and said why:
it was never confidently wrong. We found four Cadence defects. Cadence fixed two, and work on the other two continues. This is n = 1. It shows a failure mode,
not a rate.

## 8. The calibration rule: choose tasks by what the bar does (7:30–8:30)

**Headline:** A task is hard only when the strong model fails it, not when it looks hard.

**Show:** two task classes ([next steps](next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13)):

- **Lift task:** the Opus one-shot is reliable and the cheap one-shots are not. Can a harness lift a cheap
  model to the bar, for less?
- **Beyond task:** the Opus one-shot is unreliable. Can a harness raise reliability at all?

**Notes:** Reliability is measured over repeats. A one-shot that passes once says nothing about the next
run. T05 is out: the bar solves it in two minutes.

## 9. B01: a real multi-cause bug (8:30–10:00)

**Headline:** Opus fixed it every time. The cheap models fixed the main path and missed the rest.

**The task.** B01 is a real bug in a private third-party repository. The bug has several stacked faults
across services. Mocked tests pass while the bug is present. Only a running system shows the bug. The
prompt is the original product request. The grader runs the real stack and checks two outcomes: the main
path, and a second defect on a different entry point. The original fix, made before this benchmark with a person's help,
also missed that second defect. The prompt is not public, because the code belongs to a third party.
We describe the task only.

**Show:** the scores of each one-shot arm.

| Arm | Main path fixed | Both defects fixed | Mean cost | Mean time |
|---|---|---|---|---|
| Opus 5.5 one-shot | 10/10 | 10/10 | $1.29 | 7.3 min |
| Sonnet 5.5 one-shot | 4/5 | 1/5 | $0.39 | 3.5 min |
| Haiku 5.5 one-shot | 5/5 | 0/5 | $0.11 (lower bound) | 8.6 min |

**Notes:** B01 is a lift task: the bar is reliable, the cheap models are not. The code belongs to a third
party, so we publish the scores only. After a contamination incident (processes from earlier runs
outlived them), all runs were regraded with an isolated grader. No grade changed. One container per trial
has been in place since 15 October; these B01 runs ran before it.

## 10. Why the cheap models miss (10:00–12:00)

**Headline:** Not reasoning depth. Scope narrowing, and coverage.

**Show:** from the transcripts of all 20 B01 one-shots.

| | Opus | Sonnet | Haiku |
|---|---|---|---|
| Turns per run (mean) | 90 | 42 | 166 |
| Tool calls per run (mean) | 41 | 22 | 64 |
| Runs that hit the second defect's error | 10 of 10 | 1 of 5 | 5 of 5 |
| Runs that fixed it | 10 of 10 | 1 of 5 | 0 of 5 |

**Notes:**

- **Haiku did more work, not less.** It hit the error in every run. In one run, it named the cause
  correctly. Then it wrote that it would "leave that out of this change and report it". Its final summary
  did not mention it. That is scope narrowing plus a dropped commitment.
- **Sonnet mostly never exercised that path.** When it did, it fixed it. That is coverage.
- **Opus treated every broken entry point as part of the request.**

Two harness mechanisms could fix both failures without a strong model, and neither is tested yet: (1)
**no silent deferral**: each decision to leave work out goes to an independent reviewer agent at once
(not built yet); (2) **contracts before
code**: executable checks for every entry point the request covers, and the session cannot end while one
fails.

## 11. The review loop: reliability back, no money saved (12:00–13:30)

**Headline:** An independent Opus agent that checks the running system recovered the miss in every valid
run so far (2 Haiku, 1 Sonnet). It costs about as much as Opus alone.

**The task.** The same B01 bug as before, with the same private prompt. The prompt is not public. A
minimal harness runs it. The cheap model does the work. An independent Opus subagent then checks the
result in the running stack. The cheap model fixes each problem that the reviewer finds. The loop ends
when the reviewer approves, or after 3 reviews.

**Show:** both-defect fixes and cost, against the Opus one-shot.

| Arm | Both defects fixed | Mean cost |
|---|---|---|
| Opus 5.5 one-shot | 10/10 | $1.29 |
| Haiku 5.5 + Opus review loop | 2/2 | $1.15 (Haiku part a lower bound) |
| Sonnet 5.5 + Opus review loop | 1/1 | $1.24 |

**Notes:** Both Haiku runs and the one Sonnet run fixed both defects. Two more runs were set aside as
invalid (Docker went down during the run. A person restarted it between runs). That is a signal, not yet a reliability measure. The reviewer
must run and exercise the stack to check the work, and that costs about as much as Opus doing the task.
So the review loop is a signal that the reliability gap can be closed, but it does not save money. The samples are 1–2 runs per arm. The open question: can the check itself be
cheap?

Pooled, the cheap one-shots fixed both defects in 1 of 10 runs and the review loops in 3 of 3 (Fisher exact
test, one-sided, p ≈ 0.014). Small samples, two models pooled, one bug.

Process evidence from outside the benchmark points the same way: on 16 October, fresh-subagent reviews of
two Cadence PRs found 5 and 4 must-fix defects; two of them came from fixes of earlier nits
([review value](review-value.md#independent-reviews-of-two-cadence-prs-16-october-2026)).

## 12. SWE-bench Pro: the cheap one-shot is close, the bar is unreliable (13:30–14:15)

**Headline:** On a published sample, Haiku alone is within one task of Opus at a tenth of the cost. The
open question is the tasks where Opus itself is unreliable.

**The task.** SWE-bench Pro is a public set of real issues from open-source repositories. The sample has
20 Python tasks from three repositories: ansible (9), qutebrowser (5) and openlibrary (6). The agent gets
the issue and the repository, and must change the code to fix the issue. A task passes when the hidden
tests of the verifier give a reward of 1.0. The difficult parts are a large codebase that the agent does
not know, and tests that the agent cannot see. The prompt of each task is the issue text in the public
SWE-bench Pro set (Harbor `scale-ai/swe-bench-pro`). This repository keeps only the task ids
(`sample20.txt`) and the results, so we show no prompt.

**Show:** 20 Python tasks drawn at random, Claude Code in each task's container (Harbor), one one-shot try
per model:

| Model | Passed | Cost |
|---|---|---|
| Opus 5.5 | 18/20 | $5.79 |
| Sonnet 5.5 | 18/20 | $2.57 |
| Haiku 5.5 | 17/20 | $0.54 (lower bound) |

Two tasks passed only 2 of 5 Opus tries.

**Notes:** These tasks are not lift candidates: a cheap model alone gets nearly all of them, so a harness
has little to add on them. The two unreliable tasks are beyond candidates: a harness that raises their pass
rate does something the strong model alone cannot do reliably. Limits: 20 tasks, one try per model, and
trials that died in container setup were rerun (a person started the reruns). One try is a pass rate, not reliability (pass^k).

## 13. The pipeline family: no one-shot passes long work, and harness runs are in progress (14:15–15:30)

**Headline:** On long-horizon pipelines, every one-shot failed at least one check, Opus included. At one try
each, they are beyond candidates. Harness runs (Cadence on Haiku) are in progress. We will publish their
results here.

**The task.** The agent builds a data pipeline from raw public data to Parquet marts. The batch part uses
USAspending awards for fiscal year 2024 and Census county population. The stream part uses the Wikipedia
`recentchange` edit stream. A replay server sends a recorded capture and causes disconnects. All three
tasks use the same spec. Only the stack is different. P1 uses dlt and dbt-duckdb. P2 uses a
config-driven engine on Arrow, Polars and DataFusion, with dbt-duckdb. P3 uses Scala and Spark, with
dbt-spark. The grader runs 7 analyst checks against a hashed answer key. The difficult parts are
exactly-once delivery across disconnects, lateness in stream time and exact sums of money.

<details>
<summary>Original prompt (P1, <code>golden/pipeline/P1/prompt.md</code>)</summary>

```text
Build a pipeline that answers two questions for analysts, from raw public data to columnar tables a
BI tool can query directly.

**Question A (batch): where did federal contract and grant money go in fiscal year 2024?** In total and
per person, by state, county, awarding agency and month.

**Question B (stream): how is Wikipedia being edited right now?** Edits per wiki, per namespace and per
5-minute window, split by human and bot, with the net bytes added.

### Inputs

- `data/raw/usaspending/`: USAspending.gov prime award transactions, FY2024, for the agencies listed in
  `data/raw/usaspending/README.md`.
- `data/raw/census/`: the Census Bureau county population estimates.
- `data/raw/sitematrix.json`: the Wikimedia site matrix (wiki id, language, project).
- The edit stream: a Server-Sent Events endpoint with the Wikimedia EventStreams `recentchange` format.
  During development and grading it is `http://localhost:8099/v2/stream/recentchange`, a replay of a
  recorded capture. The replay server behaves like the real service, including disconnects. In a live
  demo the same code points at `https://stream.wikimedia.org/v2/stream/recentchange`.

### Architecture

- **Lake.** Ingestion writes every source to a Parquet lake under `lake/` (one folder per source table,
  partitioned where it helps). The lake keeps the source's data and adds only load metadata.
- **Models.** A dbt project in `transform/` builds everything after the lake: staging models, the star
  schema and the marts. Each mart has a dbt model contract (column names and types enforced).
- **Publish.** The marts are materialized as Parquet under `out/marts/` (one folder per mart). Anything
  downstream reads only `out/marts/`.

### Outputs

1. A star schema for Question A: one fact table at the grain of one award transaction, and dimensions
   for agency, place (state and county) and date. A monthly mart by state, county and agency, with
   net obligations, population and obligations per person.
2. For Question B: a fact table of edits at the grain of one change event, and a mart of 5-minute
   windows by wiki, namespace and actor type (human or bot), with the edit count and the net bytes
   added. The stream consumer lands micro-batches in the lake; incremental dbt models build the edit
   fact and the window mart from them.
3. The lake under `lake/`, the dbt project under `transform/`, and the published marts under
   `out/marts/`, plus whatever the stack section asks for.
4. `oracle_map.yml`: for each question in the "Checks" list below, the table and column (or SQL view)
   that answers it.
5. `DECISIONS.md`: each place where this spec left a choice to you, what you chose and why.

### Rules

- `make build` runs the batch part from the raw files. Running it twice must not change any output.
- `make stream DURATION=<seconds>` consumes the stream for that long and updates the stream tables.
  If the connection drops, the consumer resumes where it stopped. Stopping and starting the consumer
  must not count any event twice or lose one.
- Event time, not arrival time, places an edit in a window. Windows are 5 minutes long and start on
  the multiples of 5 minutes (UTC).
- Lateness is measured in stream time, not by a clock: an event is **late** when, at its first
  arrival, the highest event time among the events that arrived before it is more than 10 minutes
  after the end of its window. A late event is not added to its window; put it in a `late_events`
  table instead. The replay can run faster than real time, so a wall-clock reading of "late" is wrong.
- Money is in US dollars, summed exactly (no floating-point sums).
- Document the grain of each model. Test the keys of each model with dbt tests.

### Checks the analysts will run

1. FY2024 net obligations per awarding agency.
2. The ten counties with the highest FY2024 obligations per person.
3. The number of awards with a net negative obligation in FY2024.
4. For one month: county totals add up to state totals, and state totals add up to the source total.
5. For the stream: edits and net bytes per wiki for the replayed hour, split human and bot. Late
   events are included: this check counts every edit consumed, on time or late.
6. For the stream: the 5-minute windows with the most edits on `en.wikipedia.org` (on-time edits only).
7. For the stream: the count of late events.

### Amendment A (from the analysts, after the first review)

"Per person" means per resident in the population estimate for **July 1, 2024**, not the 2020 census
count. Where a county has no 2024 estimate, use the latest earlier estimate and say so in
`DECISIONS.md`.

Use Python 3.12 and dlt to land the raw files and the stream in the Parquet lake (dlt's filesystem
destination with Parquet files). Model with dbt-duckdb reading the lake; materialize the marts as
Parquet with dbt-duckdb's `external` materialization. The skeleton pins the versions in
`pyproject.toml`; do not change them.
```

</details>

**Show:** One spec on three stacks, run on the isolated runner (one container per trial, the grading run
offline, with a fresh `HOME`). Seven hidden checks per task. One try per cell (k = 1). Cost at list prices:

| Task | Stack | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 |
|---|---|---|---|---|
| P1 | dlt, dbt-duckdb | 0/7 ($0.30) | 3/7 ($2.06) | 6/7 ($5.82, provisional) |
| P2 | Arrow, Polars, DataFusion, dbt-duckdb | 0/7 ($0.28) | 3/7 ($4.56) | 5/7 ($7.84) |
| P3 | Scala, Spark, dbt-spark | 0/7 ($0.38) | 5/7 ($3.68) | 3/7 ($7.92) |

No run passed every check: 0 of 9. Each run took 25 to 70 minutes. The nine graded trials cost $32.84.

**Notes:**

- **Every delivered pipeline worked as software.** Each built twice with no change to an output and
  consumed the stream to the end. The failures are in the answers, not the build.
- **Haiku answered against the spec.** It read the warehouse file and unpublished dbt views, which the spec
  puts out of bounds. Even with its P2 map fixed by hand (a person, after the run), it scores 3/7 (a diagnostic, not a result). This
  is the same scope problem as B01: the cheap model does a narrower task than the one it was given.
- **Opus is not a reliable bar here.** It led on P1 and P2, and Sonnet beat it on the Scala stack. On B01
  Opus fixed both defects 10 of 10 times. Here no model passed every check. At one try each these are beyond
  *candidates*, not calibrated beyond tasks (that needs the bar to pass at most 1 of 3 tries): a harness
  that raises the pass rate would do what the strong model alone cannot.
- **Where is the harness run?** Cadence on Haiku runs on these tasks now. We will publish its results
  here. No harness result is in this repository yet. The runner installs a harness as a Claude Code
  plugin (`--plugin-dir`). Two more harness arms exist: `harnesses/reviewloop` and `harnesses/verifyloop`.
  The 15 October round ran the one-shot baselines only. They are the bar for the harness runs.
- **Limits.** One try per cell. Opus's P1 6/7 is provisional: a grader fix (reading a `checks:` key beside
  other keys) was made after its output was seen. Two check readings are open owner decisions (TASK-81):
  whether grant money is placed at the recipient's county or the place of performance (it decides 4 of
  the 6 Sonnet and Opus runs on P2 and P3), and whether check 4 accepts a reconciliation query (it affects all six, including Opus's one miss on
  P1). Grades can
  move when those are decided. The trials ran on an Apple Silicon laptop, not the specified x86-64 host, so
  times are laptop times.
- **Two harness-benchmark defects were found and fixed:** the grader deleted uncommitted work before
  grading (now `--snapshot-worktree`), and it did not read a `checks:` key beside other top-level keys.
  The benchmark is software too.

## 14. Cadence on its own repository: review caught what green tests missed (15:30–16:15)

**Headline:** Outside the benchmark, independent reviewer agents keep catching what the model and its test
suite pass.

**Show:** Every review here is a separate Cadence peer agent. No person reviewed.

- **This week, 10 to 17 October** ([self-evidence](experiments/2026-10-17-cadence-self-evidence.md)).
  Cadence stopped 85 must-fix findings before merge in the 10 Cadence runs that merged. Plan time caught
  62 of them (73%), before any code existed. Code review by reviewer agents caught the other 23. Cadence deferred 0 of them.
  None reached main open.
- **A new language check** (Go, Java and C/C++ in the complexity check): 2,561 tests passed (1 skipped).
  PR #118 had not merged when we wrote the self-evidence doc. The reviewer agent still blocked it: a Go function literal passed to a call was scored one nesting level too shallow. Fixed and
  verified by command before closure.
- **A test-ownership change:** the reviewer agent found a gate that crashed with a traceback on a
  malformed file.
- **Review rounds** ([review value](review-value.md#independent-reviews-of-two-cadence-prs-16-october-2026)):
  on two other Cadence changes, the first round of reviewer agents found 6 of 9 must-fix items, and each later round found
  one more. Two came from fixes of earlier nits.

**Notes:** Process evidence, not a controlled comparison. The week's counts come with stated limits. They
come from the operator's local Cadence records, which are not public. You can check them only against the
public Cadence PRs. "Must-fix" is the reviewer agent's word, and no person graded it again. 62 of the 85 items were
closed by text in a later review, not by a check that ran again. There is no control group. So the counts do not
show that these bugs would have shipped without Cadence. They show that the stages found them. The same discipline runs on Cadence's own debt:
Cadence's own complexity audit is being paid down in a set of refactors.

## 15. When to use a harness (16:15–17:30)

**Headline:** A strong model can write small, clear code alone. Use a harness when you must trust the
result.

**Show:**

| The work | What to use | Why |
|---|---|---|
| A small, clear change | One strong model, no harness | On three small tasks, the model alone was as good as the harness and about 30 times faster. On 20 real issues from open-source projects, even the cheapest model passed 17. |
| Work that must not break, or that a person must approve | A harness | On three small tasks it shipped no crash (each model alone shipped two). It still shipped two spec errors. Separate agents reviewed the plan, the tests and the code. It kept a record of each decision. |
| Long work with many parts | Still open | No model alone passed every check on the three data-pipeline tasks. We test Cadence on the cheapest model there now. |

**Notes:** A harness is the process around an AI coding model: a plan, tests, reviews by separate
agents, and rules the model cannot skip. It costs time. Use it where a wrong result costs more than the
time. The first two rows come from measured runs, mostly one run for each task. The third row is the
next test.

## 16. What this means for building a harness (17:30–18:15)

**Headline:** Cut the ceremony. Test the scope gate.

**Show:** what to change in a harness, from these results.

| Did not pay | Untested, next |
|---|---|
| A long planning pipeline on a weak orchestrator | Holding scope as a gate: a dropped part of the request is a defect |
| A strong-model reviewer, if the goal is cost | Cheap verification (next) |
| Review as a stand-in for executable checks | |
| Deferral checks that look only at form | |

**Notes:** Holding scope is untested as a gate: Haiku's B01 misses were scope narrowing, and Cadence itself
over-built in iteration 4. The Cadence changes that follow: a cycle limit on P6 (done); a hook writes the
delegation record (done); a no-tracker mode and a verdict that counts only from the peer of its stage
(being fixed); deferrals judged in real time (not built yet). Also done since the pilot: one-line peer
returns and a context budget, and an R3 cognitive-complexity check for every language with an analyzer. The tier-1 and tier-2 results stay measured at the pinned commit
`e5c3a92` ([whitepaper §4.1](whitepaper.md#41-cadence-after-the-benchmarks-pin-status-16-october-2026)). This agrees with Datadog's "harness-first"
argument: verification, not review, is the bottleneck.

## 17. What comes next (18:15–19:15)

**Headline:** Make the check cheap, give it long work, and measure what the record is worth when
something breaks.

**Show:**

1. **Cheap verification.** Haiku-only arms: a verification harness (contracts before code, a stop gate,
   no model reviewer); a review loop with a Haiku reviewer; full Cadence with all peers on Haiku, once its
   two open defects are fixed. In every harness arm, each deferral goes to an independent Haiku reviewer.
2. **Harness arms on the pipeline family** ([tasks](tasks/pipeline-family.md)). The tasks, the
   isolated runner and the one-shot baselines exist. Full Cadence on Haiku is in
   progress. Next: the review loop and the verification harness on Haiku. Then each task's follow-up change
   (a new mart and a dashboard), built by the same arm on its own code. This is work that does not fit
   one session.
3. **Traceability audits.** Seeded traps give each failure a known cause. A blind auditor agent gets only the
   run's record. It must find the cause, where the run first went wrong, and the cheapest fix point. A
   one-shot leaves a transcript. A harness leaves a spec, a plan, phases, reviews and decisions. What is
   each record worth?
4. **The owner's success criteria.** The arm closest to a **DRY, SOLID and extensible** system, whose
   path we can **trace**, and the **cheapest** arm in that top tier.

**Notes:** Each trial runs in its own disposable container on a remote Linux host. Every arm gets the same
prompt, word for word, with no hints and no knowledge of the traps. The measures: cost per defect-free
run, traceability when a long task goes wrong, and design quality under a follow-up change.

## 18. Close (19:15–20:00)

**Headline:** Where a harness earned its place, it was by verification, not by ceremony.

**Notes:** One line and one fork, not a recap. Every gain we measured came from an independent check or a
rule the model could not skip. Next: if a cheap check matches Opus alone on lift tasks, and carries the
long work where no one-shot, Opus included, passed every check, a harness is a cost tool too. If it cannot,
it is a governance tool: worth it where someone must trust the result, not to save money
([findings](findings.md#why-this-still-matters-as-models-get-stronger-and-more-expensive)).

---

## Questions to expect

| Question | Answer |
|---|---|
| "Isn't this just noise?" | Iteration 4 and the pilot are one run per cell; only the largest gaps count. B01 has 5–10 runs per one-shot arm, but only 1–2 per review-loop arm. The review-loop result is a signal, not a rate. |
| "You wrote Cadence. Why trust this?" | The rules were written before the runs, the graders were blind, and the main results do not favor Cadence: no quality gain, and no delivery on Haiku. |
| "Did you tune the prompt for the harness?" | No. Every arm gets the same request text, word for word. A harness arm differs only by its installed harness. Each run has an empty `HOME`, and a script checks it. |
| "Why didn't the harness win on quality?" | The small tasks fully specify every output, so review has little to add. And the harness built more than the request asked for. |
| "Why did full Cadence fail on Haiku?" | Two Cadence defects: a review stage with no cycle limit, and a gate that depends on the orchestrator recording its own delegations. Both are fixed now. The pilot is n = 1. |
| "Isn't Haiku just not smart enough?" | The transcripts say no. Haiku took more turns than Opus (166 against 90), hit the second defect in 5 of 5 runs, and diagnosed it once. It chose to leave it out. A harness can check that scope decision. |
| "What is B01? Can I see it?" | A private brownfield bug in a multi-service application with stacked faults. The code belongs to a third party, so we publish only its scores and the grader design. |
| "The review loop costs as much as Opus. Why use it?" | In 3 valid runs (2 Haiku, 1 Sonnet) it closed the reliability gap: a signal, not yet a rate. The cost is the open question. The next arms try cheap checks: a Haiku reviewer, and executable contracts with a stop gate. If none matches the bar, the harness is a governance tool, not a cost tool. |
| "What about the contamination incident?" | Processes from earlier B01 runs outlived them. Every run was regraded with an isolated grader; no grade changed. One container per trial is now in place. |
| "Why SWE-bench Pro?" | For comparison with outside numbers, filtered by the same calibration rule. On our sample of 20, Haiku alone passed 17 and Opus 18, so it has no clear lift tasks; two tasks are beyond candidates. |
| "Where is the harness run on the pipeline tasks?" | In progress. Cadence on Haiku runs on P1–P3 now, and we will publish its results here. The 15 October round ran the one-shot baselines (Haiku, Sonnet, Opus on P1–P3). They are the bar for the harness. The review-loop and verification arms follow. |
| "Could a one-shot just be asked to write a plan and tests?" | It could. That is a harness in a prompt, with no independent check and no enforcement. The baseline does not allow it, so the comparison stays fair. |
| "What about the bugs in your own harness?" | They are real, and part of the result: a Cadence change that broke two iteration-4 runs until it was fixed, and four defects from the pilot (two fixed, two being fixed). The harness is software, and it needs the review it gives. |
