# Pipeline family: first trials on the isolated runner (2026-10-15)

The first runs of the pipeline tasks ([P1, P2, P3](../plans/tasks/pipeline-family.md)) through the isolated
runner (`runner/`, wired in this change: [golden/pipeline/README.md](../../golden/pipeline/README.md#a-trial-on-the-isolated-runner)).
The machine was the test laptop: Apple Silicon, Docker Desktop with 8 CPUs and 16 GB, arm64 images, one
trial at a time. The spec asks for an x86-64 host with 32 GB, so treat these times as laptop times.

Each trial: the starting repository (`pipetask.assemble`), the prompt word for word, the dev replay
(seed 0) during the agent's session, then the grader (seed 1) running the candidate's `make` as the agent
user with a fresh HOME and no network. Rows come from `scripts/pipeline_trial.py summary`. Cost is from
token counts at [`pricing.json`](../../pricing.json) list prices.

## Step 2: smoke trials and negative controls (no agent)

| Run | Task | Repository | Reward | Checks | Grading s | First build s | Grading s without first build |
|---|---|---|---|---|---|---|---|
| P1-ref-smoke | P1 | reference | 1.0 | 7/7 | 244.2 | 46.3 | 198.0 |
| P1-ref-1 | P1 | reference | 1.0 | 7/7 | 168.2 | 23.5 | 144.7 |
| P1-ref-2 | P1 | reference | 1.0 | 7/7 | 156.5 | 16.0 | 140.5 |
| P1-ref-deadline | P1 | reference, with the P1 deadline | 1.0 | 7/7 | 155.3 | 14.6 | 140.7 |
| P1-skel-1 | P1 | skeleton unchanged | 0.0 | 0/7 | 5.5 | — | — |
| P2-ref-1 | P2 | reference | 1.0 | 7/7 | 158.2 | 16.1 | 142.1 |
| P2-ref-2 | P2 | reference | 1.0 | 7/7 | 153.7 | 14.7 | 139.0 |
| P2-skel-1 | P2 | skeleton unchanged | 0.0 | 0/7 | 2.2 | — | — |
| P3-ref-1 | P3 | reference | 1.0 | 7/7 | 350.3 | 94.3 | 256.0 |
| P3-ref-2 | P3 | reference | 1.0 | 7/7 | 357.4 | 99.9 | 257.5 |
| P3-skel-1 | P3 | skeleton unchanged | 0.0 | 0/7 | 2.3 | — | — |

- Every reference scores 1.0 and every untouched skeleton 0, on all three tasks.
- Every grading run had the agent user's network blocked, so every build used the image's warm cache
  only: uv for P1 and P2; coursier, ivy and the pip wheelhouse for P3 (`timing.json`:
  `agent_network_during_grading: blocked`).
- `P1-ref-smoke` ran while the P3 image was being built beside it, so it is slower. It is not one of the
  measurements for the caps.

### Measured caps (owner default: worst case of the reference trials plus 50%)

| Task | Reference grading runs (s) | Worst | Grading deadline (`--deadline`) | Runner backstop (`--grader-timeout`) |
|---|---|---|---|---|
| P1 | 168.2, 156.5 | 168.2 | 253 s | 373 s |
| P2 | 158.2, 153.7 | 158.2 | 238 s | 358 s |
| P3 | 350.3, 357.4 | 357.4 | 537 s | 657 s |

A grading run includes two `make build` runs and two `make stream` runs of 30 s and 90 s
(DURATION), so about 120 s of every deadline is the stream durations themselves. The values are in
`runner/pipeline/caps.json`. The agent's guard cap is 7,200 s for every one-shot trial.

## Step 3: one-shot trials on P1 (k = 1)

Claude Code 2.1.287 headless (`claude -p`, permission mode `auto`), no plugin, the prompt word for
word. Guard cap 7,200 s; no run reached it. The P1 rows are **regrades** (`P1-*-1-regrade`): the
working tree each session left (`repo/`), graded again in the same image and runner, with no agent, by
the grader with both fixes below. A regrade is not an exact reproduction. The saved tree has no
`.git`, so a file the agent committed while its own `.gitignore` matches it is left out. (The first
regrades also read the host's global git excludes, now turned off; the only global exclude,
`**/.claude/settings.local.json`, matches no file in these trees.) The first gradings stay in the rows
JSON, marked superseded and not counted.

| Run | Model | Reward | Checks (1-7) | Tokens in / cache write / cache read / out | Cost (list prices) | Turns | Agent s | Grading s | Wall s | Wall s without 1st build |
|---|---|---|---|---|---|---|---|---|---|---|
| P1-haiku-1-regrade | claude-haiku-5-5 | 0.0 | 0/7 (0000000) | 8,918 / 383,667 / 10,625,494 / 289,178 | $0.30 | 165 | 1,882.6 | 151.4 | 2,034.0 | 2,019.1 |
| P1-sonnet-1-regrade | claude-sonnet-5-5 | 0.4286 | 3/7 (1010001) | 114 / 128,048 / 4,534,270 / 83,609 | $2.06 | 58 | 1,349.3 | 162.2 | 1,511.5 | 1,492.5 |
| P1-opus-1-regrade | claude-opus-5-5 | 0.8571 (provisional) | 6/7 (1110111) | 192 / 208,595 / 12,125,930 / 117,748 | $5.82 | 120 | 1,689.1 | 158.4 | 1,847.5 | 1,833.1 |

Every run built twice with no change to an output, and every consumer read the grading replay to the
end (`stream_ok`). No API request stalled. Why each check failed:

- **Haiku**: fails mainly against the spec, not on a reading: its `oracle_map.yml` answers six checks
  with SQL over tables in the warehouse file `out/warehouse.duckdb`, which the spec puts out of bounds
  ("anything downstream reads only `out/marts/`"). Its one answer over a published mart (check 2) is
  over 2,000 times too large per person (unexplained, no trap).
- **Sonnet**: check 2 wrong under either county reading (its sums are not divided by population;
  unexplained); checks 5 and 6 name trap **W2**; check 4 below.
- **Opus**: check 4 below. Its 6/7 is **provisional**: it needed the `checks:` fix below, which was made
  after its output was seen (see "Grader defects and open readings").
- **Check 4 (Sonnet and Opus)**: both answer "for one month, county totals add up to state totals, and
  state totals add up to the source total" with a reconciliation query (totals and a mismatch count, or
  one row per state with `county_total = state_total`). The grader grades values, not the
  reconciliation alone: the key holds the month's county, state and source totals
  (`docs/plans/tasks/pipeline-traps.md`, check 4), and it reads them from rows at month, state and county
  grain (`no month column found`). The prompt may under-specify that check 4 asks for those rows.
  Opus's per-state rows are partly gradeable (state totals for one fixed month, with no month column
  and no county rows). Which shapes the key accepts is open (TASK-81 item 3), so the grade stands.

