# Postmortem write-ups from the review evidence (shapes-r2 batch)

| File | What it is |
|---|---|
| `postmortem-weaknesses.md` | Where Cadence falls short, drawn from the reviews, the records and Cadence at `2100c6e`. |
| `survey-shapes-r2.md` | A survey of the 10 shapes-r2 Cadence runs other than P1 core-6 (P1 full-5 was lost), one row per run, with citations. |
| `skill-review-R1.md` | Dispatch item 1: which core-6 findings were in R1's reach, which rule let each through, and whether #228, #229 and #231 close it, with proposed skill text against #231's head (`4c437ca`). |
| `skill-review-R2.md` | Dispatch item 3: R2's skill and gate (`skills/test-benchmark/SKILL.md`, `scripts/test_benchmark_gate.py`). |
| `skill-review-fixround.md` | Dispatch item 2: whether each core-6 fix commit fixed the class or only the named instance, and which rule wording drives that. |
| `skill-review-plan.md` | Dispatch item 4: the plan blocks P1, P3 and P4 (plan-create, plan-review, plan-update) on core-6, P2 full-5 and P2 full-6. |
| `skill-review-E1.md` | Dispatch item 5: E1's skill text (`commands/spec-driven.md`, `references/execution-protocol.md`). |
| `skill-review-A5.md` | Dispatch item 7: whether A5's (`skills/vibe-test/SKILL.md`) assumptions reach the plan and change E1, across 11 runs. |

- **Produced by:** read-only subagents of the coordinator session ("Read-only. No network, no agents
  launched"). The files name no agent id.
- **Date:** 2026-10-25 (file times 03:12 to 03:25 UTC). Committed by the evidence agent the same day.
- **Copied from:** the coordinator's scratchpad, `survive/`.

## Verified versus inferred

Each file tags its claims. `postmortem-weaknesses.md` uses **[V]** (checked with the
author's own tool calls), **[I]** (inferred) and **[L]** (taken from the postmortem log without
re-checking). `skill-review-R2.md`, `skill-review-fixround.md`, `skill-review-plan.md`, `skill-review-E1.md` and `skill-review-A5.md` use the same [V]/[I] tags. `skill-review-R1.md` has no tags; it cites
its sources in a closing Sources section, and any skill text the skill reviews propose is a proposal, not a merged change.
`survey-shapes-r2.md` cites every claim to a source tag (`rec:`, `sc:`, `T:`, tree paths, `rg:`).
Official scores are round(reward x 7) from `scores.jsonl`.

## Dispatch item 8 (check-attribution.md) was reverted

`check-attribution.md` (the per-check grid of 13 runs and the block that produced each passing check) was
removed on the owner's instruction (2026-10-25): its grid came from `v3work/<run>/pin/grade.json` in the
coordinator's scratchpad, a regrade folder another agent deleted partway through the author's task, so the grid
could not be re-checked and was never independently evaluated. The official records hold no per-check grade.
It comes back only when a regrade (grader-v3) reproduces it and someone other than its author checks it. The
file stays in git history (f8f7aef).

`survey-shapes-r2.md` uses the same deleted regrade as its secondary `rg:` source (stream positions served), so
those cells are unverified until the same regrade exists.
