# Harnesses against one-shotting: what a harness is for when the model is this good

*Whitepaper, version 1, 14 October 2026; updated 18 October 2026 (absorbs the former `findings.md`).
Benchmark: jtouley/harness-benchmark.*

> **Disclosure.** The author of this benchmark wrote Cadence, one of the harnesses measured. The
> results below that do not favor Cadence are stated first, and every number links to its data.

## Abstract

We asked when a plan-to-PR harness is worth running instead of handing a task to one strong model.
Over four rounds of measurement, the answer moved twice.

1. **On small, fully specified tasks, a harness does not write better code.** Opus 5.5 alone scored
   8.00 of 10 against 7.33 for Cadence on Opus, in about 1/30 of the time (iteration 4, one run per
   cell). The harness did ship no crashes (each one-shot shipped two, all six on one task, budgets, from
   three inputs) and left an audit trail.
2. **A full harness does not make a cheap model work.** Cadence orchestrated by Haiku 5.5 delivered
   nothing on a task that the Opus one-shot finished in 111 seconds for $0.40 (pilot, one run per arm).
   Its cost ($1.13 and $3.19) is a lower bound (§3.2).
   The run stopped in its own planning loop, or failed its own gates.
3. **On a real multi-cause bug, the cheap models do most of the work and miss the rest, and an
   independent review recovers it.** Opus alone fixed both defects of a brownfield bug in 10 runs of 10.
   Haiku alone fixed the main path in 5 of 5 and the second defect in 0 of 5. Sonnet fixed it in 1 of 5.
   A minimal review loop (the cheap model works, an independent reviewer checks the running system) fixed
   both in 2 of 2 Haiku runs and 1 of 1 Sonnet run, at about the Opus one-shot's cost. That is a signal,
   not yet a reliability measure.
4. **Why the cheap models miss is specific and fixable.** Haiku saw the second defect in every run,
   diagnosed it correctly once, then decided to "leave that out of this change and report it" and never
   reported it. Sonnet mostly never exercised that path. The gap is scope judgment and coverage, not
   reasoning depth. Haiku took more turns than Opus.
5. **On a published benchmark sample, the cheap one-shot is close to the strong one.** On 20 SWE-bench Pro
   tasks, one try per model, Opus 5.5 passed 18, Sonnet 5.5 18 and Haiku 5.5 17, and Haiku cost about one
   tenth of Opus. Those tasks leave a harness little to lift. Two tasks passed only 2 of 5 Opus tries; they,
   and reliability over repeats, are the open questions there.

Our current position (16 October 2026): **harnesses do not make strong models write better code.** On
well-specified tasks a one-shot matched the harness at about 1/30 of the time (§3.1). What a harness buys
is verification and accountability. An independent review of the running result recovered a bug that
the cheap models missed: 1 of 10 cheap one-shot runs fixed both defects, against 3 of 3 with an Opus review
loop (Haiku and Sonnet pooled; Fisher exact test, one-sided, p ≈ 0.014; small samples, §3.3). In our PR
reviews, the first review round found most of the confirmed defects (40 of 51, [review value](evidence/review-value.md)).
A long planning pipeline did not help: on a cheap model it stalled before it wrote code (§3.2). Precise specs
are why the one-shot did well. Specs as executable contracts are not tested yet.

In short: **a harness earns its cost by verification and by holding scope, not by
ceremony.** A planning pipeline on a weak model mostly adds places to stop. An independent check of the
running result, and a rule that no part of the request may be dropped silently, recover the cheap
model's misses. The open question is whether that check can itself be cheap. The next measures are
cost per defect-free run, traceability when a long task goes wrong, and design quality under a follow-up
change.

## 1. The question and why it matters

Models write code faster than people can check it. A one-shot from a strong model is often correct, and
when it is, it is fast and cheap. The case for a harness (a plan, independent reviews, gates, a record)
must rest on something a one-shot cannot give:

- **Evidence.** A record of what was planned, checked and decided, by agents that did not write the code.
- **Reliability over repeats.** A one-shot that passes once says nothing about the next run.
- **Cost.** Opus 5.5 costs 40 times Haiku 5.5 per token for prompts up to 100K tokens, and 8 times above
  that. Harness orchestrators can run above 100K: both pilot Cadence orchestrators ended there (§3.2). If a
  harness lets a cheap model reach the strong model's result, the extra tokens are cheap.

