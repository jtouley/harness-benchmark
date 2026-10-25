# Grader v3: regrade of every stored tree (2026-10-25)

Grader v3 is defined by the postmortem front matter's Grading section (owner, 2026-10-24) and described in
[grading.md#grader-v3](../../method/grading.md#grader-v3). This page is the regrade of every stored run tree
that holds agent work, under the pinned grader and under v3, with every check that changed and why. No
benchmark run was made. Nothing here changes a record or appends a score: `runs/*/scores.jsonl` gets the v3
lines only once the owner has reviewed this and the grader is merged.

Score = round(reward × 7). Reward is 0 when `stream_ok` or idempotency fails (unchanged in v3), so a run can
pass more checks and still score 0.

## Regrade table

| Run | Official | Pinned regrade | v3 | Checks pinned → v3 | Per-check change and reason |
|---|---|---|---|---|---|
| `20261023-P1-oneshot-sonnet-1-r2` (rebuilt) | 5/7 | 5/7, reproduced | **5/7** | `P.P.PPP` → `P.P.PPP` | none. 2: the top ten differ from the key (data; the shapes-r2 survey attributes it to placing money by recipient county, inferred, not rechecked here). 4: the SQL returns three scalar sums, no county or state rows |
| `20261023-P1-oneshot-haiku-1` (rebuilt) | 5/7 | 5/7, reproduced | **5/7** | `P.P.PPP` → `P.P.PPP` | none. 2: the SQL returns county names without a county code. 4: three scalar sums |
| `20261024-P1-cadence-haiku-core-6` | 4/7 | 4/7, reproduced | **7/7** | `P...PPP` → `PPPPPPP` | 2: `how` "sum net_obligations by county_fips ..., divide by county_population_2024" read (pinned: no per-person column constant per county in a monthly mart). 3: "count rows where net_obligations < 0" read: 1122 (pinned counted all 7918 rows). 4: month, county and state columns found by value among the named columns (pinned missed the county column: 54% of its rows hold `UNKNOWN` as the county, so county codes fell under its 50% share threshold) |
| `20261024-P1-cadence-haiku-core-5` | 0/7 | 0/7, reproduced | **0/7** (4 checks) | `P......` → `PPPP...` | 2: sum by county_fips, divide by population read. 3: "Count the rows where is_net_negative is true" read: 1122 (pinned 7918). 4: named columns by value, as core-6. Reward 0: `stream_ok` false |
| `20261024-P1-cadence-haiku-core-4` | 0/7 | 0/7, reproduced | **0/7** (3 checks) | `PP.....` → `PPP....` | 3: `note` "Count the rows with net_obligations below zero" read: 1122. Reward 0: `stream_ok` false. Unresolved: 4 (`note` names two more marts to read), 6 ("per window": no such column) |
| `20261024-P1-cadence-haiku-full-6` | 2/7 | 2/7, reproduced | **3/7** | `P.....P` → `P.P...P` | 3: `aggregation` "sum per award_key, then count the awards whose sum is below zero" read: 1122 (pinned counted 9820 transaction rows) |
| `20261024-P1-cadence-haiku-full-4` | 0/7 | 0/7, reproduced | **0/7** (3 checks) | `PPP....` → `PPP....` | none. Reward 0: `stream_ok` false; the stream marts its SQL names were never published |
| `20261024-P2-cadence-haiku-core-6` | 2/7 | 2/7, reproduced | **5/7** | `P....P.` → `P.P.PPP` | 3, 5, 7: the entry's own query (`queries: {answer: ...}`) is read; pinned read the bare table and ignored it. 3: awards with a negative sum, 1122. 5: per wiki and actor, every consumed edit. 7: rows where `late`, 60 (pinned counted all 12876 rows of fct_edit). Unresolved: 4 (three queries, none named `answer`) |
| `20261024-P2-cadence-haiku-full-5` | 0/7 | 0/7, reproduced | **1/7** | `.......` → `P......` | 1: `out/marts/mart_fy2024_monthly/data.parquet` resolves to that mart and `rows: grain = 'agency'` is applied (pinned: "no published mart named ..."). Still failing: 3, 5, 7 name `out/warehouse.duckdb`, outside out/marts (rule unchanged); 6 unresolved ("summed over namespace and actor_type per window"); 4 `grain = 'county' and grain = 'state'` selects no row |
| `20261024-P2-cadence-haiku-full-6` | 2/7 | 2/7, reproduced | **2/7** | `P.P....` → `P.P....` | none |
| `20261024-P2-cadence-haiku-full-4` | 0/7 | 0/7, reproduced | **0/7** (3 checks) | `P......` → `PPP....` | 2: sum per county_fips, divide by population read. 3: "count rows where is_net_negative" read. Reward 0: `stream_ok` false. 4 still fails on data: counties 09110, 09180, 72021, 72113, 72127 missing |
| `20261024-P2-cadence-haiku-core-5` | 0/7 | 0/7, reproduced | **0/7** (3 checks) | `PPP....` → `PPP....` | none. Reward 0: `stream_ok` false |
| `20261024-P2-cadence-haiku-core-4` | 0/7 | 0/7, reproduced | **0/7** (3 checks) | `PP.....` → `PPP....` | 3: "count(*) where net_obligation < 0" read. Reward 0: `stream_ok` false. Unresolved: 4, 6 (a join to dim_wiki) |
| `20261024-P2-cadence-haiku-core-2` | 0/7 | 0/7, reproduced | **0/7** | `.......` → `.......` | none: the stored HEAD is the starting repository (no oracle_map.yml) |

Every row's v3 resolution of all seven checks, the pinned reason of each changed check, and the official
score's grader commit: [regrade.json](regrade.json).

## Every point v3 gains is the answer key's answer, found in the run's own marts

v3 gains 15 checks across 8 runs. [crosscheck_gains.py](tools/crosscheck_gains.py) recomputes each one with
hand-written DuckDB SQL over the same published marts, using no pipetask code, and compares it with the
key's primary answer: all 15 match ([crosscheck-gains.txt](crosscheck-gains.txt)). The answer check itself
did not change: `_verdict`, the key, the accepted readings and traps, money to the cent and exact counts are
the pinned grader's (`git diff` of grade.py: only check 4's column roles and the call into the map reader).
No check the pinned grader passed fails under v3 (tests/test_pipeline_grader_v3.py asserts it per fixture).

