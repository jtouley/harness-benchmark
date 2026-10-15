# Pipeline task family: builder files (hidden from arms)

Inputs, replay server, answer key, grader and reference solutions for the
[pipeline family](../../docs/tasks/pipeline-family.md) (P1, P2, P3; issue #11). Increment 1 built
the shared inputs, the key, the grader and the P1 reference; increment 2 adds the P2 skeleton, prompt
and reference; increment 3 the P3 skeleton, prompt, reference and toolchain image. All three are graded
by the same grader against the same key.

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
| `pipetask/prompt.py`, `P1/prompt.md`, `P2/prompt.md`, `P3/prompt.md` | Each prompt, word for word from the specs (shared request plus the task's stack section) | Passed as the prompt |
| `P1/skeleton/` | `Makefile` (both targets fail), `pyproject.toml` and `uv.lock` (pinned dlt, dbt-core, dbt-duckdb, duckdb), empty dbt project with `profiles.yml` | Copied into the repo |
| `P1/reference/` | The P1 reference solution (dlt, DuckDB, dbt-duckdb, Parquet lake), an overlay on the skeleton | **Never** |
| `P2/skeleton/` | The same layout as P1's, pinning pyarrow, polars, datafusion, dbt-core, dbt-duckdb, duckdb | Copied into the repo |
| `P2/reference/` | The P2 reference solution: a YAML-driven engine (`engine/`, schema in `engine/pipeline.schema.yml`) running `pipelines/batch.yml` and `pipelines/stream.yml` on Arrow, Polars and DataFusion into the Parquet lake, then dbt-duckdb (the P1 models, adapted to this lake's load metadata). An overlay on the skeleton; it adds `pyyaml` and `jsonschema` (already in the lock through dbt-core) as direct dependencies | **Never** |
| `P3/skeleton/` | `Makefile` (both targets fail), `build.sbt` (Scala 2.13.18, Spark 3.5.9, ScalaTest 3.2.20) and `project/build.properties` (sbt 1.12.15), `requirements.txt` (dbt-core 1.11.6, dbt-spark 1.11.0, pyspark 3.5.9 and their whole closure, with hashes), empty dbt project with a dbt-spark `session` profile | Copied into the repo |
| `P3/reference/` | The P3 reference solution: a Spark batch job (`pipeline.Batch`), and an SSE reader feeding Spark Structured Streaming through a spool (`pipeline.Stream`), into the Parquet lake; ScalaTest suites; dbt-spark models (the P1 models in Spark SQL). An overlay on the skeleton | **Never** |
| `P3/image/` | The P3 toolchain image (`Dockerfile`: JDK 17, Python 3.12, sbt, both base images pinned by digest) and `trial.sh`, which runs a P3 trial inside it | No (the image is the trial's environment) |
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
# P3 runs in its toolchain container (needs only docker): assemble, build, stream, grade
golden/pipeline/P3/image/trial.sh /tmp/p3-out --with-reference --scalatest   # -> /tmp/p3-out/result.json
# the reference, end to end (P1 or P2)
python3 -m pipetask.assemble P1 --out /tmp/p1-ref --with-reference
uv run --project ../.. python -m pipetask.trial --repo /tmp/p1-ref \
    --key key/answer_key.json --capture data/capture/recentchange.jsonl.gz
# regenerate the key after any change to data/ or the schedule (tests fail until you do)
uv run --project ../.. python -m pipetask.key --raw data/raw \
    --capture data/capture/recentchange.jsonl.gz --seed 1 --out key/answer_key.json
uv run --project ../.. python -m pipetask.manifest
```

The full reference trials are also tests (all three tasks, plus P2's generality, validation and crash
recovery checks, and P3's ScalaTest suites; P3 needs docker): `HB_PIPELINE_REFERENCE=1 uv run --frozen --python 3.12 --with tokenizers python -m pytest tests/test_pipeline_reference.py`.

Measured on the test laptop (Apple Silicon, uv cache warm): the P2 reference's first `make build`
takes 16.5 s (most of it the virtual environment), the second 3.5 s; the full trial (two builds, two
stream runs of 30 s and 90 s, grading) 152 s. Result: 7 of 7 checks, reward 1.0, no output changed
by the second build.

Measured for P3 the same way, in its container on the test laptop (Docker Desktop, 8 CPUs, with other
containers running beside it; download caches warm in the `hb-p3-cache` volume): the first `make build`
takes 147 s (about 60 s of it the virtual environment), the second 85 s; the two stream runs 129 s
and 210 s; the whole trial, with the image build and the ScalaTest suites, 11 min. Result: 7 of 7
checks, reward 1.0, no output changed by the second build. Expect less on the x86-64 runner.

## A trial on the isolated runner

The runner (`runner/`) is wired for the three tasks. `scripts/pipeline_trial.py` assembles the
starting repository, bundles `replay.pyz` and `grader.pyz`, and calls `runner/run_trial.sh` with the
task's image and caps from `runner/pipeline/caps.json`:

```sh
runner/pipeline/build.sh                     # the trial images: runner-pipeline:py (P1, P2), :p3
python scripts/pipeline_trial.py run P1 --model claude-haiku-5-5 --out results/runs/pipeline/P1-haiku-1
python scripts/pipeline_trial.py run P1 --mode reference --out results/runs/pipeline/P1-ref-1   # smoke
python scripts/pipeline_trial.py run P1 --mode skeleton --out results/runs/pipeline/P1-skel-1   # control
python scripts/pipeline_trial.py caps P1 results/runs/pipeline/P1-ref-*      # grader caps from references
python scripts/pipeline_trial.py summary results/runs/pipeline/*              # the results table
```

How each runner change listed for this family is done:

1. **The dev replay server.** `run_trial.sh --replay replay.pyz` copies it into `/opt/hb-replay/`
   (root, mode 0700) before the container starts. The entrypoint starts it as root on
   `localhost:8099` with `--replay-seed` (default 0; the grading seed in the key is 1), waits for the
   port, and stops it after every agent process is killed, so the grader can serve the grading seed on
   the same port. Its log is `replay-dev.log`.
2. **Time caps.** The grader's caps are passed to it (`--build-timeout`, and `--stream-grace`, the time
   a `make stream` run may take beyond its DURATION, default 300 s), and the runner's `--grader-timeout`
   is above their sum. A grader killed at the runner's cap still leaves a `grade.json`:
   `{"error": "the grader was killed at its cap of N s", "reward": 0.0}`. The values are in
   `runner/pipeline/caps.json`, with the measurements they come from (below).
3. **The candidate's `make` runs unprivileged.** `run_trial.sh` copies the grader into
   `/opt/hb-grader/` (root, mode 0700), and the grader runs as root with
   `--make-user agent --make-env-file /opt/hb/toolchain.env`: every `make` runs as the agent user
   (`setpriv`), with exactly the image's toolchain variables and a fresh, empty HOME that its four runs
   share and that is removed afterwards (state under `~/.dlt/` from development is gone). The grader's
   temporary directory (the capture) is root's, mode 0700, and the key stays in its memory. While the
   grader runs, the agent user has no network beyond loopback (`iptables` owner match), so the build
   can use only the image's caches. `tests/test_runner.py` checks each point in a container.

### Decisions for the runner (default, owner may change)

From TASK-81; each is the owner's default for these first trials and may change.

- **Toolchain: a cache pre-warmed in the trial image** (TASK-81 item 14). `runner/pipeline/Dockerfile`
  builds the images from the three skeletons only: Python 3.12 and both uv locks (P1, P2) in the uv cache;
  for P3 also JDK 17, sbt, the Spark/Scala/ScalaTest closure in the coursier and ivy caches, and the
  dbt-spark closure (the files PyPI serves, so the hashes match) in a wheelhouse. No package index is
  read during a trial: the toolchain sets `UV_OFFLINE`, `PIP_NO_INDEX`, `COURSIER_MODE=offline` and
  `sbt.offline` for the agent and the grader, and the grader's `make` has no network at all. During the
  agent's session the offline switches are variables, not a firewall (the agent needs the API).
- **The warm cache does not count against the agent's loop cost.** The results report wall time with
  and without the first `make build` of grading (the one that builds the environments from the cache).
- **Cold-cache timeout** (TASK-81 item 17): the grader's caps are the measured worst case of the
  reference trials through the runner plus 50% (`pipeline_trial.py caps`): `--grader-timeout` from
  the whole grading run, `--build-timeout` from the slowest build, `--stream-grace` from the most a
  stream run took past its DURATION. A candidate slower than the reference by more than that is cut off.
- **The agent's guard cap** (criteria-v2 §5.3, not a TASK-81 item): 7,200 s for the one-shot trials,
  chosen for these first trials.
- The other TASK-81 questions (the oracle map shape, the readings the key accepts, the traps that do not
  reproduce, the plaintext answers in the key, the P2 and P3 open points below, the §8.5 tier rule) are
  out of scope for the runner and stay open.

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
| A4 | By design | The engine writes a micro-batch's files, then replaces the checkpoint by an atomic rename, and on start deletes files above the checkpoint. `test_the_p2_stream_commit_drops_a_batch_that_never_committed` simulates the crash; `test_the_p2_stream_resumes_after_a_crash_between_data_and_checkpoint` crashes `run_stream` itself between the two and restarts it; F6 (two `make stream` runs) exercises the resume |
| A5 | Not graded yet | The generality check is not in `pipetask/trial.py` (open point 1 below). `test_the_p2_engine_runs_a_pipeline_it_has_never_seen` (batch) and `test_the_p2_engine_runs_a_stream_pipeline_it_has_never_seen` (stream, a static CSV joined to each micro-batch) run it against the reference |

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
7. **The stream's batch number restarts when the lake is reset.** P2's `load_id` is the engine's
   micro-batch number (`_batch`), not a load id that grows over time as dlt's does in P1. Deleting
   `lake/` (or only `lake/_checkpoints/`) while keeping `out/warehouse.duckdb` would make
   `mart_edit_windows` skip new windows, since its incremental filter is `load_id > max(last_load_id)`.
   The reference's `make stream` therefore runs dbt with `--full-refresh` whenever no checkpoint exists
   before the run. The grader resets both folders together, so a trial never meets this.

## P3 stack traps on the pinned versions

Checked with Spark 3.5.9 (pyspark 3.5.9, the same Spark as `build.sbt`) on the frozen data:

| Trap | Reproduced | Evidence |
|---|---|---|
| K1 | Yes | `inferSchema` reads the Census `STATE` and `COUNTY` as `int`, so `STATE || COUNTY` gives `11` for `01001`. (The USAspending county code stays a string.) The reference infers no CSV type |
| K2 | By design | The SSE reader commits frames and its position in one atomic rename to a spool, and Structured Streaming lands the spool with its own checkpoint; F6 (two `make stream` runs) exercises the resume, and `StreamSpec` re-lands a batch |
| K3 | Yes | A 5-minute window aggregation with a 10-minute watermark, run three times on one checkpoint, silently drops a row that arrives after the watermark passed its window (2 counted of 3). The reference builds the windows in dbt and routes late events to `late_events` |
| K4 | No | Spark types the decimal quotient as `decimal(38,22)`: no null and no lost cents; a `double` quotient gives the same top ten to the cent (as for A2 and B8). The grader cannot name it; it stays a design-review point |
| K5 | Semantics only | A full outer join on a key with a null on both sides keeps the two null rows apart (3 rows, 1 matched). Whether check 4 fails depends on the arm's model; the reference never joins on a null key |
| K6 | Yes | A second `write.parquet` with the default `SaveMode` fails with `PATH_ALREADY_EXISTS`; `append` doubles the rows. The reference overwrites every lake table and publishes with `insert overwrite directory` |

Other facts of the pinned stack the reference met (not traps, as they fail loudly): the Hive metastore
rejects a `timestamp_ntz` partition column; `x not in (select ...)` plans a nested-loop join (minutes
instead of seconds on the event fact); pip builds pyspark 3.5.9 from a 318 MB source archive, so the
first build depends on a warm pip cache for its time.

## Open points of increment 3 (for the owner)

Gaps in the P3 page that the reference had to fill; the shared spec and the prompts are unchanged.

1. **"The same local Spark".** dbt-spark's `session` method runs pyspark's Spark, which is built for
   Scala 2.12; the Scala 2.13 ingestion runs Spark's 2.13 build in its own JVM. The reference pins the
   same Spark version on both sides (3.5.9) and they share only the lake. Whether one JVM was meant is
   not said; it is not practical with dbt-spark.
2. **No skeleton section**, as for P2. The P3 skeleton has `build.sbt` (Scala 2.13.18, Spark 3.5.9,
   ScalaTest 3.2.20, and the JDK 17 module options Spark needs in a forked JVM), `project/build.properties`
   (sbt 1.12.15), `requirements.txt` (the full closure, hashed), a dbt-spark `session` profile with its
   warehouse and Derby metastore under `out/`, and the failing `Makefile`. The page names neither the
   JDK, the sbt version nor how the dbt environment is installed (the reference: a `.venv` from
   `requirements.txt`). Scala 2.13.8, Spark's own, cannot be used: ScalaTest 3.2.20 brings a newer
   `scala-library` and sbt refuses an older compiler.
3. **Where the toolchain comes from.** The trial image must hold JDK 17, sbt and Python 3.12 with
   `venv` (`P3/image/Dockerfile` is that layer). The first build downloads Spark and the Scala
   compiler (coursier) and pyspark (pip), so a trial needs network access or a pre-warmed cache in the
   image. Which one, and whether a warm cache counts against the agent's loop cost, is an owner
   decision.
4. **K4 does not reproduce** on the frozen data (table above). The page says such a trap is removed.
5. **K5 assumes an outer join** that the shared architecture leaves to dbt, where it applies to any
   stack; as A3 for P2.
6. **The grader read timestamps with a time zone through pytz**, which it does not install, so a mart
   with Spark's `TIMESTAMP` written as an instant (Parquet `isAdjustedToUTC`, DuckDB `TIMESTAMPTZ`)
   failed check 6 with an import error. `pipetask/oracle.py` now reads such columns as UTC timestamps
   (`test_window_starts_with_a_time_zone_are_read_as_utc`). The reference writes `timestamp_ntz`.
7. **The batch number restarts with the checkpoint**, as for P2 (point 7 above): `make stream` in the
   P3 reference rebuilds the stream models in full when `lake/_checkpoints/recentchange/query/` is
   missing before the run.
8. **Time caps.** The stream runs are well inside the grader's `DURATION + 300` s on the laptop (129 s
   and 210 s), but a cold cache adds minutes to the first build; `--grader-timeout 900` may be short
   for P3 on a cold runner.