Cost: Claude Code's own `total_cost_usd` is $9.86 for the Haiku run (it prices `claude-haiku-5-5`,
which it does not recognise, far above list); the table uses token counts at `pricing.json` prices.

Clean room (`scripts/clean_room_check.py`, with `/trial`, `/tmp` and `/dev` allowed): no skill outside
the built-in list was shown or called, and no run touched a host configuration path. The verdict is
still `contaminated` for all three, because shell variables (`$D`, `$P`: the virtual environment's
package folders) and command tokens the check cannot resolve count as contacts. The stage-0 allowlist
for this runner is open (criteria-v2 §5.2).

### Harness defects found by these trials, and fixed

1. **Uncommitted work was deleted before grading.** The first Haiku run (`P1-haiku-void`, 2,637 s,
   $0.33 at list prices) built a working pipeline and never committed it (the prompt does not ask
   for it). The grader's `git clean -ffdx` deleted every new file, so `make build` failed and it
   scored 0. The run is void, not a model failure, and was run again. Fix: `--snapshot-worktree`.
   A Sonnet run started under the same grader was stopped after about 6 minutes and is also void
   (`P1-sonnet-aborted`; no transcript was kept).
2. **`checks:` beside other top-level keys was not read.** Opus's map has a `marts:` index beside
   `checks:`; the grader unwrapped `checks:` only when it was the only key, so it found no entry and
   scored 0 (`P1-opus-1`, as first graded). Fixed in `pipetask/oracle.py`; regraded: 6/7, provisional.
   (After the review of #31, a `checks:` key is unwrapped only when no top-level key is numbered, so a
   map of `check_1` to `check_7` with a stray `checks:` key still reads its seven entries.)

### Grader defects and open readings: the rule used here