## How each tree was graded

- Pinned grader: `c344bea` (`golden/pipeline/pipetask` tree `8a0977e`, the same tree as every official
  score's grader commit: c344bea, 4132b0c, 563a74c, caa48be). Run as the driver runs it,
  `scripts/host_trial.py grade` from the repository root (`--snapshot-worktree`, seed 1, deadline 600 s):
  build twice, stream twice against the replay, grade. [regrade_one.sh](tools/regrade_one.sh).
- Every trial ran in its own network namespace with loopback only ([lo_up.py](tools/lo_up.py)): no external
  network, and its own port 8099, so no trial met another process on the replay port. `UV_OFFLINE=1`.
- v3 graded the marts that same trial left (`pipetask.grade` from the repository root), so the change per
  check is the grader's alone; `trial.py` is unchanged, so `stream_ok` and idempotency carry over.
- Per run in [runs/](runs/): `pinned-trial.json` (the trial's full JSON), `pinned-marts.json` and `v3.json`
  (the two graders on the same marts), `grade-logs/` (build and stream logs), `regrade.log`. In
  `regrade.log` the column labelled `v3` was written before the v3 code existed and equals the pinned
  grader; `v3.json` is grader v3.
- Trees: each record's tree bundle from `runs-store`, sha256 checked. None of these bundles has
  `refs/graded/<run>` (they predate harness #128), so the bundle's HEAD was graded. All 12 Cadence regrades
  reproduce the official passed count, reward, `stream_ok` and idempotency exactly.

## The two Oct 23 one-shots, rebuilt from their transcripts

Their bundles hold only the starting repository (the one-shots never commit). [replay_tree.sh](tools/replay_tree.sh)
and [replay_transcript.py](tools/replay_transcript.py) rebuild the tree: the starting repository from the
bundle, then every tool call of the transcript in order (Write, Edit, and each Bash command from the cwd the
session had, with its rule that a cwd outside the repository resets to it), inside a private mount and
network namespace in which the run's own path, `/home/user/bf/runs/<run>/repo`, is the rebuild and `/tmp` is
empty. Commands that run the pipeline, fetch, wait or kill (`make`, `uv`, `dbt`, `curl`, `sleep`, `pkill`,
`nohup`) do nothing and are logged: they write only ignored outputs. `replay.jsonl` lists every call, its
exit code beside the original's `is_error`, and what was skipped. Every mismatch was read: the part that
fails reads something the rebuild does not have (a stream capture, the venv, `lake/` or `out/`, the live
replay); where the same command also writes source, the write comes first and ran. The rebuild is accepted
on the score check below, not on this reading.

| Run | Official | Rebuild under the pinned grader | Reproduced |
|---|---|---|---|
| `20261023-P1-oneshot-sonnet-1-r2` | 5/7 (passed 5, reward 0.7143, stream_ok, idempotent) | 5/7 (passed 5, reward 0.7143, stream_ok, idempotent) | yes |
| `20261023-P1-oneshot-haiku-1` | 5/7 (passed 5, reward 0.7143, stream_ok, idempotent) | 5/7 (passed 5, reward 0.7143, stream_ok, idempotent) | yes |

Both are in the table. The official scores record no per-check result, so only the totals can be matched;
the rebuilds' failing checks (2 and 4) agree with the shapes-r2 survey's finding that both one-shots placed
money by recipient county.

## Not regraded

- `20261023-P1-cadence-haiku-1-r2`, `20261024-P1-cadence-haiku-it1-1-r2`, `20261024-P2-cadence-haiku-full-2`,
  `20261024-P2-cadence-haiku-full-3`: their bundles hold only the starting repository (no agent work), and
  rebuilding from transcripts is limited to the Oct 23 one-shots. Their official scores are 0/7.
- The Oct 15 one-shots and the Oct 19 to 22 benchmark runs: no tree is stored (the Oct 15 trees are on the
  operator's laptop).
- `20261024-P2-cadence-haiku-core-2` is graded as stored: its HEAD is the starting repository; the agent's
  commits are only on the side branch `cadence/spec-e1-backup`, which was not what the run delivered.

## Golden samples

[golden/pipeline/fixtures/grader-v3/](../../../golden/pipeline/fixtures/grader-v3/): for the 13 trees with a
map, the delivered `oracle_map.yml` byte for byte and every published mart it names, as the pinned trial
left them ([build_fixtures.py](tools/build_fixtures.py)), with `expected.json` (the tree and transcript blobs,
the graded snapshot commit, the pinned result per check, v3's result and resolution per check,
[add_v3_expected.py](tools/add_v3_expected.py)). The pinned grader on the fixtures gives each tree's trial
result exactly. The tools in [tools/](tools/) are the scripts used, with this session's scratch paths in them.

## ci_local

[ci_local-7821c02.txt](ci_local-7821c02.txt): `scripts/ci_local.sh` at 7821c02 (the grader, fixtures and
this regrade), its own TMPDIR, `UV_OFFLINE=1` and every proxy pointed at a closed local port, so no external
request left the machine: OK, with the steps that need github.com or Claude Code 2.1.294 skipped as the script
reports. The pull request gives the run at its head.
