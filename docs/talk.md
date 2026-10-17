# Talk track: "Why a harness, when the model is this good?" (20 minutes)

A ready-to-present outline. Each section has a time box, a headline, what to show, and speaker
notes. Every number comes from the [whitepaper](whitepaper.md), the [findings](findings.md), the
[iteration 4 data](experiments/2026-10-12-iteration-4/), the [pilot](experiments/2026-10-13-pilot.md) and the
[pipeline trials](experiments/2026-10-15-pipeline-trials.md).
The talk is credible because it states the results that do not favor the harness first, and because it
never claims more than its sample sizes can show.

The story in one line: **a harness earns its cost by verification and by holding scope, not by
ceremony.**

The thesis, checked against the data (16 October 2026): **harnesses do not make strong models write
better code.** On well-specified tasks a one-shot matched the harness at about 1/30 of the time. What a
harness buys is verification and accountability. An independent review of the running result recovered a
bug that the cheap models missed: 1 of 10 cheap one-shot runs fixed both B01 defects, against 3 of 3 with an
Opus review loop (Haiku and Sonnet pooled; Fisher exact test, one-sided, p ≈ 0.014; small samples). The
first review round found most of the confirmed defects ([review value](review-value.md)). A long planning
pipeline did not help: on a cheap model it stalled before it wrote code. Precise specs are why the
one-shot did well. Specs as executable contracts are not tested yet.