A map shape is a **grader defect** only when the grader's contract as merged before these trials (the
`pipetask/oracle.py` docstring) says it accepts the shape and the code does not; it is fixed and every
affected run is regraded. Any other shape, and any other reading of a check, is an **open reading**
(TASK-81 items 1 and 3): the grader is not changed after seeing an arm's output, and the grade stands
until the owner decides. The `checks:` fix meets the first rule (the docstring said "optionally under
a top-level `checks:` key"), but it was made after seeing Opus's map, so Opus's P1 6/7 is provisional
until the owner confirms the contract.

## Step 3: one-shot trials on P2 (k = 1)

The same setup as P1, with the P2 prompt (Arrow, Polars, DataFusion, a YAML-driven engine) and image.

| Run | Model | Reward | Checks (1-7) | Tokens in / cache write / cache read / out | Cost (list prices) | Turns | Agent s | Grading s | Wall s | Wall s without 1st build |
|---|---|---|---|---|---|---|---|---|---|---|
| P2-haiku-1 | claude-haiku-5-5 | 0.0 | 0/7 (0000000) | 5,336 / 365,025 / 9,747,836 / 268,868 | $0.28 | 128 | 1,596.9 | 154.9 | 1,751.8 | 1,737.1 |
| P2-sonnet-1 | claude-sonnet-5-5 | 0.4286 | 3/7 (1010001) | 180 / 218,706 / 12,653,911 / 147,885 | $4.56 | 91 | 1,716.2 | 157.3 | 1,873.5 | 1,856.6 |
| P2-opus-1 | claude-opus-5-5 | 0.7143 | 5/7 (1010111) | 194 / 260,542 / 14,223,536 / 184,616 | $7.84 | 103 | 2,465.2 | 155.4 | 2,620.6 | 2,606.0 |

Again every run built twice with no change to an output, every consumer read the grading replay to
the end, and no API request stalled. Clean room as for P1: no skill outside the built-in list shown
or called, no host configuration touched; `contaminated` only by 1 to 3 unresolved shell tokens.

- **Haiku**: every entry of its `oracle_map.yml` nests the answer one level down
  (`answer: {view: chk_01_..., table: ..., columns: ...}`), a shape the grader does not read ("entry
  names no table or query"), and its `view` names are dbt views in `out/warehouse.duckdb`, not
  published marts. The nested shape is an open reading (TASK-81 item 1); the unpublished views are
  against the spec. The grade stands.
- **Sonnet**: the same three failures as on P1: check 2 (below), check 4 (the reconciliation reading,
  as on P1), checks 5 and 6 name trap **W2**.
- **Opus**: check 2 (below) and check 4 (the reconciliation reading).
- **Check 2 (Sonnet and Opus)**: the two runs give the same top ten, to the cent (21073 at 190.60
  per person, then 46065, 12073, ...). Every county in it holds a state capital (Franklin KY, Hughes SD,
  Leon FL, Thurston WA, Dauphin PA, Ingham MI, Sangamon IL, Cole MO, Lewis and Clark MT, Washington VT):
  the money is placed at the **recipient's** county (state governments receive the grants). The key
  places it at the **place of performance** (`pipetask/key.py`). Whether recipient location is an
  accepted reading of "where did the money go" is open (TASK-81 item 3), so the grade stands. The
  reading is linked to check 4: placing money by recipient also changes the month's county and state
  totals that check 4 compares with the key.

## Step 3: one-shot trials on P3 (k = 1)

The same setup, with the P3 prompt (Scala 2.13 and Spark, dbt-spark) and the `runner-pipeline:p3` image.

| Run | Model | Reward | Checks (1-7) | Tokens in / cache write / cache read / out | Cost (list prices) | Turns | Agent s | Grading s | Wall s | Wall s without 1st build |
|---|---|---|---|---|---|---|---|---|---|---|
| P3-haiku-1 | claude-haiku-5-5 | 0.0 | 0/7 (0000000) | 6,713 / 628,852 / 12,000,959 / 361,671 | $0.38 | 209 | 3,756.4 | 406.0 | 4,162.4 | 4,053.6 |
| P3-sonnet-1 | claude-sonnet-5-5 | 0.7143 | 5/7 (1010111) | 158 / 363,739 / 8,177,864 / 113,443 | $3.68 | 78 | 2,171.2 | 393.3 | 2,564.5 | 2,468.7 |
| P3-opus-1 | claude-opus-5-5 | 0.4286 | 3/7 (1010001) | 192 / 585,989 / 12,257,988 / 126,966 | $7.92 | 104 | 3,602.7 | 375.1 | 3,977.8 | 3,876.7 |

Every run built twice with no change to an output (on the image's warm caches, offline), every
consumer read the grading replay to the end, every grading run finished inside the P3 deadline (537 s),
and no API request stalled. Clean room as before (no skill outside the built-in list, no host
configuration; 1 to 9 unresolved tokens, and Haiku's one search of `/`, which inside the container holds
no user-level configuration and cannot read the grader's directory).

- **Haiku**: fails mainly against the spec, as on P1: the views its map names are dbt views that are
  not published under `out/marts/`, and it puts the path of each view's file under `sql:`
  (`transform/models/checks/...sql`), which the grader runs as SQL.
- **Sonnet**: check 2 (the recipient-county reading, the same top ten as on P2) and check 4 (the
  reconciliation reading, here two queries under one `sql:` mapping).
- **Opus**: check 2 (the recipient-county reading; its summary says so: "a county view by place of
  performance would leave most of the money unassigned"), check 4 (the reconciliation reading), check 5
  (trap **W2**: it counts every change event, log and categorize included, as an edit, and says so),
  and check 6 (unexplained).

## All nine trials

| Task | Model | Reward | Checks | Cost | Agent s | Wall s (w/o 1st build) |
|---|---|---|---|---|---|---|
| P1 | Haiku 5.5 | 0.0 | 0/7 | $0.30 | 1,882.6 | 2,034.0 (2,019.1) |
| P1 | Sonnet 5.5 | 0.4286 | 3/7 | $2.06 | 1,349.3 | 1,511.5 (1,492.5) |
| P1 | Opus 5.5 | 0.8571 (provisional) | 6/7 | $5.82 | 1,689.1 | 1,847.5 (1,833.1) |
| P2 | Haiku 5.5 | 0.0 | 0/7 | $0.28 | 1,596.9 | 1,751.8 (1,737.1) |
| P2 | Sonnet 5.5 | 0.4286 | 3/7 | $4.56 | 1,716.2 | 1,873.5 (1,856.6) |
| P2 | Opus 5.5 | 0.7143 | 5/7 | $7.84 | 2,465.2 | 2,620.6 (2,606.0) |
| P3 | Haiku 5.5 | 0.0 | 0/7 | $0.38 | 3,756.4 | 4,162.4 (4,053.6) |
| P3 | Sonnet 5.5 | 0.7143 | 5/7 | $3.68 | 2,171.2 | 2,564.5 (2,468.7) |
| P3 | Opus 5.5 | 0.4286 | 3/7 | $7.92 | 3,602.7 | 3,977.8 (3,876.7) |

Spend at list prices: $32.84 for the nine graded trials, plus $0.33 for the void Haiku run and an
unrecorded six minutes of the aborted Sonnet run. No trial passed every check (reward 1.0), so at k = 1
every cell fails the M1 bar; these runs say nothing yet about reliability. No API request stalled, and
no run reached the guard cap. Every row is in `2026-10-15-pipeline-trials.json`. Only rows with
`counted: true` are results (the nine above): void runs, first gradings superseded by a regrade, and
the diagnostic regrade are kept with `counted: false` and never count as model failures.

Every delivered pipeline built twice with no change and consumed the stream exactly as the gates
require. The checks failed for these reasons:

1. **Haiku answered against the spec.** On P1 and P3 its maps read the warehouse file and unpublished
   dbt views, which the spec rules out. On P2 the map also has a nested shape (an open reading, TASK-81
   item 1). Diagnostic only (`P2-haiku-1-flatmap-regrade`, not a result): with its P2 map edited by
   hand, the `answer:` level lifted **and** the unpublished view names dropped, the delivery scores 3/7
   (checks 1, 6, 7). Both edits were needed, so the shape alone does not account for the 0.
2. **Check 2: recipient county or place of performance** (TASK-81 item 3). The reading decides 4 of the
   six Sonnet and Opus runs (P2 and P3, both models). P1 Sonnet fails check 2 under either reading, and
   P1 Opus uses the place of performance and passes.
3. **Check 4: rows or a reconciliation** (TASK-81 item 3, linked to check 2). Every Sonnet and Opus run
   answers with a reconciliation query; the key grades the month's totals, read from rows at month,
   state and county grain, and the prompt may under-specify that.
