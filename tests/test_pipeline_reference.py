"""The references pass the grader end to end (the proof that each task is solvable and the key right).

Slow (a few minutes per task: a virtual environment, two builds, two stream runs against the replay
server), so it runs only with HB_PIPELINE_REFERENCE=1. P1 and P2 need make and uv on the PATH. P3 runs
entirely in its pinned toolchain container (golden/pipeline/P3/image/), so it needs only docker.

P2 adds two checks of its engine (docs/tasks/P2-config-arrow-polars-datafusion.md): a pipeline file it
has never seen runs with no code change (the generality check), and a broken file is reported with its
file and line before anything runs.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import duckdb
import pytest

from pipetask import assemble, trial

PIPELINE = Path(__file__).resolve().parents[1] / "golden" / "pipeline"

pytestmark = pytest.mark.skipif(os.environ.get("HB_PIPELINE_REFERENCE") != "1",
                                reason="set HB_PIPELINE_REFERENCE=1 to run the reference trials")


@pytest.mark.parametrize("task", ["P1", "P2"])
def test_the_reference_passes_every_check_and_rebuilds_identically(task, tmp_path):
    key = json.loads((PIPELINE / "key" / "answer_key.json").read_text(encoding="utf-8"))
    repo = assemble.assemble(task, tmp_path / "repo", with_reference=True)
    result = trial.trial(repo, key, PIPELINE / "data" / "capture" / "recentchange.jsonl.gz",
                         seed=key["stream"]["seed"], port=8099, speed=60.0, durations=(30, 90),
                         build_timeout=1800, logs=tmp_path / "logs")
    failed = {n: c for n, c in result["checks"].items() if not c["pass"]}
    assert result["idempotent"], result["changed_by_second_build"]
    assert failed == {}
    assert result["reward"] == 1.0


# A pipeline the P2 reference never saw: the Census 2024 file under a new name, one Polars transform
# and one DataFusion SQL transform, landed in the lake.
UNSEEN = """\
pipeline: census_copy
sources:
  - name: counties_raw
    type: file
    format: csv
    paths: [data/raw/census/co-est2024-alldata.csv]
    encoding: latin1
transforms:
  - name: counties_typed
    engine: polars
    input: counties_raw
    filter: "SUMLEV = '050'"
    with_columns: {county_fips: "STATE || COUNTY"}
    cast: {POPESTIMATE2024: int64}
  - name: county_population
    engine: datafusion
    inputs: [counties_typed]
    sql: select county_fips, "CTYNAME" as county_name, "POPESTIMATE2024" as population from counties_typed
sinks:
  - {input: county_population, table: county_population_copy, mode: replace}
"""


@pytest.fixture(scope="module")
def p2_repo(tmp_path_factory):
    repo = assemble.assemble("P2", tmp_path_factory.mktemp("p2") / "repo", with_reference=True, git=False)
    subprocess.run(["uv", "sync", "--frozen", "-q"], cwd=repo, check=True)
    return repo


def engine(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["uv", "run", "--frozen", "python", "-m", "engine", *args], cwd=repo,
                          capture_output=True, text=True)


def test_the_p2_engine_runs_a_pipeline_it_has_never_seen(p2_repo):
    (p2_repo / "pipelines" / "census_copy.yml").write_text(UNSEEN, encoding="utf-8")
    done = engine(p2_repo, "run", "pipelines/census_copy.yml")
    assert done.returncode == 0, done.stderr
    con = duckdb.connect()
    landed = con.execute(
        "select count(*), count(distinct county_fips), min(length(county_fips)), sum(population), "
        "any_value(typeof(population)) from read_parquet(?)",
        [str(p2_repo / "lake" / "county_population_copy" / "*.parquet")]).fetchone()
    source = con.execute(
        "select count(*), count(distinct STATE || COUNTY), 5, sum(cast(POPESTIMATE2024 as bigint)), 'BIGINT' "
        "from read_csv(?, all_varchar = true, encoding = 'latin-1') where SUMLEV = '050'",
        [str(p2_repo / "data" / "raw" / "census" / "co-est2024-alldata.csv")]).fetchone()
    assert landed == source


def test_the_p2_engine_reports_file_and_line_before_running(p2_repo):
    wrong_engine = UNSEEN.replace("engine: datafusion", "engine: spark")
    (p2_repo / "pipelines" / "broken.yml").write_text(wrong_engine, encoding="utf-8")
    done = engine(p2_repo, "run", "pipelines/broken.yml")
    line = next(i for i, text in enumerate(wrong_engine.splitlines(), 1) if "engine: spark" in text)
    assert done.returncode == 2
    assert f"pipelines/broken.yml:{line}:" in done.stderr, done.stderr

    dangling = UNSEEN.replace("inputs: [counties_typed]", "inputs: [counties_typd]")
    (p2_repo / "pipelines" / "broken.yml").write_text(dangling, encoding="utf-8")
    done = engine(p2_repo, "validate", "pipelines/broken.yml")
    line = next(i for i, text in enumerate(dangling.splitlines(), 1) if "counties_typd" in text)
    assert done.returncode == 2
    assert f"pipelines/broken.yml:{line}: 'counties_typd' is not defined" in done.stderr, done.stderr


CRASH = """\
from pathlib import Path
import pyarrow as pa
from engine.sinks import StreamCommit
lake = Path('crash_lake')
commit = StreamCommit(lake, 'stream', ['events'])
commit.commit(1, {'events': pa.table({'x': [1, 2]})}, {'last_event_id': 'a', 'next_seq': 2})
# a crash after batch 2's data was written and before its checkpoint replaced batch 1's
(lake / 'events' / '0000000002.parquet').write_bytes((lake / 'events' / '0000000001.parquet').read_bytes())
(lake / 'events' / '0000000003.parquet.tmp').write_bytes(b'partial')
removed = sorted(p.name for p in commit.recover())
print(removed, commit.load(), sorted(p.name for p in (lake / 'events').iterdir()))
"""


def test_the_p2_stream_commit_drops_a_batch_that_never_committed(p2_repo):
    done = subprocess.run(["uv", "run", "--frozen", "python", "-c", CRASH], cwd=p2_repo, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == ("['0000000002.parquet', '0000000003.parquet.tmp'] "
                                   "(1, {'last_event_id': 'a', 'next_seq': 2}) ['0000000001.parquet']")


@pytest.mark.skipif(shutil.which("docker") is None, reason="the P3 trial runs in docker")
def test_the_p3_reference_passes_every_check_in_its_container(tmp_path):
    """Build the toolchain image, run the ScalaTest suites, then the full trial, all in the container."""
    done = subprocess.run([str(PIPELINE / "P3" / "image" / "trial.sh"), str(tmp_path), "--with-reference",
                           "--scalatest"], capture_output=True, text=True, timeout=3600)
    assert done.returncode == 0, done.stderr[-3000:]
    assert "All tests passed." in (tmp_path / "logs" / "scalatest.log").read_text(encoding="utf-8")
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    failed = {n: c for n, c in result["checks"].items() if not c["pass"]}
    assert result["idempotent"], result["changed_by_second_build"]
    assert failed == {}
    assert result["reward"] == 1.0
