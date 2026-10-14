# Next steps: the cheapest model that matches Opus, with an audit trail

Status: proposed design (October 2026). Nothing here has run yet. It follows from the
[findings so far](findings.md) and must meet [criteria v1](criteria.md) before any result counts.

## The question

**What is the cheapest model that, inside a harness, matches or beats Opus 5.5 working alone,
and leaves an audit trail that a one-shot run cannot?**

The cheap model may use many more tokens than Opus. What counts is the dollar cost per defect-free delivered run,
the defects that reach the delivered code, and the evidence that the run leaves behind.

## Why this is the right next question

- In iteration 4, a harness on Opus showed no quality gain over Opus alone (Cadence 7.33, Opus alone
  8.00, mostly within single-run noise), at about 4 times the tokens. On these tasks, "a harness on
  the same strong model" buys evidence and enforcement, not better code or lower cost.
- Per-token list prices differ by up to 40 times: Opus 5.5 $4 / $20 per million input / output
  tokens, Haiku 5.5 $0.10 / $0.50 ([`pricing.json`](../pricing.json)). Two conditions: the Haiku 5.5
  price holds for prompts up to 100K tokens ($0.50 / $2.50 above that, which a long harness session
  can pass), and its cache prices are derived, not listed. Cache reads differ by 20 times.
- **Estimate (not a result):** Cadence on Opus used about 4 times the tokens of the Opus one-shot.
  If Cadence on Haiku 5.5 uses a similar number of tokens with a similar mix, and its prompts stay
  under 100K tokens, it costs between 1/10 and 1/5 of the Opus one-shot. A weaker model may need more
  tokens, and prompts over 100K tokens cost 5 times more on Haiku 5.5. It also holds only if a cheap
  model can follow the Cadence procedure at all. The pilot below finds out.
- Haiku 4.5 alone delivered 1 of 3 tasks, with quality 3.50 on that one. A cheap model alone does not reach Opus. The open question is how
  much of that gap a plan, independent review and verified fixes can close.

## Owner decisions for this design (2026-10-12)

- **No harness runs on Opus.** Opus 5.5 appears only as the one-shot bar. Every harness arm runs on a
  cheap model. The point is that a harness may spend many tokens, because on a model that costs
  pennies the token count does not matter; dollars per defect-free delivered run does.
