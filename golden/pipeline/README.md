# Pipeline task family: builder files (hidden from arms)

Inputs, replay server, answer key, grader and reference solutions for the
[pipeline family](../../docs/tasks/pipeline-family.md) (P1, P2, P3; issue #11). Increment 1 built
the shared inputs, the key, the grader and the P1 reference; increment 2 adds the P2 skeleton, prompt
and reference, graded by the same grader against the same key. P3 has no skeleton or reference yet.

**Nothing in this folder goes into a trial except `<task>/skeleton/` and `data/raw/`**, which
`pipetask/assemble.py` copies into the starting repository. The task prompt is passed separately.
The capture, the replay server code, the key, the grader, the references and this page stay out.

| Path | What | In a trial |
|---|---|---|
| `data/raw/` | Frozen batch inputs: USAspending FY2024 transactions for four agencies (archive zips as served), Census county estimates (vintages 2024 and 2021), the Wikimedia site matrix | Copied into the repo as `data/raw/` |
| `data/capture/recentchange.jsonl.gz` | One hour of the live `recentchange` stream, nine wikis plus canary events, byte for byte | Served only through the replay server |
| `data/MANIFEST.json` | sha256, size and source of every file under `data/` | No |
| `snapshot/` | `fetch_inputs.py`, `capture_stream.py`, `freeze_capture.py`: how `data/` was made | No |
| `pipetask/schedule.py`, `pipetask/replay.py` | Replay server and its seeded fault schedule (F1 to F5) | Runs as a service (`replay.pyz`), its files unreadable to the agent |
| `pipetask/key.py`, `key/answer_key.json` | Answer key and the wrong answer of each single trap, computed independently of any reference | No (inside `grader.pyz`, copied in after the agent) |
| `pipetask/oracle.py`, `pipetask/grade.py`, `pipetask/trial.py` | Grader: resets the repo to its committed tree (`git clean -ffdx`, then `out/` and `lake/` removed), runs `make build` twice and `make stream` twice against the replay, checks the seven answers. The map's SQL can read only `out/marts/` (DuckDB `allowed_directories`, external access off, settings locked). Reward 0 when a second build changes an output, no `make stream` run exits 0, or no run read the grading replay up to the end of the late batch (the stream answers do not depend on the seed, so marts left from development would match). The reset covers the repository only: state kept under `$HOME`, such as dlt's default `~/.dlt/pipelines/`, survives it, so the runner should give the grader's `make` a fresh `HOME` | No (inside `grader.pyz`) |
| `pipetask/prompt.py`, `P1/prompt.md`, `P2/prompt.md` | Each prompt, word for word from the specs (shared request plus the task's stack section) | Passed as the prompt |
| `P1/skeleton/` | `Makefile` (both targets fail), `pyproject.toml` and `uv.lock` (pinned dlt, dbt-core, dbt-duckdb, duckdb), empty dbt project with `profiles.yml` | Copied into the repo |
| `P1/reference/` | The P1 reference solution (dlt, DuckDB, dbt-duckdb, Parquet lake), an overlay on the skeleton | **Never** |
| `P2/skeleton/` | The same layout as P1's, pinning pyarrow, polars, datafusion, dbt-core, dbt-duckdb, duckdb | Copied into the repo |
| `P2/reference/` | The P2 reference solution: a YAML-driven engine (`engine/`, schema in `engine/pipeline.schema.yml`) running `pipelines/batch.yml` and `pipelines/stream.yml` on Arrow, Polars and DataFusion into the Parquet lake, then dbt-duckdb (the P1 models, adapted to this lake's load metadata). An overlay on the skeleton; it adds `pyyaml` and `jsonschema` (already in the lock through dbt-core) as direct dependencies | **Never** |
| `pipetask/bundle.py` | Builds `replay.pyz` and `grader.pyz`, the two files a trial container needs | — |

## Commands

All of them run in a project virtual environment (`uv run`); nothing is installed on the host.

```sh
cd golden/pipeline
# the starting repository of a trial (what run_trial.sh --repo gets)
python3 -m pipetask.assemble P1 --out /tmp/p1-repo
# the replay server for development (any seed)
python3 -m pipetask.replay --capture data/capture/recentchange.jsonl.gz --seed 0
# grade a delivered repository: build twice, stream twice, check
uv run --project ../.. python -m pipetask.trial --repo /tmp/p1-repo \
    --key key/answer_key.json --capture data/capture/recentchange.jsonl.gz
# the reference, end to end (P1 or P2)
python3 -m pipetask.assemble P1 --out /tmp/p1-ref --with-reference
uv run --project ../.. python -m pipetask.trial --repo /tmp/p1-ref \
    --key key/answer_key.json --capture data/capture/recentchange.jsonl.gz
# regenerate the key after any change to data/ or the schedule (tests fail until you do)
uv run --project ../.. python -m pipetask.key --raw data/raw \
    --capture data/capture/recentchange.jsonl.gz --seed 1 --out key/answer_key.json
uv run --project ../.. python -m pipetask.manifest
```

The full reference trials are also tests (both tasks, plus P2's generality, validation and crash
recovery checks): `HB_PIPELINE_REFERENCE=1 uv run --frozen --python 3.12 --with tokenizers python -m pytest tests/test_pipeline_reference.py`.

Measured on the test laptop (Apple Silicon, uv cache warm): the P2 reference's first `make build`
takes 16.5 s (most of it the virtual environment), the second 3.5 s; the full trial (two builds, two
stream runs of 30 s and 90 s, grading) 152 s. Result: 7 of 7 checks, reward 1.0, no output changed
by the second build.

## A trial on the isolated runner

The runner (`runner/`, PR #23) is not on `main` yet, so it is not wired. A trial will be:

```sh
python3 -m pipetask.assemble P1 --out /tmp/p1-repo
python3 -m pipetask.bundle --out /tmp/p1-dist          # replay.pyz, grader.pyz
runner/run_trial.sh --repo /tmp/p1-repo --prompt golden/pipeline/P1/prompt.md \
    --grader /tmp/p1-dist/grader.pyz --model <model> [--plugin-dir <arm>] --out results/runs/<trial>
```

Three runner changes are needed for this family (left for the wiring step):

1. **The dev replay server.** Before the agent starts, the entrypoint copies `replay.pyz` to a
   root-only path (mode 0700) and starts `python3 replay.pyz --seed <dev seed>` as root on port 8099,
   so the arm can develop against `http://localhost:8099/v2/stream/recentchange`. The grading seed
   (in the key) must differ from the dev seed. After the agent phase, the entrypoint stops it, so the
   grader can serve the grading seed on the same port.
2. **Time caps.** The grader runs `make build` twice and `make stream` twice (30 s and 90 s by default),
   plus a dependency install. Its own caps are `--build-timeout` per build (default 1800 s) and
   DURATION + 300 s per stream run, so its worst case is 2 × 1800 + 330 + 390 = 4,320 s. The runner's
   `--grader-timeout` must be above that, or the grader must get a smaller `--build-timeout`; otherwise a
   slow candidate is killed by the runner and leaves no JSON instead of being graded. The current
   default, `--grader-timeout 900`, is below that worst case.
   The agent cap for this task is an owner decision (the family is meant to exceed one session).
3. **The candidate's `make` runs unprivileged.** The grader runs the delivered `make build` and
   `make stream`. It reads the answer key from `grader.pyz` into memory and never writes it to disk,
   but the archive itself holds the key. So the runner keeps `grader.pyz` (and the grader's temporary
   directory) owned by root with mode 0700, and runs the candidate's `make` as the unprivileged agent
   user, not as the grader's user. Until then, a Makefile written in the agent phase could read the
   archive (PR #26 review, F-02).

## What the key fixes that the spec leaves open

The grader accepts more than one reading where the spec is ambiguous (each check's `accepted` in the
key); the reference uses the first.

| Point | Primary (reference) | Also accepted |
|---|---|---|
| Event time of an edit | `timestamp` | `meta.dt` |
| What moves the watermark of the spec's lateness rule (the rule itself is in the spec) | Every non-canary event that parses | Canaries, non-edit events and the invalid frame moving it, or not: all eight readings give the same 60 late events (`late_rule` in the key), so none needs its own answer |
| Check 7 counts late edits or every late event? | Late edits (`edit`, `new`) | Late events of any type |
| Check 6 label of a window | Its start | Its end |
| "Latest earlier estimate" for Connecticut's former counties | POPESTIMATE2021 from vintage 2021 | — |
| Territories (no county estimate in either file) | No per-person value; left out of the ranking | — |
| Transactions with no state | One `unknown` member; counted in the source total | Any representation that sums to it |

## Traps the frozen data does and does not reproduce

A trap is reproduced for a check when its single wrong answer (computed by `pipetask/key.py`) differs
from the key, so the grader can name it. Grading seed 1. Source: `key/answer_key.json`.

| Check | Reproduced | Not reproduced, and why |
|---|---|---|
| 1 | B1, B2, B6, B7 | B8: float sums of these amounts round back to the right cents |
| 2 | B3, B6, B7, S1 | B4: no Connecticut place is in the top ten (B4 shows in check 4) |
| 3 | B2, B6 | — |
| 4 | B4, B5, B7 | B8, as in check 1 |
| 5 | W1, W2, W4, W5, F2, F5, S3 (`S3-drops`: late edits dropped) | S3 and F4 as "late edits added to their window": check 5 counts every edit either way |
| 6 | S3, F4, F5, F2, W2 | W3 (local time): the grading container runs in UTC, so local time is UTC |
| 7 | S3, F4, F5 | F2: the re-sent frames arrive right after each disconnect, at the current watermark, so they are not late and an F2 consumer still counts 60 |

Not computable offline, so a failure they cause is "unexplained" and goes to the audit: F1 and F6
(how much is counted twice depends on when the consumer stops), F3 (assigning windows by wall-clock
arrival depends on the replay's timing).

Data facts behind the traps: 9,820 transactions on 7,918 awards; 1,226 negative transactions; 7,781
with no county and 57 with no state (foreign places among them); Connecticut appears under six former
county codes and three planning-region codes; 13 county codes have no 2024 estimate (the six
Connecticut counties and seven territory codes). The capture has 21,502 frames over 3,600 s from nine
wikis, two canary events (which carry only `meta`), and SSE ids whose two data-centre entries do not
always advance together. The CSV quirks a loader meets: quoted values that span lines (USAspending)
and Latin-1 text (Census).

## P2 stack traps on the pinned versions

The P2 page says each stack trap is a claim about the pinned versions, checked when the reference is
built. Checked with pyarrow 26.0.0, polars 2.0.0 and datafusion 55.0.0 on the frozen data:

| Trap | Reproduced | Evidence |
|---|---|---|
| A1 | Yes | `polars.read_csv` and `pyarrow.csv.read_csv` both infer `STATE` and `COUNTY` of the Census file as Int64 (`01` becomes `1`). The reference reads every CSV column as text |
| A2 | No | Casting `federal_action_obligation` to Float64 and summing gives the same cents as the decimal sum, per agency and per month and county (as for B8). The grader cannot name it; it stays a design-review point |
| A3 | Yes | An inner join on a key with a NULL on both sides drops that row in Polars (default `join`) and in DataFusion SQL. The reference never joins on a NULL key: transactions without a county get an unknown member of the place dimension |
| A4 | By design | The engine writes a micro-batch's files, then replaces the checkpoint by an atomic rename, and on start deletes files above the checkpoint. `test_the_p2_stream_commit_drops_a_batch_that_never_committed` simulates the crash; F6 (two `make stream` runs) exercises the resume |
| A5 | Not graded yet | The generality check is not in `pipetask/trial.py` (open point 1 below). `test_the_p2_engine_runs_a_pipeline_it_has_never_seen` runs it against the reference |

Polars 2.0 removed the cast from text to `Date` (`str.to_date` replaces it). An arm that writes
`cast(pl.Date)` gets an error at once, not a wrong answer, so it is not a trap.

## Open points of increment 2 (for the owner)

Gaps in the P2 page that the reference had to fill; the shared spec and the prompts are unchanged.

1. **How the grader runs the generality check.** The page says the grader adds a third pipeline file
   and it must "land the right rows", but not where the file goes, what command runs one file (the
   reference uses `python -m engine run pipelines/<file>.yml`; an arm may choose anything), what lake
   table name to expect, or whether the check is an eighth check in the reward. Until then the grader
   scores P2 on the seven shared checks only, and the reference's generality is a test, not a grade.
2. **No skeleton section.** P1's page describes its skeleton; P2's does not. The P2 skeleton copies
   P1's layout and pins dbt-core, dbt-duckdb and duckdb at P1's versions besides the three the page
   names. The stack section also does not say "do not change the versions", as P1's does.
3. **"A new source or mart … needs YAML only."** In the shared architecture every mart is a dbt model,
   so a mart never needs engine code anyway. Probably "a new source or lake table" is meant.
4. **A2 does not reproduce** on the frozen data (table above). The page says such a trap is removed.
5. **A3 assumes joins on the engine side.** The architecture puts every join in dbt, where DuckDB
   drops NULL keys in the same way; the trap as written applies only to an arm that joins in the
   engine.
6. **"Commits the position in the same step as the data"** is exact only for one sink. With two (the
   events and the frames that are not JSON) the reference commits files then a checkpoint, and deletes
   uncommitted files on start. The page does not say whether that, or one sink per stream, is meant.
