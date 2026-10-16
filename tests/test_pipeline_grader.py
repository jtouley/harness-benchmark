"""The pipeline grader against candidates built from the committed answer key.

A candidate here is a set of published marts (Parquet under out/marts/) and an oracle_map.yml. Built
from the key's own answers it must pass; built from a single trap's wrong answer it must fail and name
that trap. The key itself is tested in test_pipeline_key.py.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest
import yaml

from pipetask import grade, oracle

KEY_PATH = Path(__file__).resolve().parents[1] / "golden" / "pipeline" / "key" / "answer_key.json"

SQL_MAP = {
    "checks": {
        1: {"sql": "select agency_name, net from agency_totals"},
        2: {"sql": "select county_fips, per_person from county_per_person"},
        3: {"sql": "select n from negative_awards"},
        4: {"table": "monthly", "columns": ["month_start", "state_fips", "county_fips", "net"]},
        5: {"sql": "select wiki, is_bot, edits, net_bytes from wiki_edits"},
        6: {"sql": "select window_start, edits from windows where wiki = 'enwiki'"},
        7: {"sql": "select count(*) from late_events"},
    }
}


@pytest.fixture(scope="module")
def key():
    return json.loads(KEY_PATH.read_text(encoding="utf-8"))


def answers(key) -> dict:
    return {**{n: c["answer"] for n, c in key["batch"]["checks"].items()},
            **{n: c["answer"] for n, c in key["stream"]["checks"].items()}}


def write_mart(repo: Path, name: str, columns: str, rows: list[tuple]) -> None:
    folder = repo / "out" / "marts" / name
    folder.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"create table t ({columns})")
    if rows:
        marks = ", ".join("?" * len(rows[0]))
        con.executemany(f"insert into t values ({marks})", rows)
    path = (folder / "data.parquet").as_posix().replace("'", "''")
    con.execute(f"copy t to '{path}' (format parquet)")


def write_candidate(repo: Path, key: dict, ans: dict, oracle_map=SQL_MAP, agency_by_name=True,
                    fips_as_int=False) -> Path:
    names = key["batch"]["agencies"]
    write_mart(repo, "agency_totals", "agency_name varchar, net decimal(18,2)",
               [(names[c] if agency_by_name else c, Decimal(v)) for c, v in ans["1"].items()])
    fips_type = "integer" if fips_as_int else "varchar"
    write_mart(repo, "county_per_person", f"county_fips {fips_type}, per_person decimal(18,6)",
               [(int(f) if fips_as_int else f, Decimal(v)) for f, v in ans["2"]])
    write_mart(repo, "negative_awards", "n bigint", [(ans["3"],)])
    month = datetime.strptime(ans["4"]["month"], "%Y-%m").date()
    rows = [(month, f[:2], f, Decimal(v)) for f, v in ans["4"]["counties"].items()]
    for state, total in ans["4"]["states"].items():
        rest = Decimal(total) - sum(Decimal(v) for f, v in ans["4"]["counties"].items() if f[:2] == state)
        rows.append((month, None if state == "unknown" else state, None, rest))
    write_mart(repo, "monthly", "month_start date, state_fips varchar, county_fips varchar, net decimal(18,2)", rows)
    write_mart(repo, "wiki_edits", "wiki varchar, is_bot boolean, edits bigint, net_bytes bigint",
               [(k.split("|")[0], k.endswith("|bot"), e, b) for k, (e, b) in ans["5"].items()])
    write_mart(repo, "windows", "wiki varchar, window_start timestamp, edits bigint",
               [("enwiki", datetime.fromtimestamp(int(t), timezone.utc).replace(tzinfo=None), n)
                for t, n in ans["6"]["windows"].items()])
    write_mart(repo, "late_events", "event_id varchar", [(f"e{i}",) for i in range(ans["7"])])
    (repo / "oracle_map.yml").write_text(yaml.safe_dump(oracle_map), encoding="utf-8")
    return repo


def test_the_key_answers_pass_every_check(key, tmp_path):
    result = grade.grade(write_candidate(tmp_path, key, answers(key)), key)
    assert result["passed"] == 7, {n: c for n, c in result["checks"].items() if not c["pass"]}
    assert all(c["interpretation"] == "primary" for c in result["checks"].values())


def test_codes_for_agencies_and_integer_county_codes_are_read_too(key, tmp_path):
    result = grade.grade(write_candidate(tmp_path, key, answers(key), agency_by_name=False, fips_as_int=True), key)
    assert result["checks"]["1"]["pass"] and result["checks"]["2"]["pass"]


def test_window_starts_with_a_time_zone_are_read_as_utc(key, tmp_path):
    repo = write_candidate(tmp_path, key, answers(key))
    windows = repo / "out" / "marts" / "windows" / "data.parquet"
    con = duckdb.connect()
    con.execute("set TimeZone = 'America/New_York'")  # the instant, not the writer's zone, must count
    con.execute(f"copy (select wiki, timezone('UTC', window_start) as window_start, edits "
                f"from read_parquet('{windows.as_posix()}')) to '{windows.as_posix()}.tz' (format parquet)")
    assert con.execute(f"select typeof(window_start) from read_parquet('{windows.as_posix()}.tz')").fetchone() == (
        "TIMESTAMP WITH TIME ZONE",)
    windows.unlink()
    windows.with_suffix(".parquet.tz").rename(windows)
    result = grade.grade(repo, key)
    assert result["checks"]["6"]["pass"], result["checks"]["6"]


@pytest.mark.parametrize("oracle_map", [
    # a list in check order, plain strings
    [SQL_MAP["checks"][n]["sql"] if "sql" in SQL_MAP["checks"][n] else "monthly" for n in range(1, 8)],
    # descriptive keys, a table and a column hint, an out/marts path
    {f"check_{n}_answer": v for n, v in SQL_MAP["checks"].items()} | {"check_4_answer": {"model": "out/marts/monthly", "column": "net"}},
    # `checks:` beside other top-level keys (an index of the marts), as a list with ids (P1-opus-1)
    {"marts": {"monthly": "out/marts/monthly/"},
     "checks": [{"id": n, **v} for n, v in SQL_MAP["checks"].items()]},
])
def test_other_map_shapes_are_read(key, tmp_path, oracle_map):
    result = grade.grade(write_candidate(tmp_path, key, answers(key), oracle_map=oracle_map), key)
    assert result["passed"] == 7, {n: c for n, c in result["checks"].items() if not c["pass"]}


def trap_cases():
    key = json.loads(KEY_PATH.read_text(encoding="utf-8"))
    for section in ("batch", "stream"):
        for n, check in key[section]["checks"].items():
            for trap in check["traps"]:
                yield pytest.param(n, trap, id=f"check{n}-{trap}")


@pytest.mark.parametrize(("check", "trap"), list(trap_cases()))
def test_a_single_trap_answer_fails_its_check_and_is_named(key, tmp_path, check, trap):
    ans = answers(key)
    section = "batch" if check in key["batch"]["checks"] else "stream"
    ans[check] = key[section]["checks"][check]["traps"][trap]
    if check == "4":  # the key stores only the month's totals; keep the grader's reading identical
        assert ans[check]["month"] == key["batch"]["checks"]["4"]["answer"]["month"]
    result = grade.grade(write_candidate(tmp_path, key, ans), key)
    verdict = result["checks"][check]
    assert not verdict["pass"]
    assert trap in verdict["traps"]
    others = {n: c["pass"] for n, c in result["checks"].items() if n != check}
    assert all(others.values()), others


def test_an_answer_no_trap_explains_is_unexplained(key, tmp_path):
    ans = answers(key)
    first = next(iter(ans["1"]))
    ans["1"] = dict(ans["1"], **{first: str(Decimal(ans["1"][first]) + Decimal("0.01"))})
    verdict = grade.grade(write_candidate(tmp_path, key, ans), key)["checks"]["1"]
    assert not verdict["pass"] and verdict["traps"] == [] and verdict["unexplained"]


def test_a_missing_map_fails_every_check_without_crashing(key, tmp_path):
    write_candidate(tmp_path, key, answers(key))
    (tmp_path / "oracle_map.yml").unlink()
    result = grade.grade(tmp_path, key)
    assert result["passed"] == 0
    assert all("missing" in c["error"] for c in result["checks"].values())


def test_a_broken_query_or_unknown_table_fails_only_its_check(key, tmp_path):
    broken = {"checks": {**SQL_MAP["checks"], 1: {"sql": "select nope from agency_totals"},
                         3: {"table": "no_such_mart"}}}
    result = grade.grade(write_candidate(tmp_path, key, answers(key), oracle_map=broken), key)
    assert not result["checks"]["1"]["pass"] and "failed" in result["checks"]["1"]["error"]
    assert not result["checks"]["3"]["pass"] and "no published mart" in result["checks"]["3"]["error"]
    assert result["passed"] == 5


@pytest.mark.parametrize(("value", "expected"), [
    ("01001", "01001"), (1001, "01001"), ("9001", "09001"), ("09-unknown", None), ("09999", None), (None, None),
])
def test_county_codes_normalize(value, expected):
    assert grade.county_fips(value) == expected


@pytest.mark.parametrize(("value", "expected"), [
    ("2024-07", "2024-07"), ("2024-07-01", "2024-07"), (202407, "2024-07"), (Decimal("204004.17"), None),
    (datetime(2024, 7, 1), "2024-07"), (12345, None),
])
def test_months_normalize(value, expected):
    assert grade.year_month(value) == expected


@pytest.mark.parametrize(("value", "expected"), [
    ("CT", "09"), ("9", "09"), ("Connecticut", "09"), ("09", "09"), ("XX", None), (None, None),
])
def test_states_normalize(value, expected):
    assert grade.state_fips(value) == expected


# ------------------------------------------------------------------- the map's SQL sees only out/marts/


def _reads_the_key(glob: str) -> dict:
    src = f"read_json_objects('{glob}')"
    return {"checks": {
        3: {"sql": f"select cast(json_extract_string(json, '$.batch.checks.3.answer') as bigint) as n from {src}"},
        7: {"sql": f"select cast(json_extract_string(json, '$.stream.checks.7.answer') as bigint) as n from {src}"},
    }}


@pytest.mark.parametrize("where", ["outside the repo", "inside the repo"])
def test_the_map_sql_cannot_read_a_file_outside_out_marts(key, tmp_path, where):
    repo = tmp_path / "repo"
    (repo / "out" / "marts").mkdir(parents=True)
    keydir = tmp_path / "tmpkey" if where == "outside the repo" else repo / "notes"
    keydir.mkdir()
    (keydir / "answer_key.json").write_text(json.dumps(key))
    (repo / "oracle_map.yml").write_text(yaml.safe_dump(_reads_the_key(f"{keydir.parent.as_posix()}/*/answer_key.json")))
    result = grade.grade(repo, key)
    assert not result["checks"]["3"]["pass"] and not result["checks"]["7"]["pass"]


def test_the_map_sql_cannot_turn_file_access_back_on(key, tmp_path):
    con = oracle.connect(write_candidate(tmp_path, key, answers(key)))
    assert con.sql('select count(*) from "agency_totals"').fetchone()[0] == 4
    for setting in ("enable_external_access = true", "allowed_directories = ['/']", "lock_configuration = false"):
        with pytest.raises(duckdb.Error):
            con.execute(f"set {setting}")


@pytest.mark.parametrize("link", ["out/marts/key.json", "out/marts"])
def test_a_symlink_under_out_marts_fails_every_check(key, tmp_path, link):
    repo = write_candidate(tmp_path / "repo", key, answers(key))
    (tmp_path / "answer_key.json").write_text(json.dumps(key))
    if link == "out/marts":
        (repo / "out" / "marts").rename(tmp_path / "elsewhere")
        (repo / "out" / "marts").symlink_to(tmp_path / "elsewhere")
    else:
        (repo / link).symlink_to(tmp_path / "answer_key.json")
    result = grade.grade(repo, key)
    assert result["passed"] == 0 and "symbolic link" in result["checks"]["1"]["error"]


@pytest.mark.parametrize("name", ["it's", 'say "hi"', "x'); select 1; --"])
def test_a_mart_folder_name_is_a_name_not_sql(tmp_path, name):
    repo = tmp_path / "repo"
    write_mart(repo, name, "n bigint", [(42,)])
    con = oracle.connect(repo)
    quoted = name.replace('"', '""')
    assert con.sql(f'select n from "{quoted}"').fetchall() == [(42,)]


def test_numbered_entries_at_the_top_level_win_over_a_stray_checks_key(key, tmp_path):
    """`checks:` is unwrapped only when the top level has no numbered entries (PR #31 review)."""
    oracle_map = {f"check_{n}": v for n, v in SQL_MAP["checks"].items()} | {"checks": ["all seven, above"]}
    result = grade.grade(write_candidate(tmp_path, key, answers(key), oracle_map=oracle_map), key)
    assert result["passed"] == 7, {n: c for n, c in result["checks"].items() if not c["pass"]}


@pytest.mark.parametrize("extra", [{"v2": True}, {"schema_v3": "x"}, {"version": 2}])
def test_a_key_with_a_digit_that_is_not_a_check_does_not_stop_the_checks_unwrap(key, tmp_path, extra):
    oracle_map = extra | {"checks": [{"id": n, **v} for n, v in SQL_MAP["checks"].items()]}
    result = grade.grade(write_candidate(tmp_path, key, answers(key), oracle_map=oracle_map), key)
    assert result["passed"] == 7, {n: c for n, c in result["checks"].items() if not c["pass"]}
