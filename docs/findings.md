# What a harness buys you: findings so far (October 2026)

This page answers one question with the data this repository has: **when is a plan-to-PR
harness worth running instead of handing the task to one strong model?** It sums up two
exploratory rounds on tasks T04–T06 ([iteration 3](experiments/2026-10-10-harness-vs-oneshot.md),
[iteration 4](experiments/2026-10-12-iteration-4.md)) and the deterministic tiers 1–2
([`results/REPORT.md`](../results/REPORT.md)). Each claim links to its evidence. Each limit is
stated next to the claim it limits.

> **Short answer.** On small, precisely specified tasks, a strong model alone writes code as good
> as a harness, about 30 times faster. A harness does not buy better average code there. It buys
> four other things: **evidence you can audit, completion you can trust, review of the edge cases
> the author misses, and rules the model cannot skip.** Those four things matter more as models
> get stronger and more expensive, because they let you check a stronger model and swap in a
> cheaper one. The next experiment ([next steps](next-steps.md)) tests that second claim directly.

## The numbers in one table

Iteration 4. Three feature tasks, one run per cell, blind Opus grader (1–10, mean of design,
correctness, readability and tests). Time is mean wall time per task.

| Arm | Delivered | Hidden tests | Blind quality | Time | Tokens | Audit trail |
|---|---|---|---|---|---|---|
| Opus one-shot | 3 of 3 | 19/19 | **8.00** | 2 min | 69k | 1 commit, nothing else |
| ship-feature (Opus) | 2 of 3 | 13/19 | 7.88 (2 tasks) | 42 min | 212k | plan and reviews, no ledger |
| **Cadence (Opus)** | **3 of 3** | **19/19** | 7.33 | 63 min | 279k | **plan, 6 reviews, verified findings ledger, peer attestations, 16 gate records per run** |
| Sonnet one-shot | 3 of 3 | 19/19 | 7.08 | 2 min | 64k | 1 commit, nothing else |
| Haiku 4.5 one-shot | 3 of 3 | 17/19 | 3.25 | 4 min | 71k | 2 of 3 runs did not commit |

List prices per million tokens (input / output, [`pricing.json`](../pricing.json), 2026-10-08):
Opus 5.5 $4 / $20, Sonnet 5.5 $2 / $10, Haiku 4.5 $1 / $5, **Haiku 5.5 $0.10 / $0.50**. These runs
did not record the input, output and cache split, so they report tokens, not dollars.

## What we got from Cadence

