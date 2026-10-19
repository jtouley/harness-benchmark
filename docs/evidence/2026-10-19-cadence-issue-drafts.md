# Cadence issue drafts from the cadence-core postmortem (19 October 2026)

Evidence is on harness-benchmark branch `ccr-3d2e0c73-lr6bdt` at `abb8c07`, under
`docs/evidence/2026-10-19-pipeline-cadence-core/`. The postmortem is
[here](2026-10-19-cadence-core-postmortem.md). Two defects the runs found are already fixed and are left
out: the P9 gate counting applied must-fix ids (`f6011df`), and no PR record without a forge (`f734888`).

The owner reviewed the first drafts. Four drafts were dropped or redirected, and two stand:

| Draft | Decision | Why |
|---|---|---|
| R1 walks the code, not the delivered files | Dropped as a separate issue | As written it points Cadence at the benchmark's grader (`out/marts/`, the answer map), which would tune the harness to the test (criteria v2 §2.4). The generic part, proving each of the ticket's own requirements against what was delivered, is in issue A |
| The audit trail does not match the declared paths | Not a Cadence issue yet | The declared paths are harness-benchmark's own lockfile row, written by the benchmark session. First check that row against Cadence's code and the run's full `.context/`; the copy in the evidence may be incomplete. File in Cadence only if Cadence documents those paths and writes others |
| The plan-review loop always reaches its limit | Search first, then comment | Real; the owner has raised it elsewhere, so an issue probably exists. Add this round's evidence there (below) |
| The orchestrator sizes the acceptance step | Dropped | A plan should not pin run parameters such as a stream's duration. The one-hour run cost a score only because of a time cap criteria v2 forbids for harness arms (harness-benchmark #48), and "the replayed hour" came from the benchmark's own prompt |

## A. Build a requirement list from the ticket and hold the run to it

Check jtouley/cadence#103 first ("plans name the external contracts they read"); if it covers this,
comment there instead.

What happened (third P1 run): the plan restated the ticket as seven "acceptance signals" in its own
words. One of the ticket's stated requirements was not among them, and the plan then specified the
opposite of it: the ticket asks for one folder per published table, and the plan writes single files
(plan lines 204, 262, 511). Its Phase 8 exit criterion accepts any model that `dbt ls` lists, where the
ticket asks for published tables. Five plan reviews and five PR reviews checked the plan and the code
against each other, never against the ticket's sentences. Nothing in the run listed the ticket's
requirements, traced each one to a phase and a proof, or blocked closure until each had evidence.

Ask (generic, no knowledge of any benchmark):
- At plan creation, quote every requirement sentence of the ticket into a numbered list (quoted, not
  paraphrased).
- Map each to the phase that meets it and the check that proves it. The plan review fails a plan with an
  unmapped requirement, or one whose plan text contradicts the quote.
- The orchestrator works that list as its task list (the host's task tools where it has them) to the end.
- Closure refuses `must_fix: 0` until each requirement has evidence from the delivered work (a command
  and its output), not from the plan.

## B. Plan-review cycles each find new items in the previous cycle's additions (comment on the existing issue)

On all three Haiku 5.5 runs, plan review ran to its five-cycle limit. Every verdict was `READY WITH
CHANGES`, with three to five new must-fix items found in text the previous cycle added (MF-1 to MF-19
over five reviews on the P1 rerun). The limit, not the reviewer, ended the loop: about 20 minutes and
$0.12 to $0.15 per run, at base prices.

## C. Peer handoffs as lean documents (comment on the existing lean-prompt issue)

The 13 October pilot found peer prompts sent as "full briefings, not the one-line lean form the gate
expects", and `guard_lean_task_prompt.py` wired only in the Cursor hooks, not Claude Code's
(`docs/evidence/2026-10-13-pilot/cadence_haiku_opus/outputs/summary.md`, item 1). No transcripts were
committed for the 19 October runs, so whether that still holds cannot be checked. Related on the
benchmark side: harness-benchmark #56 (the benchmark itself pastes the whole ticket and an environment
note into the prompt instead of handing over a document).
