# Review skill eval, 25 October: set-up, no result yet

- Question: does the candidate review skill `antagonistic-review` (cadence#230), or one of its parts, find more
  reproduced defects than the current `/pr-review-local` and the built-in `code-review` skill, on the same stored
  diffs, by more than the run-to-run variance and within the speed SLO? And does cadence#228's revision of
  `/pr-review-local` beat the current version?
- Status: the eval set, the harness and the run lists are committed. **No review has run yet**, so there is no
  result. The reviewer runs must be Agent-tool subagents of the coordinator's session (owner limit, 25 October:
  no CLI agents, no sandboxes). The session that built this had no Agent tool.

## What is here

| File | What it is |
|---|---|
| [`../../../revieweval/`](../../../revieweval/) | `prepare.py`, `build.py`, `compare.py`, `cases.json` and the README with the steps |
| `trees.json` | For each case: the run id, the tree blob sha256, the original head and base, and the blinded commits |
| `configs-*.json` | The configurations and baselines of each iteration, pinned to cadence commits |
| `dispatch-*.jsonl` | The run lists: one line per subagent, with the run folder, the step, the steps it waits for, the diff, the prompt and the output path |

## The eval set

11 stored trees of batch `2026-10-24-shapes-r2` (`runs-store`, sha256 checked against each `record.json`).
P1 full-5 has no tree. No run is re-run. Each tree is blinded: two commits, neutral messages and authors, and
no arm files. The cases are `review-01` to `review-11`, a fixed shuffle.

Known answers, and how each one is verified:

| Answers | Cases | Verified by |
|---|---|---|
| The consumer does not get past the replay's invalid frame (loops or crashes): a must-fix | 6 (stream_ok false) | The grader (code) in `runs/<id>/scores.jsonl`, grader c344bea. Mechanism from the postmortem log for P1 core-4, P2 core-5 (loop) and P2 core-4 (crash). |
| A must-fix claim of that defect is a false finding | 5 (stream_ok true) | The same grader field |
| The survivability pilot's H1, H2 (must-fix) and M1 to M7 (any severity) | review-01 (P1 core-6) | The pilot's consolidation, which reproduced each one in a scratch clone. The pilot's tree and review-01 have the same git tree (9305aa39). H1 counts only when shown from the code or a local stub: the pilot's 403 came from an outside request that the rules did not permit. |

All configurations review the same head of each case (the stored final tree). So the flagged-and-fixed counts
of the original runs are not a metric. The set has no one-shot trees yet.

## The iterations

| Iteration | Configurations | Baselines | Runs | Dispatches |
|---|---|---|---|---|
| `antagonistic-vs-baselines` | `new_skill` = antagonistic-review@7683e55 `#full`; parts `#three` (three reviewers, no consolidation) and `#single` (one reviewer); `old_skill` = pr-review-local@2100c6e; `builtin_code_review` = `/code-review <path>` as it ships | `old_skill`, `builtin_code_review` | 3 | 528 |
| `r1-current-vs-pr228` | `new_skill` = pr-review-local@9314a61 (#228); `old_skill` = pr-review-local@2100c6e | `old_skill` | 3 | 132 |

cadence#229 does not change the R1 review text (`commands/pr-review-local.md`, `references/review-rigor.md`). It
adds a budget to the R1 row of `stages.json` and runs R2 and R3 in parallel. So the R1 comparison uses #228,
which changes both files.

## Versions of the candidate

| Commit | Change | Source |
|---|---|---|
| 3c5420b | The owner's procedure and prompts | Front matter, survivability line |
| cc367f5 | The consolidation standard: the parts of `/pr-review-local` that worked, and the run learnings | Log Oct 25 02:30, the pilot on P1 core-6 |
| c49d1ff | One must-fix per class, severity apart from reproduction, collection proof, stage-boundary kills, local stubs | The weakness review (`survive/postmortem-weaknesses.md`) |
| 7683e55 | Spec breaks are must-fix, reading is not a pass, independent oracles, the full input classes, the spec trace | The R1 skill review (`survive/skill-review-R1.md`) |

The run lists use 7683e55. The R1 skill review reports that the #228 and #229 R1 text closes none of the
pilot's findings on P1 core-6 (inferred from reading, not measured). The `r1-current-vs-pr228` iteration
measures it.

## The rule

`compare.py collect` computes, for each configuration against each baseline: recall (defect answers found),
false findings (control answers broken, plus must-fix claims that the grader refuted), each as the mean and
stddev over the 3 repeats, and wall time and tokens per review. A configuration is measurably better only when
its recall gain is larger than the larger stddev, its false findings are not worse beyond their stddev, and its
time and tokens are at most 1.25 times the baseline's. Cost is in tokens: Agent-tool notifications report
tokens, not dollars.

## Known limits

- The reviewers run without a jail (the owner's limit forbids building one). Each prompt says to read nothing
  outside the run's own copy, the build log and the output folder, but nothing enforces it. The workspace is
  outside every checkout, and `cases.json` and `golden/` are not in it.
- The build step (`build.py`) did not run: port 8099 was taken by another process. Without it, the reviewers
  get no build log.
- 660 dispatches at 3 repeats is a large batch. Run `antagonistic-vs-baselines` first.

## Sources kept here

`sources/` holds copies of the files that the candidate and the known answers cite, written by other agents of
the same session (the survivability pilot and the postmortem agent), unchanged, with `SHA256SUMS`:
`final-review-t1.md` and `findings-t1-{A,B,C}.txt` (the pilot on P1 core-6), `postmortem-weaknesses.md` and
`skill-review-R1.md`.