| What | Evidence |
|---|---|
| **It finished every task, with evidence for every step.** 3 of 3 in both rounds (after the fix in cadence#57). All gates A1–R7 passed. 10/10 process checks on both reruns. | [iteration 4 results](experiments/2026-10-12-iteration-4.md#results), [`results.json`](experiments/2026-10-12-iteration-4/results.json) |
| **An audit trail a reviewer can check without trusting the model.** Per run: a plan, a spec check, a plan review, an adversarial review, two test scorecards, a PR review, 12–23 attestation rows that prove a separate peer wrote each verdict, 16 gate records, and a findings ledger where 6 of 6 must-fix findings closed with a verification command. | [`auditability.json`](experiments/2026-10-12-iteration-4/auditability.json) |
| **Review caught defects that the author missed, before delivery.** Cadence's own R1 and R2 peers raised must-fix findings and verified each fix: a README example that failed (`--base EUR`), a CSV header that switched the currency check off, a store value that crashed with a traceback. The same class of defect shipped in the one-shot solutions (NaN amount traceback and tiny-limit crash in Opus budgets). | Cadence ledgers in [`cadence_ledgers/`](experiments/2026-10-12-iteration-4/cadence_ledgers/), one-shot defects in [`blind_scores/budgets.json`](experiments/2026-10-12-iteration-4/blind_scores/budgets.json) |
| **Better results on the specs with the most edge cases.** Budgets (iteration 4): both harnesses 7.75, beating Opus (7.25), Sonnet (6.25) and Haiku (3.5) alone. Audit-undo (iteration 3): Cadence 8.5 and ship-feature 8.25 against Sonnet 6.25 and Haiku 2.25. | [iteration 4](experiments/2026-10-12-iteration-4.md#findings), [iteration 3](experiments/2026-10-10-harness-vs-oneshot.md#findings) |
| **It failed loudly, not silently.** When a Cadence defect (cadence#56) broke two runs, both stopped with a recorded hard stop and the reason. Neither reported success. No one-shot arm has a way to say "I could not prove this". | [iteration 4, finding 5](experiments/2026-10-12-iteration-4.md#findings) |
| **Rules the model cannot skip.** Cadence's installed hooks block a forged approval, a self-certified verdict, a shell edit before plan approval and a stop mid-run: 7 of 9 probes. A one-shot session enforces none of these. | [README tier-2 table](../README.md#benchmark-results-october-2026), [`results/probes.json`](../results/probes.json) |

## What we did not get from Cadence

| What | Evidence |
|---|---|
| **Better average code than the same model alone.** Opus one-shot 8.00, Cadence 7.33. On 2 of 3 tasks Opus alone scored higher. | [iteration 4 results](experiments/2026-10-12-iteration-4.md#results) |
| **Restraint.** In both rounds the graders marked Cadence down for building beyond the spec: overflow handling, header normalization, a store version bump, an inverse-rate fallback. "Over-built for this change" (audit-undo, iteration 4). | [`blind_scores/`](experiments/2026-10-12-iteration-4/blind_scores/) |
| **Speed or low cost.** About 30 times the wall time and 4 times the tokens of a one-shot, on tasks a one-shot finishes in 2 minutes. | [iteration 4 results](experiments/2026-10-12-iteration-4.md#results) |
| **Freedom from its own defects.** #52 added a defect (#56) that broke 2 of 3 runs until #57 fixed it. The harness is software, and it needs the same review it gives. | cadence#56, cadence#57 |
| **Independence from the host setup.** User-level skills with the same names took the place of Cadence's review peers (cadence#53). The orchestrators had to correct each peer. | [iteration 4 confounds](experiments/2026-10-12-iteration-4.md#confounds-and-limits-read-before-citing) |

## What one-shotting gave, and what it did not

| Gave | Did not give |
|---|---|
| Opus alone: the best average code on precise specs (8.00), in 2 minutes. | No plan, no review, no record of what it checked. You must re-review the work yourself. |
| Sonnet alone: 7.08, close to the harnesses on precise specs. | Edge cases: Opus and Sonnet budgets shipped crashes and wrong alerts that a grader reproduced in one command each. |
| Low cost per run. | No completion signal you can trust: two Haiku runs never committed, and a one-shot cannot report "not done". |
| | Haiku 4.5 alone is not usable here (3.25): spec failures that hidden tests miss. Cheap models alone do not reach Opus. |

## Why this still matters as models get stronger and more expensive

1. **A stronger model writes more code that someone must trust.** The one-shot arms give you
   output. Cadence gives you output plus a verified ledger, independent reviews and gate records.
   As models improve, the cost of reviewing their output does not go away. A harness moves that
   cost from a human reading code to a human reading evidence.
2. **The price gap between models is 40 times.** Opus 5.5 costs 40 times Haiku 5.5 per token. A
   harness spends more tokens on purpose: planning, independent review, verification. If those
   tokens let a cheap model reach Opus quality with an audit trail, the harness becomes the cheaper
   option. **This is a hypothesis, not a result.** Nobody has run Cadence on a cheap model yet. It is
   the subject of [next steps](next-steps.md).
3. **Small, precise tasks are the easy case.** All six data points here are class S tasks
   ([criteria §3](criteria.md)), where a model alone should do well. Repository-scale work with open
   design choices (class L) and work where a wrong answer looks right (class O) are where review and
   evidence should matter most. Those tasks are not run yet.

## What would change these conclusions

- **More runs.** Each cell ran once. Criteria v1 requires 5 runs per cell and two graders. A gap
  under about 1 quality point is noise.
- **Class L and O tasks.** If a harness does not beat a one-shot there, the case for it rests only
  on auditability and enforcement.
- **A cheap-model harness arm.** If Cadence on Haiku 5.5 or Sonnet matches Opus alone, the cost
  argument holds. If it does not, the harness is a governance tool, not a cost tool.

## Sources

- [Iteration 4 write-up](experiments/2026-10-12-iteration-4.md) and [data](experiments/2026-10-12-iteration-4/)
- [Iteration 3 write-up](experiments/2026-10-10-harness-vs-oneshot.md) and [data](experiments/2026-10-10-harness-vs-oneshot.json)
- [How the experiments were run](process.md)
- [20-minute talk track](talk.md)
- [Next steps: the cheapest model that matches Opus](next-steps.md)
- [Criteria v1](criteria.md)