**Cost figures.** Haiku 5.5 dollar figures in this talk use the base price for every request, so they
are lower bounds: Haiku 5.5 costs 5 times more for a prompt above 100K tokens, and the scripts priced
session totals ([next steps](next-steps.md#cost-accounting-price-each-request-at-its-own-tier-planned-2026-10-16)).

---

## 1. The setup (0:00–1:00)

**Headline:** We gave the same request to strong and cheap models, alone and inside our harness. Then
we checked the result without knowing which arm made it.

**Show:** six rounds: iteration 4 (three small feature tasks), a pilot (Cadence on a cheap model), B01
(a real multi-cause bug), a sample of SWE-bench Pro, three long data pipelines, and Cadence reviewing its
own repository.

**The question in the title:** today's strong models, Opus 5.5 among them, finish small work alone. So
what is a harness for now? Section 13 answers it.

**Notes:** **Disclosure:** I wrote Cadence. That is why the rules were written down before the runs,
why the graders were blind, and why the results against Cadence come first.

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
This talk tests both.

## 3. Iteration 4: no quality gain from the harness (2:30–4:00)

**Headline:** On small, precise tasks, the harness did not beat the model alone, and it took about 30
times longer.

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

## 4. Iteration 4: what the harness bought, and what it did not (4:00–5:30)

**Headline:** Not better code. Four other things, at a high price.

**Show:**

| Bought | Did not buy |
|---|---|
| **No crash in delivered code.** Each one-shot shipped two (all six on one task, budgets, from three inputs); neither harness shipped one. | **Restraint.** The graders marked Cadence down for scope it was not asked for ("heavier than needed"). |
| **An audit trail.** A plan, reviews by 8–12 separate agents, a findings ledger, 12–23 attestation rows per run. A one-shot leaves one commit. | **Speed or cost.** About 30 times the wall time, 4 times the tokens. |
| **Completion you can trust.** 3 of 3 delivered, or a recorded stop. No false success. | **Its own correctness** (cadence#56, fixed in #57). |
| **Rules it cannot skip.** The hooks block 7 of 9 probes. | |

**Notes:** Better code is already off the table from section 3, so it is not repeated here. The defect gap
(0.67 against 1.00 major or critical defects per run) is under the 0.5 bar of our own rule. So "fewer defects" is not shown. The crash count is the clearest signal, and it comes from
one task.

## 5. The pilot: full Cadence on a cheap model delivered nothing (5:30–7:30)

**Headline:** We put the whole harness on Haiku 5.5. It stopped in its own process before it wrote any
code.

**Show:** T05 (budgets), clean room, one run per arm ([pilot](experiments/2026-10-13-pilot.md)).

| Arm | Result | Time | Cost |
|---|---|---|---|
| Opus 5.5 one-shot | Delivered; 7/7 hidden tests; quality gate passed | 111 s | $0.40 |
| Cadence, all Haiku 5.5 | Hard stop at P6 after four plan updates | 75 min | $1.13 (lower bound; up to $5.66) |
| Cadence, Haiku 5.5 + Opus reviews | Hard stop at P9: no delegation records | 27 min | $3.19 (lower bound; up to $4.50) |

**Notes:** The cheap arms spent at least 3 and 8 times the dollars of the Opus one-shot (up to 14 and 11
times at the upper bound), and delivered nothing. Both orchestrators ended above 100K prompt tokens. Static
skill text explains only about 18K of that; one cause is that each peer returned a full report into the
orchestrator's context (Cadence PR #97 adds one-line peer returns and a context budget; not yet rerun).
The causes: the adversarial review had no cycle limit and found new edge cases each round. In the other
arm, a gate depends on the orchestrator recording its own delegations, and the cheap orchestrator did not
record them. A full harness on a weak orchestrator adds places to stop. Both runs stopped and said why:
no false success. We filed four Cadence defects (cadence#63–#66); #63 and #64 are now fixed. This is n = 1. It shows a failure mode,
not a rate.

## 6. The calibration rule: choose tasks by what the bar does (7:30–8:30)

**Headline:** A task is hard only when the strong model fails it, not when it looks hard.

**Show:** two task classes ([next steps](next-steps.md#task-selection-calibrated-against-the-bar-owner-direction-2026-10-13)):

- **Lift task:** the Opus one-shot is reliable and the cheap one-shots are not. Can a harness lift a cheap
  model to the bar, for less?
- **Beyond task:** the Opus one-shot is unreliable. Can a harness raise reliability at all?

**Notes:** Reliability is measured over repeats. A one-shot that passes once says nothing about the next
run. T05 is out: the bar solves it in two minutes.

## 7. B01: a real multi-cause bug (8:30–10:00)

**Headline:** Opus fixed it every time. The cheap models fixed the main path and missed the rest.

**Show:** a private brownfield bug in a multi-service application with stacked faults. The prompt is the
original product request. The grader runs the real stack and checks two outcomes: the main path, and a
second defect.

| Arm | Main path fixed | Both defects fixed | Mean cost | Mean time |
|---|---|---|---|---|
| Opus 5.5 one-shot | 10/10 | 10/10 | $1.29 | 7.3 min |
| Sonnet 5.5 one-shot | 4/5 | 1/5 | $0.39 | 3.5 min |
| Haiku 5.5 one-shot | 5/5 | 0/5 | $0.11 (lower bound) | 8.6 min |

**Notes:** B01 is a lift task: the bar is reliable, the cheap models are not. The code belongs to a third
party, so we publish the scores only. After a contamination incident (processes from earlier runs
outlived them), all runs were regraded with an isolated grader. No grade changed. One container per trial
is now done (harness-benchmark#10, closed 15 October by PR #23); these B01 runs ran before it.

## 8. Why the cheap models miss (10:00–12:00)

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

Two harness mechanisms fix both failures without a strong model: (1) **no silent deferral**: each
decision to leave work out goes to an independent reviewer at once (cadence#68); (2) **contracts before
code**: executable checks for every entry point the request covers, and the session cannot end while one
fails.

## 9. The review loop: reliability back, no money saved (12:00–13:30)

**Headline:** An independent reviewer that checks the running system recovered the miss in every valid
run so far (2 Haiku, 1 Sonnet). It costs about as much as Opus alone.

**Show:** a minimal harness: the cheap model works, an Opus subagent reviews in the running system, the
cheap model fixes.

| Arm | Both defects fixed | Mean cost |
|---|---|---|
| Opus 5.5 one-shot | 10/10 | $1.29 |
| Haiku 5.5 + Opus review loop | 2/2 | $1.15 (Haiku part a lower bound) |
| Sonnet 5.5 + Opus review loop | 1/1 | $1.24 |

**Notes:** Both Haiku runs and the one Sonnet run fixed both defects. Two more runs were set aside as
invalid (Docker went down during the run). That is a signal, not yet a reliability measure. The reviewer
must run and exercise the stack to check the work, and that costs about as much as Opus doing the task.
So the review loop is a signal that the reliability gap can be closed, but it does not save money. The samples are 1–2 runs per arm. The open question: can the check itself be
cheap?

Pooled, the cheap one-shots fixed both defects in 1 of 10 runs and the review loops in 3 of 3 (Fisher exact
test, one-sided, p ≈ 0.014). Small samples, two models pooled, one bug.

Process evidence from outside the benchmark points the same way: on 16 October, fresh-subagent reviews of
two Cadence PRs found 5 and 4 must-fix defects; two of them came from fixes of earlier nits
([review value](review-value.md#independent-reviews-of-two-cadence-prs-16-october-2026)).

## 10. SWE-bench Pro: the cheap one-shot is close, the bar is unreliable (13:30–14:15)

**Headline:** On a published sample, Haiku alone is within one task of Opus at a tenth of the cost. The
open question is the tasks where Opus itself is unreliable.

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
trials that died in container setup were rerun. One try is a pass rate, not reliability (pass^k).

## 11. The pipeline family: no one-shot passes long work, and no harness has run yet (14:15–15:30)

**Headline:** On long-horizon pipelines, every one-shot failed at least one check, Opus included. These are
the first tasks where the bar itself is unreliable. The harness arms have not run on them yet.

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
  puts out of bounds. Even with its P2 map fixed by hand, it scores 3/7 (a diagnostic, not a result). This
  is the same scope problem as B01: the cheap model does a narrower task than the one it was given.
- **Opus is not a reliable bar here.** It led on P1 and P2, and Sonnet beat it on the Scala stack. On B01
  Opus fixed both defects 10 of 10 times. Here no model is near a full pass. That makes these the first
  *beyond* tasks: a harness that raises the pass rate would do what the strong model alone cannot.
- **Where is the harness run?** It has not happened yet. The runner already installs a harness as a
  Claude Code plugin (`--plugin-dir`), and two harness arms are built: `harnesses/reviewloop` and
  `harnesses/verifyloop`. The 15 October round ran the one-shot baselines only, so there is a bar to measure
  the harnesses against. The harness trials are the next run (section 15).
- **Limits.** One try per cell. Opus's P1 6/7 is provisional: a grader fix (reading a `checks:` key beside
  other keys) was made after its output was seen. Two check readings are open owner decisions (TASK-81):
  whether grant money is placed at the recipient's county or the place of performance (it decides 4 of
  the 6 Sonnet and Opus runs on P2 and P3), and whether check 4 accepts a reconciliation query. Grades can
  move when those are decided. The trials ran on an Apple Silicon laptop, not the specified x86-64 host, so
  times are laptop times.
- **Two harness-benchmark defects were found and fixed:** the grader deleted uncommitted work before
  grading (now `--snapshot-worktree`), and it did not read a `checks:` key beside other top-level keys.
  The benchmark is software too.

## 12. Cadence on its own repository: review caught what green tests missed (15:30–16:15)

**Headline:** Outside the benchmark, independent review keeps catching what the model and its test
suite pass.

**Show:**

- **PR #118** (Go, Java and C/C++ in the complexity check): 2,599 tests passed. The R1 review still
  blocked it: a Go function literal passed to a call was scored one nesting level too shallow. Fixed and
  verified by command before closure.
- **PR #112** (test ownership): R1 found a gate that crashed with a traceback on a malformed file.
  Closing the run exposed a bypass in the harness itself: `ledger_verify.py --dry-run` marked findings
  verified without running their checks (cadence#121).
- **Review rounds** ([review value](review-value.md)): across 18 PR reviews, the first round found 40 of
  51 confirmed defects (78%); rounds two and three found the other 11.

**Notes:** Process evidence, not a controlled comparison. The same discipline runs on Cadence's own debt:
the complexity audit (cadence#98) is being paid down in open refactor PRs #129–#134.

## 13. What strong models change: the harness's job moved from writing code to proving it (16:15–17:30)

**Headline:** The stronger the model, the less a harness is needed to write code, and the more of its
output someone has to check.

**Show:** three zones, each pointing back to its evidence rather than repeating it:

| Work | Use | Evidence |
|---|---|---|
| Small, specified work | The model alone. A harness added time, not quality; a cheap model alone is already close. | Sections 3, 10 |
| Work someone must trust | A harness as verifier and record: independent review, enforced rules, a ledger. | Sections 4, 9, 12 |
| Long work past the model | The open frontier: no one-shot finished it, Opus included. | Section 11 |

**Notes:** This is the answer to the title. Today's strong models finish small, well-specified work
alone, so a harness is no longer what gets that code written. What the harness bought, every time it
bought something, was verification and a record; that gets more valuable, not less, as models write more
code faster. The third row is a hypothesis: whether a harness carries long work no model finishes alone
is the next experiment. The first two rows are measured, mostly on one run per cell. We have no market
data: this is about the harness's job, not its market share.

## 14. What this means for building a harness (17:30–18:15)

**Headline:** Keep verification and scope. Cut ceremony.

**Show:**

| Holds up | Does not |
|---|---|
| Independent verification of the running result | A long planning pipeline on a weak orchestrator |
| An audit trail with attested authorship | A strong-model reviewer, if the goal is cost |
| Enforcement the model cannot skip | Review as a stand-in for executable checks |
| Holding scope: a dropped part of the request is a defect | Deferral checks that look only at form |

**Notes:** The Cadence changes that follow: a cycle limit on P6 (cadence#63, done); a hook writes the
delegation record (cadence#64, done); a no-tracker mode (cadence#65, open); a verdict counts only from the
peer of its stage (cadence#66, open); deferrals are judged in real time (cadence#68, open). Also done since
the pilot: one-line peer returns and a context budget (PR #97), and an R3 cognitive-complexity check for
every language with an analyzer (PR #101). The tier-1 and tier-2 results stay measured at the pinned commit
`e5c3a92` ([whitepaper §4.1](whitepaper.md#41-cadence-after-the-benchmarks-pin-status-16-october-2026)). This agrees with Datadog's "harness-first"
argument: verification, not review, is the bottleneck.

## 15. What comes next (18:15–19:15)

**Headline:** Make the check cheap, give it long work, and measure what the record is worth when
something breaks.

**Show:**

1. **Cheap verification.** Haiku-only arms: a verification harness (contracts before code, a stop gate,
   no model reviewer); a review loop with a Haiku reviewer; full Cadence with all peers on Haiku, after
   cadence#65 and #66 are fixed (#63 and #64 are fixed). In every harness arm, each deferral goes to an independent Haiku reviewer.
2. **Harness arms on the pipeline family** ([tasks](tasks/pipeline-family.md)). The tasks, the
   isolated runner and the one-shot baselines are done (section 11). Next: the review loop and the
   verification harness on Haiku, with full Cadence on Haiku to follow. Then each task's follow-up change
   (a new mart and a dashboard), built by the same arm on its own code. This is work that does not fit
   one session.
3. **Traceability audits.** Seeded traps give each failure a known cause. A blind auditor gets only the
   run's record. It must find the cause, where the run first went wrong, and the cheapest fix point. A
   one-shot leaves a transcript. A harness leaves a spec, a plan, phases, reviews and decisions. What is
   each record worth?
4. **The owner's success criteria.** The arm closest to a **DRY, SOLID and extensible** system, whose
   path we can **trace**, and the **cheapest** arm in that top tier.

**Notes:** Each trial runs in its own disposable container on a remote Linux host. Every arm gets the same
prompt, word for word, with no hints and no knowledge of the traps. The measures: cost per defect-free
run, traceability when a long task goes wrong, and design quality under a follow-up change.

## 16. Close (19:15–20:00)

**Headline:** A harness earns its cost by verification and by holding scope, not by ceremony.

**Notes:** Three lines, not a recap:

1. Strong models made the harness optional for writing small, specified code.
2. They did not make it optional for proving code: every gain we measured came from an independent check
   or an enforced rule.
3. Open: can that check be cheap, and can it carry long work that no model finishes alone?

---

## Questions to expect

| Question | Answer |
|---|---|
| "Isn't this just noise?" | Iteration 4 and the pilot are one run per cell; only the largest gaps count. B01 has 5–10 runs per one-shot arm, but only 1–2 per review-loop arm. The review-loop result is a signal, not a rate. |
| "You wrote Cadence. Why trust this?" | The rules were written before the runs, the graders were blind, and the main results do not favor Cadence: no quality gain, and no delivery on Haiku. |
| "Did you tune the prompt for the harness?" | No. Every arm gets the same request text, word for word. A harness arm differs only by its installed harness. Each run has an empty `HOME`, and a script checks it. |
| "Why didn't the harness win on quality?" | The small tasks fully specify every output, so review has little to add. And the harness built more than the request asked for. |
| "Why did full Cadence fail on Haiku?" | Two Cadence defects: a review stage with no cycle limit, and a gate that depends on the orchestrator recording its own delegations. Both are fixed now (cadence#63, #64). The pilot is n = 1. |
| "Isn't Haiku just not smart enough?" | The transcripts say no. Haiku took more turns than Opus (166 against 90), hit the second defect in 5 of 5 runs, and diagnosed it once. It chose to leave it out. A harness can check that scope decision. |
| "What is B01? Can I see it?" | A private brownfield bug in a multi-service application with stacked faults. The code belongs to a third party, so we publish only its scores and the grader design. |
| "The review loop costs as much as Opus. Why use it?" | In 3 valid runs (2 Haiku, 1 Sonnet) it closed the reliability gap: a signal, not yet a rate. The cost is the open question. The next arms try cheap checks: a Haiku reviewer, and executable contracts with a stop gate. If none matches the bar, the harness is a governance tool, not a cost tool. |
| "What about the contamination incident?" | Processes from earlier B01 runs outlived them. Every run was regraded with an isolated grader; no grade changed. One container per trial is now done (harness-benchmark#10, closed by PR #23). |
| "Why SWE-bench Pro?" | For comparison with outside numbers, filtered by the same calibration rule. On our sample of 20, Haiku alone passed 17 and Opus 18, so it has no clear lift tasks; two tasks are beyond candidates. |
| "Where is the harness run on the pipeline tasks?" | Not run yet. The 15 October round ran the one-shot baselines (Haiku, Sonnet, Opus on P1–P3) so the harness has a bar to beat. The runner already takes a harness as a plugin, and the review-loop and verification arms are built. Those trials are next. |
| "Could a one-shot just be asked to write a plan and tests?" | It could. That is a harness in a prompt, with no independent check and no enforcement. The baseline does not allow it, so the comparison stays fair. |
| "What about the bugs in your own harness?" | They are real, and part of the result: cadence#56 and #57 in iteration 4, cadence#63–#66 from the pilot (#63 and #64 fixed). The harness is software, and it needs the review it gives. |