- **The tasks must be harder.** On T04–T06, Opus alone finished in about 2 minutes with the top
  scores. Those tasks are too easy to show what a harness is for. The main run set uses class L and O
  tasks ([criteria §3](criteria.md#3-task-classes)), starting with the proposed
  [L3 open-data BI pipeline](tasks/L3-open-data-bi-pipeline.md). T05 stays as a quick pilot only.
- **Quality is measured by the published [quality model](quality-model.md)**, not by one grader's
  rubric, and every run must pass the [clean-room check](process.md#clean-room) before it is graded.
- **Two Cadence variants on the cheap model.** (a) *All cheap*: every stage, reviews included, runs on
  the arm's cheap model. (b) *Cheap + Opus reviews*: the cheap model plans and implements; the review
  peers (plan review, adversarial review, PR review, test benchmark) run on Opus 5.5, and their Opus tokens
  count in the arm's cost. Comparing (a) and (b) shows what Opus reviews add, per dollar.
- **A harness run is never cut off.** Harness arms have no per-trial time cap. A Cadence run took
  54–68 minutes in iteration 4, and criteria v1's 1800 s cap would have scored every one as not
  delivered. Spend is controlled by a budget for the whole run set, recorded before it starts, not by
  stopping a trial. (One-shot arms keep a generous time cap only as a guard against a hung session. The cap is recorded
  in the criteria, and a one-shot that hits it is reported separately, not mixed with other failures.)
- **Cursor CLI and OpenAI arms.** The Cursor CLI runs in `auto` mode (Cursor picks the model) and on
  its cheapest models; the OpenAI arms use the cheapest tool-using models the account can call. Each
  of these runs with Cadence and alone.
- **Opus never orchestrates a Cadence run.** It appears only as the one-shot bar and as the reviewer in
  variant (b). Sonnet does not run a Cadence arm (the B01 review-loop rows below are a minimal harness, not Cadence). The lift of the harness is measured on the cheap models,
  against each model's own one-shot. The main claim is "cheap model + Cadence is not worse than the Opus
  one-shot".

## Task selection: calibrated against the bar (owner direction, 2026-10-13)

The pilot showed the problem again: on T05 the Opus 5.5 one-shot delivered a correct, tool-clean change in 111 seconds for $0.40. A task like that cannot show what a harness adds to Opus. A task is "hard" only when calibration shows it (the bar fails it, or the cheap one-shots fail it), not when it looks hard.

- **Calibration rule (revised 2026-10-14).** Each task is calibrated with clean-room tries of the Opus 5.5 one-shot and of the cheap one-shots, graded by the task's own acceptance check. A task enters the benchmark in one of the two classes defined below: a **beyond** task (the bar passes at most 1 of 3 tries) or a **lift** task (the bar is reliable and the cheap one-shots are not). A task that the bar and the cheap one-shots all pass reliably is dropped, however large it looks.
- **Real defects, not specified features.** Each task starts from a symptom or a product request, as a user would write it. It needs a running system to confirm (a database, a queue, a worker), and has more than one cause. Its existing tests stay green while the defect is present. The model of this class is a private brownfield bug: several stacked faults across services, hidden by passing mocked tests.
- **Implementation-agnostic grading.** The acceptance check observes the product outcome in the running stack (rows, alerts, responses), never function names that one fix happened to use.
- **Sources.**
  1. *Private brownfield tasks.* Real repositories that cannot be published. The benchmark publishes the scores and the grader design, not the code. B01 is the first.
  2. *Review-caught defects from Cadence's own history.* A first implementation passed its own tests, then a review found the bug (for example the closed-run `peer_models` defect in jtouley/cadence#62). The task is the original request; the hidden check is the behavior the review added.
  3. *A published hard set* (for example the public SWE-bench Pro split) for comparison with outside numbers, filtered by the same calibration rule.
- **Calibration records** are kept per task: the three tries, their cost and time, and the grader output. A task admitted as lift or beyond gets the harness arms; a dropped task does not.

| Task | Source | Opus 5.5 one-shot | Result |
|---|---|---|---|
| B01 | private brownfield bug (several stacked faults across services) | 10 of 10 passed, including a second defect on another entry point (mean 7.3 min, $1.29) | Not a "beyond" task. A **lift** task (see below). |

**Two task classes (revised 2026-10-14).** The owner's question is whether a cheap model, which does the tool calls and the writing, plus a harness can reach the bar's reliability for less. So a task qualifies in one of two ways:

- **Lift task:** the Opus one-shot is reliable and the cheap one-shots are not. Question: does a harness lift the cheap model to the bar's reliability, and at what cost?
- **Beyond task:** the Opus one-shot is unreliable. Question: does a harness raise reliability above the bar?

Reliability is measured over repeated runs (pass^k, k ≥ 3), not one pass: a one-shot that passes once says nothing about the next run.

**B01 so far (interim and unsourced; n is small).** B01 is private: its prompt, grader and run records are not in this repository, so nobody can check the numbers below from it. They come from the operator's local run records. The B01 runs ran on the host, not in a container, and workers from one run could outlive it and share a message broker with later runs (a known defect of the B01 calibration). Grader: the product outcome in the running stack, plus a second check for a defect on another entry point that the original human-assisted fix also missed. Costs are from token counts at `pricing.json` list prices. Haiku 5.5 costs use the base price, so they are lower bounds for requests above 100 K tokens.

| Arm | Main path fixed | Both defects fixed | Mean cost | Notes |
|---|---|---|---|---|
| Opus 5.5 one-shot | 10/10 | 10/10 | $1.29 | |
| Sonnet 5.5 one-shot | 4/5 | 1/5 | $0.39 | |
| Haiku 5.5 one-shot | 5/5 | 0/5 | $0.11 | |
| Haiku 5.5 + Opus review loop | 2/2 | 2/2 | $1.15 ($0.16 Haiku, $0.99 Opus) | minimal harness: cheap model works, an Opus subagent reviews in the running system, the cheap model fixes |
| Sonnet 5.5 + Opus review loop | 1/1 | 1/1 | $1.24 ($0.47 Sonnet, $0.77 Opus) | same |

Reading: in 2 of 2 Haiku runs and 1 of 1 Sonnet run, an Opus review loop fixed both defects, where the cheap one-shots fixed both in 0 of 5 and 1 of 5. That is a signal, not yet a reliability measure (pass^k needs k ≥ 3). It does not save money. The reviewer must run the stack to check the work, and that costs about as much as Opus doing the task. The open cost question is whether a cheaper reviewer (Sonnet reviewing Haiku) keeps the reliability. Runs were cut short by repeated Docker Desktop failures on the test host; two runs were set aside as invalid (Docker down during the run); their arms are not recorded here.

## Hypotheses

| # | Hypothesis | What would refute it |
|---|---|---|
| H1 | Cadence on a model at 1/10 of the Opus price per token or less has no more major or critical defects per run than the Opus one-shot, and delivers as often | Its defect rate or delivery rate is worse than the Opus one-shot's after 5 runs per task |
| H2 | It costs less per defect-free delivered run than the Opus one-shot, however many tokens it uses | Its dollars per defect-free delivered run are higher than the Opus one-shot's |
| H3 | It leaves a complete audit trail (M10) on every delivered run | Plans, independent reviews or closure records are missing, or do not match the delivered head |
| H4 | The harness closes more of the gap on hard tasks than on easy ones | Its defect gap to the Opus one-shot is no smaller on class L and O tasks than on T05 |
| H5 | Opus reviews on a cheap implementer cut escaped defects below the all-cheap variant, and still cost less per defect-free delivered run than the Opus one-shot | Variant (b) has no fewer escaped defects than (a), or costs more per defect-free delivered run than the Opus one-shot |

## Arms

Each harness arm has a one-shot arm on the same model ([criteria §2](criteria.md)), so the
harness effect and the model effect stay separate. Opus runs no harness arm by itself; it reviews in one
variant only.

| Tier | Host | Model (pinned at run time) | Harness arm | One-shot arm |
|---|---|---|---|---|
| Bar | Claude Code | Opus 5.5 | none | **Opus one-shot (the bar)** |
| Anthropic, cheapest | Claude Code | Haiku 5.5 | Cadence, all cheap | one-shot |
| Opus reviews | Claude Code | Haiku 5.5 implements, Opus 5.5 reviews | Cadence, cheap + Opus reviews | shares the Haiku 5.5 one-shot |
| Anthropic, cheap | Claude Code | Haiku 4.5 | Cadence | one-shot |
| Cursor | Cursor CLI (`cursor-agent`) | `auto` (Cursor picks the model) | Cadence | one-shot |
| Cursor, cheap | Cursor CLI | the cheapest models in `cursor-agent --list-models`, for example `gpt-5.4-mini-*`, `gemini-3.6-flash-*` to `gemini-3.8-flash-*`, `composer-2.5` | Cadence | one-shot |
| OpenAI, cheap | OpenAI API (an agent CLI or a small tool loop) | the cheapest tool-using OpenAI models the account can call (from the account's model list at run time) | Cadence (headless gate protocol) | one-shot |

Sonnet 5.5 costs half of Opus per token, so it is not a cheap arm. It joins only if no cheap arm
matches Opus, as a step to find where the line is.

**`auto` needs its own reporting.** In `auto` mode Cursor chooses the model per request, so the arm is
"whatever Cursor routes to", not one model. Record the model of each request where the CLI's JSON output
reports it, and the cost from Cursor's own usage accounting; when the model is not reported, say so. Cursor may route the harness
arm and the one-shot arm to different models, so report the models of both side by side. The
`auto` arm answers "what does the default Cursor experience give", and it is compared with the Opus
one-shot like any other arm.

The Cursor model ids above are names from `cursor-agent --list-models` on 2026-10-12. Pin the exact
id, its effort level and the CLI version in `frameworks.lock.json` at run time. Add each model's price
to `pricing.json` with its source and date before the run. No price is assumed in this document.

## What differs by host (read before comparing hosts)

| Property | Claude Code | Cursor CLI | OpenAI API / other CLI |
|---|---|---|---|
| Cadence hooks enforce the gates | yes (`hooks/hooks.json`) | to verify: `cursor-agent` must load `~/.cursor/hooks.json` in `--print` mode | no hooks: the [headless gate protocol](https://github.com/jtouley/cadence/blob/main/SKILL.md) runs the checks as commands |
| Peer verdicts attested (a separate agent wrote each review) | yes (`agent_id` on each write) | no: Cursor sends no agent id, so the gates fall back to provenance records | no |
| Token and cost accounting | `claude -p --output-format json` reports usage and cost | to verify: `--output-format json` usage fields | the API response reports usage |

Auditability (M10) is therefore strongest on Claude Code. Report it per host, and do not compare
an attested Claude Code trail with an unattested one as if they were equal.

## Measures

The [criteria v1](criteria.md#4-measures) measures, with these points stressed for this question:

- **M1 acceptance** gates delivery. **M2 reproduced defects** decide "matches Opus". The other layers of
  the [quality model](quality-model.md) (the tool gate and the design checklist) are reported beside it.
- **M9 cost in dollars**: input, output and cache tokens of the whole session, nested subagents
  included, priced from `pricing.json`. Iterations 3 and 4 did not record this split. This run must.
- **M10 auditability**, scored as a checklist per run: a plan; a spec check; a plan review, an
  adversarial review and a PR review, each by an agent other than the implementer; a findings ledger
  where each must-fix finding has a verification; a closure record that names the delivered head.
  Report the share of items present, by host.
- **M3 false success**: a run that claims success while M1 or M2 shows failure. A harness that stops
  with a recorded reason is not a false success.

## Decision rule for this question

The rule is criteria v1 §6 ([decision rule](criteria.md#6-decision-rule-pre-registered)), applied to
each harness arm against the **Opus one-shot** instead of a one-shot on its own model. A harness arm on
a cheaper model **matches Opus** when all of these hold:

1. **Defects (non-inferiority):** its mean count of test-confirmed escaped defects per attempted run is
   at most the Opus one-shot's plus a margin, and the 90% bootstrap interval of the difference stays
   under that margin. The margin is fixed in the criteria before the run set; this proposal suggests 0.25
   defects per run. With 5 runs per task the interval is coarse, and when both arms have no defects it is
   [0, 0], which counts as "not worse": report the per-run counts beside it. (Criteria v1 asks for 0.5 fewer to show "fewer defects". "Matches" asks for "not
   worse by more than the margin".)
2. **No more false success:** its M3 rate is not higher than the Opus one-shot's (tolerance 0.05).
3. **Delivery:** its M1 pass rate per attempted run is at least the Opus one-shot's minus 10 points.

Among the arms that match, the answer is the one with the lowest **cost per defect-free delivered run**
(M9 dollars divided by the attempted runs that pass M1 with no critical or major defect). M7 quality and
M10 auditability are reported beside it. They do not decide. If no arm matches, the answer is "none yet",
and the harness case rests on auditability and enforcement. Each arm is also compared with the one-shot
on its own model, as criteria v1 requires, so the harness effect and the model effect stay separate.

**Caps (owner decision, 2026-10-12).** Harness arms have no per-trial time cap: a harness run is never
cut off. Criteria v1's 1800 s cap would have scored every iteration-4 Cadence run (3,266–4,061 s) as not
delivered. Spend is controlled by one budget for the run set, recorded in the criteria before the first
run; the run set stops scheduling new trials when the budget is spent, and never stops a trial in
progress. This changes criteria v1 §6 and is part of the next criteria version, with a changelog entry.

## Plan

| Stage | What | Size | Exit |
|---|---|---|---|
| 0. Prerequisites | See the list below | none | Each item has a test or a recorded check |
| 1. Pilot | T05 (budgets: the only task where every one-shot shipped a crash) only, n = 1, every arm | ~13 runs | Drop an arm that cannot follow the Cadence procedure at all. Keep the rest. The pilot decides nothing else |
| 2. Hard tasks | Tasks admitted as lift or beyond tasks (see "Task selection"): B01 (lift) and the other real-defect tasks first, then the [L3 open-data BI pipeline](tasks/L3-open-data-bi-pipeline.md) if calibration admits it. n = 5, the arms that passed the pilot, plus the Opus bar | ≤ 195 runs | The decision rule above, per task and per class |
| 3. Easy tasks, for contrast | T04–T06, n = 5, the same arms | ≤ 195 runs | Tests H4: does the harness matter more on hard tasks |

## Prerequisites (stage 0)

1. **Caps.** Record the run-set budget, and the removal of the per-trial time cap for harness arms, in the
   next criteria version (see above).
2. **Cost capture.** Record input, output and cache tokens and dollars for the whole session, nested
   subagents included, from the host's own accounting. Verify that this includes the harness's peers.
3. **Clean room per run, checked.** Each run gets a clean `HOME` with only its arm's own harness
   installed: no user-level skill, rule, command or memory. That keeps a user-level skill from taking
   the place of a Cadence peer (cadence#53) and keeps skill descriptions such as "strict TDD" away from
   the one-shot baselines. [`scripts/clean_room_check.py`](../scripts/clean_room_check.py) reads each
   transcript and must return `clean` before the run is graded ([process](process.md#clean-room)). The
   Harbor tier already gives a clean container; Claude Code and Cursor CLI runs need it set up.
4. **Cadence on cheap models, with a per-stage model setting.** Check that Haiku 5.5 can follow the
   Cadence procedure end to end (the pilot). Cadence needs a setting that names the model of each peer
   stage, so variant (a) keeps every stage on the cheap model and variant (b) sends only the review peers
   to Opus (jtouley/cadence#58). Today every peer inherits the host's model. The cost accounting must split the session's tokens
   by model, so each model's tokens are priced at its own price.
5. **Cursor CLI validation.** Confirm that `cursor-agent --print` runs Cadence's Cursor hooks. This
   also closes the README limitation "No Cursor binary was available to validate them".
6. **OpenAI host.** Pick the agent runner (an OpenAI-capable coding CLI or a small tool loop over the
   API), pin it, and run Cadence through the headless gate protocol.
7. **Two graders and a repro script** (criteria §5): each reproduced defect re-runs in a clean copy.
8. **Prices** for every model in `pricing.json`, with source and date.

## What we will report

- One table per task: arm, model, host, delivered, M2 defects by severity, M3, cost per defect-free
  delivered run, M7, M10 share, completion.
- A cost and quality chart with the Opus one-shot as the reference point.
- The answer to the question, by the decision rule, including "none yet" if that is the result.
- Every result that goes against the harness, reported the same way as a result for it.
