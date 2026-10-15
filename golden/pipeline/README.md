# Pipeline task family: builder files (hidden from arms)

Inputs, replay server, answer key, grader and reference solutions for the
[pipeline family](../../docs/tasks/pipeline-family.md) (P1, P2, P3; issue #11). Increment 1 builds
the shared inputs, the key, the grader and the P1 reference. P2 and P3 have no skeleton or reference
yet.

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
| `pipetask/oracle.py`, `pipetask/grade.py`, `pipetask/trial.py` | Grader: reads `oracle_map.yml`, runs `make build` twice and `make stream` twice against the replay, checks the seven answers | No (inside `grader.pyz`) |
| `pipetask/prompt.py`, `P1/prompt.md` | The P1 prompt, word for word from the specs | Passed as the prompt |
| `P1/skeleton/` | `Makefile` (both targets fail), `pyproject.toml` and `uv.lock` (pinned dlt, dbt-core, dbt-duckdb, duckdb), empty dbt project with `profiles.yml` | Copied into the repo |
| `P1/reference/` | The P1 reference solution (dlt, DuckDB, dbt-duckdb, Parquet lake), an overlay on the skeleton | **Never** |
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
# the reference, end to end
python3 -m pipetask.assemble P1 --out /tmp/p1-ref --with-reference
uv run --project ../.. python -m pipetask.trial --repo /tmp/p1-ref \
    --key key/answer_key.json --capture data/capture/recentchange.jsonl.gz
# regenerate the key after any change to data/ or the schedule (tests fail until you do)
uv run --project ../.. python -m pipetask.key --raw data/raw \
    --capture data/capture/recentchange.jsonl.gz --seed 1 --out key/answer_key.json
uv run --project ../.. python -m pipetask.manifest
```

The full reference trial is also a test: `HB_PIPELINE_REFERENCE=1 uv run --frozen --python 3.12 python -m pytest tests/test_pipeline_reference.py`.

## A trial on the isolated runner

The runner (`runner/`, PR #23) is not on `main` yet, so it is not wired. A trial will be:

```sh
python3 -m pipetask.assemble P1 --out /tmp/p1-repo
python3 -m pipetask.bundle --out /tmp/p1-dist          # replay.pyz, grader.pyz
runner/run_trial.sh --repo /tmp/p1-repo --prompt golden/pipeline/P1/prompt.md \
    --grader /tmp/p1-dist/grader.pyz --model <model> [--plugin-dir <arm>] --out results/runs/<trial>
```

Two runner changes are needed for this family (left for the wiring step):

1. **The dev replay server.** Before the agent starts, the entrypoint copies `replay.pyz` to a
   root-only path (mode 0700) and starts `python3 replay.pyz --seed <dev seed>` as root on port 8099,
   so the arm can develop against `http://localhost:8099/v2/stream/recentchange`. The grading seed
   (in the key) must differ from the dev seed. After the agent phase, the entrypoint stops it, so the
   grader can serve the grading seed on the same port.
2. **Time caps.** The grader runs `make build` twice and `make stream` twice (30 s and 90 s by default),
   plus a dependency install: allow at least 15 minutes (`--grader-timeout 900` is the current default).
   The agent cap for this task is an owner decision (the family is meant to exceed one session).

## What the key fixes that the spec leaves open

The grader accepts more than one reading where the spec is ambiguous (each check's `accepted` in the
key); the reference uses the first.

| Point | Primary (reference) | Also accepted |
|---|---|---|
| Event time of an edit | `timestamp` | `meta.dt` |
| "Arrives more than 10 minutes after its window ended", in a replay at 60x | Against the stream's event-time watermark at arrival | — (a wall-clock reading cannot work at replay speed) |
| Check 5 counts late edits? | Yes (all edits consumed) | Excluding late edits |
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
| 5 | W1, W2, W4, W5, F2, F5 | — |
| 6 | S3, F4, F5, W2 | W3 (local time): the grading container runs in UTC, so local time is UTC. F2: the re-sent frames do not move an en.wikipedia top window |
| 7 | S3, F4, F2, F5 | — |

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
