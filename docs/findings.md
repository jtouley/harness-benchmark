# What a harness buys you: findings so far (October 2026)

This page answers one question with the data this repository has: **when is a plan-to-PR
harness worth running instead of handing the task to one strong model?** It sums up two
exploratory rounds on tasks T04–T06 ([iteration 3](experiments/2026-10-10-harness-vs-oneshot.md),
[iteration 4](experiments/2026-10-12-iteration-4.md)) and the deterministic tiers 1–2
([`results/REPORT.md`](../results/REPORT.md)). Each claim links to its evidence. Each limit is
stated next to the claim it limits.

> **Disclosure.** The owner of this benchmark wrote Cadence, one of the harnesses measured here
> ([criteria v1](criteria.md#disclosure)). That is why the main result below, which does not favor
> Cadence, is stated first.

> **Update, 16 October 2026: the thesis, checked against the data.** Harnesses do not make strong
> models write better code. On well-specified tasks a one-shot matched the harness at about 1/30 of the
> time. What a harness buys is verification and accountability: an independent review of the running
> result recovered a bug that the cheap models missed (1 of 10 cheap one-shot runs fixed both B01 defects,
> against 3 of 3 with an Opus review loop; Haiku and Sonnet pooled; Fisher exact test, one-sided,
> p ≈ 0.014; small samples), and the first review round found most of the confirmed defects
> ([review value](review-value.md)). A long planning pipeline did not help: on a cheap model it stalled
> before it wrote code. Precise specs are why the one-shot did well; specs as executable contracts are
> not tested yet. Also new: the Haiku 5.5 dollar figures below are lower bounds (see
> [next steps](next-steps.md#cost-accounting-price-each-request-at-its-own-tier-planned-2026-10-16)), and
> Cadence has changed since the pinned commit ([whitepaper §4.1](whitepaper.md#41-cadence-after-the-benchmarks-pin-status-16-october-2026)).

> **Update, 14 October 2026.** Four newer results are summarized in
> [Since iteration 4](#since-iteration-4) and argued in full in the [whitepaper](whitepaper.md):
> Cadence on Haiku 5.5 delivered nothing in the pilot; on a real multi-cause bug the cheap one-shots
> fix the main path and miss the second defect, and an independent review loop recovered it in 2/2 Haiku
> and 1/1 Sonnet runs (a signal) at about the Opus one-shot's cost; the cheap models miss by scope narrowing and coverage, not by
> reasoning depth; and on a 20-task SWE-bench Pro sample (one try per model), a one-shot Haiku 5.5
> passed 17 against Opus 5.5's 18 at about one tenth of the cost, so those tasks are not lift candidates
> for a harness.

> **Short answer (iteration 4).** On small, precisely specified tasks, a harness did **not** show better code
> than a strong model alone, and it took about 30 times longer. What it did show is
> narrower and concrete: **no crash reached its delivered code** (each one-shot shipped two; all six are
> on one task, budgets, from three inputs),
> **an audit trail a reviewer can check**, **completion on every task, or a recorded stop**, and
> **rules the model cannot skip**. Whether a harness lets a much cheaper model match Opus is the
> next experiment ([next steps](next-steps.md)), not a result.

## How to read these numbers

Each cell ran **once**, with **one** blind grader. The docs treat a quality gap under about 1 point
as noise. Criteria v1 requires 5 runs per cell and two graders before any claim. "Delivered" means
the run passed every hidden test (M1), as [criteria v1](criteria.md#4-measures) defines it.

## The numbers in one table

Iteration 4. Quality is the blind mean (1–10) over delivered runs only. Defects are reproduced by
the grader. Their severity is assigned from the grader's text by a written rule
([`defects.json`](experiments/2026-10-12-iteration-4/defects.json)). One call is borderline: ship-feature's
multicurrency change no longer loads a hand-edited old ledger file with a JSON-number amount. We
labeled it minor, because ledgerlite never writes that shape. As major, it raises ship-feature to
1.00 and leaves Cadence unchanged.

| Arm | Delivered (M1) | Blind quality | Major or critical defects per attempted run | Crashes in delivered code | Time per task | Audit trail |
|---|---|---|---|---|---|---|
| Opus 5.5 one-shot | 3 of 3 | 8.00 | 1.00 | 2 | 2 min | 1 commit |
| ship-feature (Opus) | 2 of 3 | 7.88 | 0.67 | 0 | 42 min | plan and reviews |
| Cadence (Opus) | 3 of 3 | 7.33 | 0.67 | 0 | 63 min | plan, 6 reviews by separate agents, verified ledger, attestations |
| Sonnet 5.5 one-shot | 3 of 3 | 7.08 | 1.33 | 2 | 2 min | 1 commit |
| Haiku 4.5 one-shot | 1 of 3 | 3.50 (1 task) | 2.67 | 2 | 4 min | 2 of 3 runs did not commit |

List prices per million tokens (input / output, [`pricing.json`](../pricing.json), 2026-10-08):
Opus 5.5 $4 / $20, Sonnet 5.5 $2 / $10, Haiku 4.5 $1 / $5, Haiku 5.5 $0.10 / $0.50 (for prompts up to
100K tokens; $0.50 / $2.50 above that; its cache prices are derived, not listed). These runs did not
record the input, output and cache split, so they report tokens, not dollars.

## Since iteration 4

| Round | Result | Evidence |
|---|---|---|
| **Pilot** (T05, clean room, one run per arm) | The Opus one-shot delivered in 111 s for $0.40 (7/7 hidden tests, quality gate passed). Cadence on Haiku 5.5 hard-stopped at P6 after four plan updates ($1.13, 75 min); Cadence on Haiku with Opus reviews hard-stopped at P9 ($3.19, 27 min). Both costs are lower bounds (up to $5.66 and $4.50): each orchestrator ended above 100K prompt tokens, where Haiku 5.5 costs 5 times more. A full harness on a weak orchestrator adds places to stop. Four Cadence defects filed (cadence#63–#66); #63 and #64 are fixed, #65 and #66 are open. | [pilot](experiments/2026-10-13-pilot.md) |
| **Calibration rule** | Tasks are chosen by what the Opus one-shot does on them: a *lift* task (Opus reliable, cheap one-shots not) or a *beyond* task (Opus unreliable). Reliability is measured over repeats. | [next steps](next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13) |
| **B01**, a private multi-service bug (lift task) | Both defects fixed: Opus one-shot 10/10 ($1.29), Sonnet 1/5 ($0.39), Haiku 0/5 ($0.11). Review loop with an Opus reviewer: Haiku 2/2 ($1.15), Sonnet 1/1 ($1.24). Haiku 5.5 costs are lower bounds (base price only). A signal that reliability can be recovered, not yet a reliability measure (pass^k needs k ≥ 3); two more runs were set aside as invalid (Docker down during the run). No money saved. | [whitepaper §3.3](whitepaper.md#33-a-real-multi-cause-bug-b01-a-lift-task) |
| **Why cheap models miss** | Haiku hit the second defect in 5/5 runs and diagnosed it correctly once; in that run it chose to "leave that out of this change and report it", and did not report it. Sonnet never exercised that path in 4/5. Haiku took more turns than Opus (166 against 90). | [whitepaper §3.4](whitepaper.md#34-why-the-cheap-models-miss) |
| **SWE-bench Pro** (20 sampled tasks, one try per model) | One-shots passed: Opus 5.5 18/20 ($5.79), Sonnet 5.5 18/20 ($2.57), Haiku 5.5 17/20 ($0.54, a lower bound). Haiku is within one task of Opus at about one tenth of the cost (at most about half, if every Haiku request were above 100K), so these tasks are not lift candidates for a harness. Two tasks passed only 2 of 5 Opus tries (beyond candidates). Limits: 20 tasks, one try per model, setup failures rerun (the model never ran in them). Open: the beyond tasks and reliability over repeats (pass^k), not single-pass rates. | [calibration](../calibration/README.md), [per task](../calibration/swebench-pro/round2.md) |

## What we got from Cadence

| What | Evidence | Limit |
|---|---|---|
| **No crash in the delivered code.** Neither harness shipped a traceback. Opus, Sonnet and Haiku alone each shipped two, all on budgets (a NaN amount, a tiny limit, a NaN limit). | [`defects.json`](experiments/2026-10-12-iteration-4/defects.json), [`blind_scores/budgets.json`](experiments/2026-10-12-iteration-4/blind_scores/budgets.json) | Major or critical defects per run: Cadence 0.67, Opus 1.00. That gap (0.33) is under the 0.5 bar of the pre-registered rule, so "fewer defects" is **not shown**. |
| **Review caught defects before delivery, with a record.** Cadence's peers raised 6 must-fix findings across 3 runs, and each was fixed and verified by a command: a README example that failed (`--base EUR`), a CSV header that switched the currency check off, a stored limit that crashed with a traceback. | [`cadence_ledgers/`](experiments/2026-10-12-iteration-4/cadence_ledgers/) | Cadence still shipped two major defects that its reviews did not catch (a duplicate alert, an unlogged empty import). |
| **An audit trail a reviewer can check without trusting the model.** Per run: a plan, a spec check, a plan review, an adversarial review, two test scorecards, a PR review, and a findings ledger. 12–23 attestation rows per run record the hash of each review file and the agent that wrote it (8–12 different peer agents per run). The hook denies a review write by the orchestrator, so the implementer cannot be its own reviewer. 16 gate records per run. | [`auditability.json`](experiments/2026-10-12-iteration-4/auditability.json), [`cadence_attest/`](experiments/2026-10-12-iteration-4/cadence_attest/) | The attestation is a Claude Code feature. On Cursor and other hosts the trail has no agent ids ([next steps](next-steps.md#what-differs-by-host-read-before-comparing-hosts)). |
| **It finished every task, or it stopped and said why.** 3 of 3 delivered in both rounds (iteration 4 after cadence#57). 10/10 process checks on both reruns. When a Cadence defect (cadence#56) broke two runs, both stopped with a recorded reason, and neither reported success. | [iteration 4](experiments/2026-10-12-iteration-4.md#results) | ship-feature, the other harness, failed to deliver 1 of 3 tasks in each round. |
| **Rules the model cannot skip.** Cadence's installed hooks block a forged approval, a self-certified verdict, a shell edit before plan approval and a stop mid-run: 7 of 9 probes. A one-shot session enforces none of these. | [README tier-2 table](../README.md#benchmark-results-october-2026), [`results/probes.json`](../results/probes.json) | The probes test the hooks, not code quality. |

More process evidence for review (16 October 2026, outside the benchmark): independent reviews of two
Cadence PRs found 5 and 4 must-fix defects (as of the rounds read), and two of them were caused by fixes of
earlier review nits ([review value](review-value.md#independent-reviews-of-two-cadence-prs-16-october-2026)).

## What we did not get from Cadence

| What | Evidence |
|---|---|
| **Better code than the same model alone.** Opus alone 8.00, Cadence 7.33. Per task the gaps are +2.0 (multicurrency, Opus better), −0.5 (budgets, Cadence better) and +0.5 (audit-undo, Opus better). Only multicurrency is outside the noise band. The supported statement is "no quality gain shown", not "a quality loss". | [`results.json`](experiments/2026-10-12-iteration-4/results.json) |
| **Fewer defects under the pre-registered rule.** 0.67 against 1.00 major or critical defects per run: a 0.33 gap, under the 0.5 bar, on one run per cell. | [`defects.json`](experiments/2026-10-12-iteration-4/defects.json), [criteria §6](criteria.md#6-decision-rule-pre-registered) |
| **Restraint.** In both rounds the graders marked Cadence down for building beyond the spec: overflow handling, header normalization, a store version bump, a duplicate-sequence guard, a clock seam. The audit-undo grader called it "very robust" but "heavier than needed". | [`blind_scores/`](experiments/2026-10-12-iteration-4/blind_scores/) |
| **Simpler code by the tools: not shown.** On the proposed [quality model](quality-model.md)'s tool gate (new-code coverage, cognitive and cyclomatic complexity, new bug findings, new type errors; measured before the duplication check was added to the gate, so these counts do not include it), Opus alone passed on 3 of 3 tasks and Cadence on 1 of 3: one function at cognitive complexity 19, and one new type error. But the task authors' own reference solutions pass on only 1 of 3: adding a subcommand takes the CLI dispatcher (cyclomatic 7 in the baseline) over 10. So on these tasks the gate mostly shows whether a solution refactored the dispatcher, and it does not yet separate good solutions from bad ones. Cadence's tests do reach more branches (91–93% against 82–89%). | [`quality_metrics.json`](experiments/2026-10-12-iteration-4/quality_metrics.json) |
| **Speed or low cost.** About 30 times the wall time and 4 times the tokens of a one-shot, on tasks a one-shot finishes in 2 minutes. | [`results.json`](experiments/2026-10-12-iteration-4/results.json) |
| **Freedom from its own defects.** cadence#52 added a defect (cadence#56) that broke 2 of 3 runs until cadence#57 fixed it. The harness is software, and it needs the review it gives. | cadence#56, cadence#57 |
| **Independence from the host setup.** User-level skills with the same names took the place of Cadence's review peers (cadence#53). The orchestrators had to correct each peer. | [iteration 4 confounds](experiments/2026-10-12-iteration-4.md#confounds-and-limits-read-before-citing) |

## What one-shotting gave, and what it did not

| Gave | Did not give |
|---|---|
| Opus alone: the highest quality score (8.00), in 2 minutes, with every hidden test passed. | No plan, no review, no record of what was checked. A person must re-review the code. |
| Sonnet alone: 7.08, every hidden test passed, in 2 minutes. | The edge cases: Opus and Sonnet both shipped two crashes on budgets, each reproduced by one command. |
| Low cost per run. | A signal you can trust: two Haiku runs never committed their work, and a one-shot has no way to report "not done" or "not proven". |
| | Haiku 4.5 alone delivered 1 of 3 tasks (3.50 on the one it delivered). A cheap model alone does not reach Opus. |

## Why this still matters as models get stronger and more expensive

1. **A stronger model writes more code that someone must trust.** A one-shot gives you code. Cadence
   gives you code plus a ledger, reviews by agents that did not write it, and gate records. Better
   models do not remove the need to check their work. A harness changes what a person checks: the
   evidence, not every line.
2. **Prices differ by up to 40 times per token.** Opus 5.5 costs 40 times Haiku 5.5 for prompts up to
   100K tokens, and 8 times above that. Harness orchestrators can run above 100K: both pilot Cadence
   orchestrators ended there. A harness spends extra tokens on purpose: planning, independent review, verification.
   If those tokens let a cheap model reach Opus quality with an audit trail, the harness becomes the
   cheaper option. The first measurements ([since iteration 4](#since-iteration-4)) say: not the full
   Cadence pipeline on Haiku (it stopped before implementing), but an independent review of the running
   result does recover the cheap model's misses, so far at about the Opus one-shot's cost. The open
   question is whether that verification can itself be cheap ([whitepaper](whitepaper.md#6-what-comes-next)).
3. **Small, precise tasks are the easy case.** All the data here comes from class S tasks
   ([criteria §3](criteria.md#3-task-classes)), where a model alone should do well. Repository-scale
   work with open design choices (class L), and work where a wrong answer looks right (class O), are
   where review and evidence should matter most. Those tasks are not run yet.

## About iteration 3

Iteration 3 scored the harnesses above Sonnet and Haiku alone on audit-undo (Cadence 8.5,
ship-feature 8.25, Sonnet 6.25). That round had no Opus one-shot, so it cannot separate the harness
from the model, and its Cadence audit-undo run reviewed its own work. In iteration 4, Opus alone
scored 8.00 on the same task, against Cadence's 7.50. Iteration 3 is evidence that Opus beats Sonnet
and Haiku on that task. It is not evidence for a harness.

## What would change these conclusions

- **A clean-room baseline.** The one-shots could see the user-level skill list, which describes TDD.
  None used a skill, but the descriptions may have primed them. The next run set gates on
  [`clean_room_check.py`](../scripts/clean_room_check.py).
- **Harder tasks.** Opus alone did these tasks in about 2 minutes. Tasks are now chosen by calibration
  against the Opus one-shot (class L and O tasks), and the long-horizon set is the
  [pipeline family](tasks/pipeline-family.md) (one spec on three stacks, with a follow-up change and a
  traceability audit; it supersedes L3). The harness also runs on cheap models, all cheap and with Opus as
  reviewer only ([next steps](next-steps.md)).
- **More runs and a second grader.** Each cell ran once. Apart from Haiku's results and the 2.0-point
  quality gap on multicurrency, every gap here is within single-run noise.
- **Class L and O tasks.** If a harness does not reduce defects there, the case for it rests on
  auditability and enforcement only.
- **A cheap verification arm.** The pilot answered the first form of this question (full Cadence on Haiku
  did not deliver). If a Haiku-only verification harness (contracts before code and a stop gate, or a
  Haiku reviewer) matches Opus alone on lift tasks, the cost argument holds. If it does not, the harness
  is a governance tool, not a cost tool.

## Sources

- [Iteration 4 write-up](experiments/2026-10-12-iteration-4.md) and [data](experiments/2026-10-12-iteration-4/)
- [Iteration 3 write-up](experiments/2026-10-10-harness-vs-oneshot.md) and [data](experiments/2026-10-10-harness-vs-oneshot.json)
- [How the experiments were run](process.md)
- [20-minute talk track](talk.md)
- [Next steps: the cheapest model that matches Opus](next-steps.md)
- [Criteria v1](criteria.md)
