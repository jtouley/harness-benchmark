# Next steps: the cheapest model that matches Opus, with an audit trail

Status: proposed design (October 2026). Nothing here has run yet. It follows from the
[findings so far](findings.md) and must meet [criteria v1](criteria.md) before any result counts.

## The question

**What is the cheapest model that, inside a harness, matches or beats Opus 5.5 working alone,
and leaves an audit trail that a one-shot run cannot?**

The cheap model may use more tokens than Opus. What counts is the dollar cost per delivered task,
the defects that reach the delivered code, and the evidence that the run leaves behind.

## Why this is the right next question

- In iteration 4, Opus alone was the best arm on quality (8.00). A harness on Opus cost about 4
  times the tokens and gave a little lower quality (Cadence 7.33). So "harness on the same strong
  model" is a governance purchase, not a quality or cost purchase, on these tasks.
- Per-token list prices differ by 40 times: Opus 5.5 $4 / $20 per million input / output tokens,
  Haiku 5.5 $0.10 / $0.50 ([`pricing.json`](../pricing.json)). Cache reads differ by 20 times.
- **Estimate (not a result):** Cadence on Opus used about 4 times the tokens of the Opus one-shot.
  If Cadence on Haiku 5.5 uses a similar number of tokens with a similar mix, it costs between 1/10
  and 1/5 of the Opus one-shot. That holds only if a cheap model can follow the Cadence procedure
  at all. The pilot below finds out.
- Haiku 4.5 alone scored 3.25. A cheap model alone does not reach Opus. The open question is how
  much of that gap a plan, independent review and verified fixes can close.

## Hypotheses

| # | Hypothesis | What would refute it |
|---|---|---|
| H1 | Cadence on a model at 1/10 of the Opus price per token reaches the Opus one-shot within 0.5 quality points, with no more major defects | Its quality or defect count stays clearly below the Opus one-shot after 5 runs per task |
| H2 | It costs less per delivered task than the Opus one-shot, including its extra tokens | Its dollars per delivered task are higher than the Opus one-shot's |
| H3 | It leaves a complete audit trail (M10) on every delivered run | Plans, independent reviews or closure records are missing, or do not match the delivered head |
| H4 | A cheap implementer with a strong reviewer (Opus only for R1) is the cheapest arm that matches Opus | Single-model cheap arms match Opus for less, or the mixed arm does not match Opus |

## Arms

Each harness arm has a one-shot arm on the same model ([criteria §2](criteria.md)), so the
harness effect and the model effect stay separate.

| Tier | Host | Model (pinned at run time) | Harness arm | One-shot arm |
|---|---|---|---|---|
| Bar | Claude Code | Opus 5.5 | Cadence (ceiling) | **Opus one-shot (the bar)** |
| Anthropic ladder | Claude Code | Sonnet 5.5 | Cadence | one-shot |
| Anthropic ladder | Claude Code | Haiku 5.5 | Cadence | one-shot |
| Cross-vendor | Cursor CLI (`cursor-agent`) | `gpt-5.4-mini-*` | Cadence | one-shot |
| Cross-vendor | Cursor CLI | `gemini-3.8-flash-*` | Cadence | one-shot |
| Cross-vendor | Cursor CLI | `composer-2.5` | Cadence | one-shot |
| Cross-vendor | OpenAI API (an agent CLI or a small tool loop) | the cheapest tool-using OpenAI model the account can call | Cadence (headless gate protocol) | one-shot |
| Mixed | Claude Code | Haiku 5.5 implements, Opus 5.5 runs R1 only | Cadence | not applicable |

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

- **M1 acceptance** gates delivery. **M2 reproduced defects** and **M7 quality** decide "matches Opus".
- **M9 cost in dollars**: input, output and cache tokens of the whole session, nested subagents
  included, priced from `pricing.json`. Iterations 3 and 4 did not record this split. This run must.
- **M10 auditability**, scored as a checklist per run: a plan; a spec check; a plan review, an
  adversarial review and a PR review, each by an agent other than the implementer; a findings ledger
  where each must-fix finding has a verification; a closure record that names the delivered head.
  Report the share of items present, by host.
- **M3 false success**: a run that claims success while M1 or M2 shows failure. A harness that stops
  with a recorded reason is not a false success.

## Decision rule for this question

The answer is the **cheapest arm, in dollars per delivered task, that meets all of these**:
quality (M7) at least the Opus one-shot minus 0.5; major or critical defects (M2) at most the Opus
one-shot's; completion (M8) at least 4 of 5 runs per task; M10 complete on every delivered run.
If no arm meets them, the answer is "none yet", and the harness case rests on auditability and
enforcement only. The sample, the caps and the two-grader protocol are those of criteria v1.

## Plan

| Stage | What | Size | Exit |
|---|---|---|---|
| 0. Prerequisites | See the list below | none | Each item has a test or a recorded check |
| 1. Pilot | T05 (budgets, the task with the most edge cases) only, n = 1, every arm | ~15 runs | Drop an arm that cannot follow the Cadence procedure at all. Keep the rest |
| 2. Ladder | T04–T06, n = 5, the arms that passed the pilot, plus the Opus bar | ≤ 150 runs | The decision rule above, per task |
| 3. Harder tasks | Class L and O tasks ([criteria §3](criteria.md)) once committed under `golden/tasks/` | per criteria | Repeat the decision rule where a harness should earn most |

## Prerequisites (stage 0)

1. **Cost capture.** Record input, output and cache tokens and dollars for the whole session, nested
   subagents included, from the host's own accounting. Verify that this includes the harness's peers.
2. **Isolated environment per run.** Each run gets a clean `HOME`, so no user-level skill takes the
   place of a Cadence peer (cadence#53), and no sandbox rule blocks a harness's own scripts. The
   Harbor tier already gives a clean container.
3. **Cadence on cheap models.** A per-stage model setting, so a stage (for example R1) can run on a
   stronger model than the implementer (H4). Today all peers inherit the host model.
4. **Cursor CLI validation.** Confirm that `cursor-agent --print` runs Cadence's Cursor hooks. This
   also closes the README limitation "No Cursor binary was available to validate them".
5. **OpenAI host.** Pick the agent runner (an OpenAI-capable coding CLI or a small tool loop over the
   API), pin it, and run Cadence through the headless gate protocol.
6. **Two graders and a repro script** (criteria §5): each reproduced defect re-runs in a clean copy.
7. **Prices** for every model in `pricing.json`, with source and date.

## What we will report

- One table per task: arm, model, host, delivered, hidden, M2 defects by severity, M7, dollars per
  delivered task, M10 share, completion.
- A cost and quality chart with the Opus one-shot as the reference point.
- The answer to the question, by the decision rule, including "none yet" if that is the result.
- Every result that goes against the harness, reported the same way as a result for it.