## 2. Method

- **Pre-registered criteria** ([criteria v1](method/criteria.md)): measures, sample size and a decision rule
  written before the runs.
- **A neutral one-shot baseline:** the same request, with the harness parts removed and nothing added.
- **A clean room** ([process](method/process.md#clean-room)): each run has an empty `HOME`, so user-level skills,
  rules and memory cannot prime or replace anything. A checker reads each transcript and must return
  `clean` before grading ([`clean_room_check.py`](../scripts/clean_room_check.py)).
- **A published quality model** ([quality model](method/quality-model.md)): ISO/IEC 25010 characteristics,
  measured by published tools and thresholds (coverage, cognitive and cyclomatic complexity, bug and
  type findings), blind defect review, and from now on duplication, coupling and a follow-up change.
- **Costs from token counts** at list prices ([`pricing.json`](../pricing.json)), because the host
  misprices models it does not know.
- **Task selection by calibration** ([next steps](plans/next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13)).
  A task is chosen by what the bar does on it, not by how hard it looks:
  - a **lift task**: the Opus one-shot is reliable and the cheap one-shots are not. Can a harness lift a
    cheap model to the bar for less?
  - a **beyond task**: the Opus one-shot is unreliable. Can a harness raise reliability at all?

## 3. Results

### 3.1 Small, fully specified tasks (iteration 4)

Three feature tasks on a 300-line Python ledger (T04–T06), one run per cell, one blind grader
([iteration 4](evidence/2026-10-12-iteration-4.md), [data](evidence/2026-10-12-iteration-4/)).
A quality gap under about 1 point is noise. "Delivered" means the run passed every hidden test (M1,
[criteria v1](method/criteria.md#4-measures)). Quality is the blind mean (1–10) over delivered runs only.

| Arm | Delivered | Blind quality | Major or critical defects per run | Crashes shipped | Time per task | Audit trail |
|---|---|---|---|---|---|---|
| Opus 5.5 one-shot | 3 of 3 | 8.00 | 1.00 | 2 | 2 min | 1 commit |
| ship-feature (Opus) | 2 of 3 | 7.88 (2 tasks) | 0.67 | 0 | 42 min | plan and reviews |
| Cadence (Opus) | 3 of 3 | 7.33 | 0.67 | 0 | 63 min | plan, 6 reviews by separate agents, verified ledger, attestations |
| Sonnet 5.5 one-shot | 3 of 3 | 7.08 | 1.33 | 2 | 2 min | 1 commit |
| Haiku 4.5 one-shot | 1 of 3 | 3.50 (1 task) | 2.67 | 2 | 4 min | 2 of 3 runs did not commit |

Defects are reproduced by the grader; severity is assigned from the grader's text by a written rule
([`defects.json`](evidence/2026-10-12-iteration-4/defects.json)). One call is borderline:
ship-feature's multicurrency change no longer loads a hand-edited old ledger file with a JSON-number
amount. It is labeled minor, because ledgerlite never writes that shape; as major, it raises
ship-feature to 1.00 and leaves Cadence unchanged. These runs did not record the input, output and cache
split, so they report tokens, not dollars.

**What the harness gave.**

| What | Evidence | Limit |
|---|---|---|
| **No crash in the delivered code.** Neither harness shipped a traceback. Opus, Sonnet and Haiku alone each shipped two, all on budgets (a NaN amount, a tiny limit, a NaN limit). | [`defects.json`](evidence/2026-10-12-iteration-4/defects.json), [`blind_scores/budgets.json`](evidence/2026-10-12-iteration-4/blind_scores/budgets.json) | Major or critical defects per run: Cadence 0.67, Opus 1.00. That gap (0.33) is under the 0.5 bar of the pre-registered rule, so "fewer defects" is **not shown**. |
| **Review caught defects before delivery, with a record.** Cadence's peers raised 6 must-fix findings across 3 runs, each fixed and verified by a command: a README example that failed (`--base EUR`), a CSV header that switched the currency check off, a stored limit that crashed with a traceback. | [`cadence_ledgers/`](evidence/2026-10-12-iteration-4/cadence_ledgers/) | Cadence still shipped two major defects that its reviews did not catch (a duplicate alert, an unlogged empty import). |
| **An audit trail a reviewer can check without trusting the model.** Per run: a plan, a spec check, a plan review, an adversarial review, two test scorecards, a PR review, and a findings ledger. 12–23 attestation rows per run record the hash of each review file and the agent that wrote it (8–12 different peer agents per run). The hook denies a review write by the orchestrator. 16 gate records per run. | [`auditability.json`](evidence/2026-10-12-iteration-4/auditability.json), [`cadence_attest/`](evidence/2026-10-12-iteration-4/cadence_attest/) | The attestation is a Claude Code feature. On other hosts the trail has no agent ids ([next steps](plans/next-steps.md#what-differs-by-host-read-before-comparing-hosts)). |
| **It finished every task, or it stopped and said why.** 3 of 3 delivered (after cadence#57). When a Cadence defect (cadence#56) broke two runs, both stopped with a recorded reason, and neither reported success. | [iteration 4](evidence/2026-10-12-iteration-4.md#results) | ship-feature failed to deliver 1 of 3 tasks in each round. |
| **Rules the model cannot skip.** Cadence's installed hooks block a forged approval, a self-certified verdict, a shell edit before plan approval and a stop mid-run (7 of 9 probes). A one-shot session enforces none of these. | [`results/probes.json`](../results/probes.json) | The probes test the hooks, not code quality. |

**What the harness did not give.**

| What | Evidence |
|---|---|
| **Better code than the same model alone.** Per task the gaps are +2.0 (multicurrency, Opus better), −0.5 (budgets, Cadence better) and +0.5 (audit-undo, Opus better). Only multicurrency is outside the noise band. The supported statement is "no quality gain shown", not "a quality loss". | [`results.json`](evidence/2026-10-12-iteration-4/results.json) |
| **Restraint.** The graders marked Cadence down for building beyond the spec: overflow handling, header normalization, a store version bump, a duplicate-sequence guard, a clock seam. | [`blind_scores/`](evidence/2026-10-12-iteration-4/blind_scores/) |
| **Simpler code by the tools: not shown.** On the [quality model](method/quality-model.md)'s tool gate (measured before duplication was added), Opus alone passed 3 of 3 tasks and Cadence 1 of 3. But the task authors' own reference solutions pass only 1 of 3, because adding a subcommand takes the CLI dispatcher over cyclomatic 10, so the gate does not yet separate good solutions from bad ones. Cadence's tests reach more branches (91–93% against 82–89%). | [`quality_metrics.json`](evidence/2026-10-12-iteration-4/quality_metrics.json) |
| **Speed or low cost.** About 30 times the wall time and 4 times the tokens of a one-shot. | [`results.json`](evidence/2026-10-12-iteration-4/results.json) |
| **Freedom from its own defects.** cadence#52 added a defect (cadence#56) that broke 2 of 3 runs until cadence#57 fixed it. | cadence#56, cadence#57 |
| **Independence from the host setup.** User-level skills with the same names took the place of Cadence's review peers (cadence#53). | [iteration 4 confounds](evidence/2026-10-12-iteration-4.md#confounds-and-limits-read-before-citing) |

**What one-shotting gave, and did not.** Opus alone had the highest score, every hidden test passed, in
2 minutes, but no plan, no review and no record of what was checked; a person must re-review the code.
Opus and Sonnet both shipped two crashes on budgets. Two Haiku 4.5 runs never committed their work, and a
one-shot has no way to report "not done" or "not proven".

**Iteration 3** ([write-up](evidence/2026-10-10-harness-vs-oneshot.md)) scored the harnesses above
Sonnet and Haiku alone on audit-undo (Cadence 8.5, ship-feature 8.25, Sonnet 6.25). It had no Opus
one-shot, so it cannot separate the harness from the model, and its Cadence run reviewed its own work. In
iteration 4 Opus alone scored 8.00 on the same task against Cadence's 7.50. Iteration 3 is not evidence
for a harness.

### 3.2 Cadence on a cheap model (pilot)

T05 (budgets), clean room, Cadence loaded with `--plugin-dir`, one run per arm
([pilot](evidence/2026-10-13-pilot.md)).

| Arm | Result | Time | Cost |
|---|---|---|---|
| Opus 5.5 one-shot | Delivered; 7/7 hidden tests; quality gate passed | 111 s | $0.40 |
| Cadence, all Haiku 5.5 | Hard stop at P6 after four plan updates | 75 min | $1.13 (lower bound; up to $5.66) |
| Cadence, Haiku 5.5 + Opus reviews | Hard stop at P9: no delegation records | 27 min | $3.19 (lower bound; up to $4.50) |

The Haiku 5.5 costs use the base price ($0.10 / $0.50 per million tokens) for every request. The last
orchestrator request of each Cadence arm was above 100K prompt tokens (111,736 and 156,578), where Haiku
5.5 costs 5 times more. The upper bound prices every Haiku token at the higher rate. The runs kept no
per-request records, so the true cost is not known; re-pricing is planned
([next steps](plans/next-steps.md#cost-accounting-price-each-request-at-its-own-tier-planned-2026-10-16)).
Static skill text does not explain the context size; one cause is that every peer returned a full report
into the orchestrator's context ([pilot follow-up](evidence/2026-10-13-pilot.md#follow-up-2026-10-16-why-the-orchestrators-context-was-large)).

The harness gave the cheap model more places to stop: a review loop with no cycle limit, and gates that
depend on the orchestrator recording its own delegations. Four Cadence defects were filed from this run
(cadence#63–#66).

### 3.3 A real multi-cause bug (B01, a lift task)

A private brownfield bug in a multi-service application. Several faults stack across services, and the
existing mocked tests hide some of them. The prompt is the original product request. The grader runs the real
stack and checks the product outcome: the main path, and a second entry point that the original
human-assisted fix also missed. The task's code is not published (it belongs to a third party); its
scores are.

| Arm | Main path fixed | Both defects fixed | Mean cost | Mean time |
|---|---|---|---|---|
| Opus 5.5 one-shot | 10/10 | 10/10 | $1.29 | 7.3 min |
| Sonnet 5.5 one-shot | 4/5 | 1/5 | $0.39 | 3.5 min |
| Haiku 5.5 one-shot | 5/5 | 0/5 | $0.11 | 8.6 min |
| Haiku 5.5 + Opus review loop | 2/2 | 2/2 | $1.15 | |
| Sonnet 5.5 + Opus review loop | 1/1 | 1/1 | $1.24 | |

All runs were regraded with an isolated grader after a contamination incident (§5); no grade changed.
Costs are from token counts at list prices, computed off-repo. The Haiku 5.5 costs use the base price for
every request, so they are lower bounds for requests above 100K prompt tokens.

**Reading.** An Opus review loop fixed both defects in 2 of 2 Haiku runs and 1 of 1 Sonnet run, where the
cheap one-shots fixed both in 0 of 5 and 1 of 5. That is a signal, not yet a reliability measure (pass^k
needs k ≥ 3). Two further review-loop runs were set aside as invalid (Docker went down during the run);
they are not in the table (§5). It does not save money. The reviewer must run and exercise the stack to
check the work, and that costs about as much as Opus doing the task.

### 3.4 Why the cheap models miss

From the transcripts of all 20 B01 one-shots:

| | Opus | Sonnet | Haiku |
|---|---|---|---|
| Turns per run (mean) | 90 | 42 | 166 |
| Tool calls per run (mean) | 41 | 22 | 64 |
| Runs that hit the second defect's error | 10 of 10 | 1 of 5 | 5 of 5 |
| Runs that fixed it | 10 of 10 | 1 of 5 | 0 of 5 |

- **Haiku did more work, not less.** It hit the error every time. In one run it named the cause correctly,
  then wrote that it would "leave that out of this change and report it". The final summary did not
  mention it. The failure is **scope narrowing plus a dropped commitment**.
- **Sonnet mostly never exercised the second entry point.** When it did, it fixed it. The failure is
  **coverage**.
- **Opus treated every broken entry point as part of the request.**

This points to two harness mechanisms that need no strong model:

1. **No silent deferral.** Every decision to leave work out goes to an independent reviewer at once, which
   judges it against the request; a rejected deferral is implemented before the run may finish
   (cadence#68).
2. **Contracts before code.** Write executable checks for every entry point the request covers before the
   implementation starts, and do not let the session end while one fails. This is the "harness-first"
   argument of Datadog's engineering team: verification, not review, is the bottleneck, and *"a weak
   harness cannot be compensated for by better models or more human review"*
   ([Datadog, harness-first agents](https://www.datadoghq.com/blog/ai/harness-first-agents/)).

### 3.5 A published benchmark: where the bar is unreliable

SWE-bench Pro (Harbor 0.24.0, Claude Code in each task's container), 20 Python tasks drawn at random
([calibration](../calibration/README.md)), one one-shot try per model:

| Model | Passed | Cost (list prices) | Per task |
|---|---|---|---|
| Opus 5.5 | 18/20 | $5.79 | $0.290 |
| Sonnet 5.5 | 18/20 | $2.57 | $0.129 |
| Haiku 5.5 | 17/20 | $0.54 (lower bound) | $0.027 |

Pass/fail per task, and the script that merges the runs: [`round2.md`](../calibration/swebench-pro/round2.md).

- **Haiku 5.5 alone is within one task of Opus 5.5, at about one tenth of the cost.** That cost is a lower
  bound: priced at the rate above 100K prompt tokens for every token, Haiku would cost about $2.70, about half of
  Opus. Only one task passed on Opus and failed on both cheaper models, each once; one try does not make it a lift task. So this
  sample is not where a harness can show lift: a cheap model alone already gets nearly all of it.
- **Where the bar is unreliable.** Two tasks passed only 2 of 5 Opus tries. Those are beyond candidates: a
  harness that raises their pass rate does something the strong model alone cannot do reliably.
- **What one try does not show.** A single pass rate says nothing about the next run. The open measure is
  reliability over repeats (pass^k) on the beyond tasks and on the tasks the models split on.
- **Limits.** 20 tasks; one try per model; 15 trials (Haiku 10, Sonnet 4, Opus 1) died in container setup
  before the model ran and were rerun once; they are not counted as fails. Cost is computed from token counts at list prices, because Claude Code misprices Haiku 5.5.
  The collector prices trial totals at the base rate and prices cache writes as plain input, so the Haiku
  5.5 cost is a lower bound and every cost is somewhat low ([calibration](../calibration/README.md)).

## 4. What this means for building a harness

Stronger models do not remove the need to check their work; they write more code someone must trust. A
one-shot gives you code. A harness can give you code plus evidence: a ledger, reviews by agents that did
not write it, and gate records. It changes what a person checks, the evidence rather than every line.

| Holds up | Does not |
|---|---|
| Independent verification of the running result (a signal: it recovered the cheap-model miss in 2/2 Haiku and 1/1 Sonnet B01 runs) | A long planning pipeline on a weak orchestrator (more places to stop) |
| An audit trail with attested authorship (it makes failures diagnosable in minutes) | Review by a strong model as the verification step, if the goal is cost |
| Enforcement the model cannot skip (gates, stop hooks) | Review as a stand-in for executable checks |
| Holding scope: a dropped part of the request is a defect | Deferral checks that look only at form (a ticket, a label) |

Cadence changes that follow: P6 gets a cycle limit (cadence#63, done); the delegation record is written
by a hook, not by the orchestrator (cadence#64, done); a no-tracker mode (cadence#65, open); a verdict
counts only from the peer of its stage (cadence#66, open); deferrals are judged in real time (cadence#68,
open).

### 4.1 Cadence after the benchmark's pin (status 16 October 2026)

The tier-1 and tier-2 results ([`results/REPORT.md`](../results/REPORT.md)) stay measured at the pinned
Cadence commit `e5c3a92` ([`frameworks.lock.json`](../frameworks.lock.json)). They are not rerun. Cadence
main has changed since then (`git log e5c3a92..origin/main`, and two PRs merged on 16 October):

| Change | Cadence issue / PR |
|---|---|
| P6 adversarial loop bounded at three cycles; open items carried | #63 / PR #88 (`a88f611`) |
| The Claude Code hook writes the lean delegation record | #64 / PR #75 (`948d785`) |
| A2 and `install.sh` report peer shadows | #53 / PR #74 |
| Run-scoped records, so concurrent runs do not break each other | #76 / PR #81 |
| Hooks find the workspace from the host; absolute commands for the agent | #82, #83 / PR #87 |
| A Pi extension runs the gates | #84 / PR #91 |
| A5 judges only the reports of its own run | #93 / PR #95 |
| Lean peer return (one line, held once at `SubagentStop`) and an orchestrator context budget (shadow by default) | #96 / PR #97 |
| R3 measures cognitive complexity for every language with an analyzer; a new or worse function over 15 fails. Before it, R3 was a stub that listed changed `.rs` files and always passed | #100 / PR #101 |

Issues opened on 16 October: an audit of Cadence's own complexity and tests (#98: 2,251 tests, test code
1.5 times the source lines); why Cadence's own stages did not stop that debt (#99); a VERDICT word list for
the lean return (#102); plans name external contracts, test-benchmark owns fixtures and edge-case inputs,
and plans do not cycle on tests (#103; a postmortem refined it). The R3 scan for #100 found 47 of 2,307
functions over cognitive complexity 15.

## 5. Threats to validity

- **Small samples.** Iteration 4 and the pilot are one run per cell, with one grader. B01 has 5–10 runs
  per one-shot arm and 1–2 per review-loop arm. Only the largest gaps are outside noise. Criteria v1
  requires 5 runs per cell and two graders before any claim.
- **Iteration 4 was not a clean room.** Its one-shots could see the user-level skill list, which
  describes TDD. None used a skill, but the descriptions may have primed them. Later rounds gate on
  [`clean_room_check.py`](../scripts/clean_room_check.py).
- **Easy tasks.** T04–T06 are class S ([criteria §3](method/criteria.md#3-task-classes)), where a model alone
  should do well; Opus finished each in about 2 minutes. Class L and O tasks, where review and evidence
  should matter most, have not run.
- **Invalid runs set aside.** Two further review-loop runs were set aside as invalid (Docker went down
  during the run). They are not counted in either review-loop arm, so the 2/2 and 1/1 cells are the valid
  runs only.
- **Contamination incident.** The B01 runs ran agents on the host. Workers they started outlived their
  runs and shared a message broker with later runs and the grader. All runs were regraded with an isolated
  grader (a private broker database, stray processes killed); no grade changed. One container per trial is
  now done ([harness-benchmark#10](https://github.com/jtouley/harness-benchmark/issues/10), closed 15 October by
  PR #23, [runner](../runner/README.md)). The B01 runs above ran before it.
- **Infrastructure losses.** Emulated x86 containers crashed the test laptop's Docker three times; the
  affected trials are recorded as infrastructure errors, not failures, and were rerun.
- **One task per class so far.** B01 is one bug; SWE-bench Pro is one benchmark's sample of 20, with one
  try per model.
- **Author bias.** Mitigated by pre-registration, blind grading, and stating the unfavorable results first.

## 6. What comes next

1. **The pipeline family** ([tasks](plans/tasks/pipeline-family.md)): one spec on three stacks (dlt and
   dbt-duckdb; a config-driven Arrow, Polars and DataFusion engine with dbt-duckdb; Scala Spark with
   dbt-spark), each on a Parquet lake, each with a follow-up change (a new mart and a dashboard). Work that
   does not fit one session.
2. **Traceability as a measure.** Seeded traps give each failure a known cause. A blind auditor gets only
   the run's record and must find the cause, where it first went wrong, and the cheapest fix point. A
   one-shot leaves a transcript; a harness leaves a spec, a plan, phases, reviews and decisions. The
   question is what each is worth when something breaks.
3. **Cheap verification.** Haiku-only arms: a verification harness (contracts before code, a stop gate),
   a review loop with a Haiku reviewer, and Cadence with all peers on Haiku after its defects are fixed.
4. **Success criteria** ([quality model](method/quality-model.md#owner-criteria-2026-10-14-dry-solid-extensible-traceable-cheap)):
   the arm closest to a DRY, SOLID and extensible system, whose path we can understand, and the
   cheapest arm in that top tier.
