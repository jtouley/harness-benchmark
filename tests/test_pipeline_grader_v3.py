"""Grader v3 (docs/method/grading.md#grader-v3): golden samples from the stored run trees, and the grammar.

Each fixture under golden/pipeline/fixtures/grader-v3/<run_id>/ is one stored tree's delivered oracle_map.yml
and the published marts it names, byte for byte as the pinned grader's trial left them
(docs/evidence/2026-10-25-grader-v3/). expected.json holds the pinned grader's result per check and grader
v3's. Every entry of every fixture is a parser case: its resolution (the stated operation read, or the
reason it is unresolved) is pinned here, so a grammar change that moves any of them shows up.
"""

from __future__ import annotations

import json
import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest
import yaml

from pipetask import grade, ops, oracle

ROOT = Path(__file__).resolve().parents[1]
KEY = json.loads((ROOT / "golden" / "pipeline" / "key" / "answer_key.json").read_text(encoding="utf-8"))
FIXTURES = sorted(p for p in (ROOT / "golden" / "pipeline" / "fixtures" / "grader-v3").iterdir() if p.is_dir())


def _grade_from(repo: Path) -> dict:
    """Grade from the repository root, as the trial runs it (an oracle_map path is relative to it)."""
    here = os.getcwd()
    os.chdir(repo)
    try:
        return grade.grade(Path("."), KEY)
    finally:
        os.chdir(here)


def test_there_is_a_golden_sample_for_every_stored_tree_with_a_map():
    names = {fx.name for fx in FIXTURES}
    assert "20261024-P1-cadence-haiku-core-6" in names and "20261023-P1-oneshot-sonnet-1-r2" in names
    assert len(names) == 13


@pytest.mark.parametrize("fx", FIXTURES, ids=lambda p: p.name)
def test_golden_sample_grades_as_recorded(fx):
    expected = json.loads((fx / "expected.json").read_text(encoding="utf-8"))
    got = _grade_from(fx)
    for n, want in expected["v3"]["checks"].items():
        check = got["checks"][n]
        assert bool(check["pass"]) == want["pass"], (n, check)
        assert (check.get("source") or check.get("error")) == want["resolution"], n
    assert got["passed"] == expected["v3"]["passed"]


@pytest.mark.parametrize("fx", FIXTURES, ids=lambda p: p.name)
def test_v3_keeps_every_check_the_pinned_grader_passed(fx):
    expected = json.loads((fx / "expected.json").read_text(encoding="utf-8"))
    for n, passed in expected["pinned"]["checks"].items():
        if passed:
            assert expected["v3"]["checks"][n]["pass"], n


def test_core6_reads_its_stated_operations_to_seven():
    expected = json.loads((ROOT / "golden/pipeline/fixtures/grader-v3/20261024-P1-cadence-haiku-core-6"
                           / "expected.json").read_text())
    assert expected["pinned"]["passed"] == 4 and expected["v3"]["passed"] == 7
    assert "stated operation: filter net_obligations < 0; count(*)" in expected["v3"]["checks"]["3"]["resolution"]


# ------------------------------------------------------------------------------------- the grammar


COLUMNS = ["agency_code", "county_fips", "net_obligations", "population", "is_net_negative", "wiki",
           "actor_type", "net_bytes", "window_start", "edit_count", "domain", "award_key", "month_start"]


def plan(text: str, key: str = "how", named=()) -> ops.Plan:
    return ops.parse({key: text}, COLUMNS, ["other_mart"], list(named))


@pytest.mark.parametrize("text, described", [
    ("sum net_obligations by agency_code over all months", "sum(net_obligations); by agency_code"),
    ("Sum net_obligations by agency_code.", "sum(net_obligations); by agency_code"),
    ("sum(net_obligations) grouped by agency_code, over all months and places", "sum(net_obligations); by agency_code"),
    ("count rows where net_obligations < 0", "filter net_obligations < 0; count(*)"),
    ("Count the rows with net_obligations below zero.", "filter net_obligations < 0; count(*)"),
    ("Count the rows where is_net_negative is true.", "filter is_net_negative = true; count(*)"),
    ("count rows where is_net_negative", "filter is_net_negative = true; count(*)"),
    ("count(*)", "count(*)"),
    ("sum net_obligations per county_fips, divide by population (July 1, 2024 basis)",
     "sum(net_obligations); by county_fips; divided by population"),
    ("filter domain = en.wikipedia.org, sum edit_count by window_start, order by the sum descending, "
     "take the first ten rows", "filter domain = 'en.wikipedia.org'; sum(edit_count); by window_start"),
    ("Filter wiki to enwiki. Sum edit_count by window_start and sort by the sum, descending.",
     "filter wiki = 'enwiki'; sum(edit_count); by window_start"),
    ("count(*) and sum(net_bytes) grouped by wiki and actor_type, where window_start is in the replayed hour",
     "count(*), sum(net_bytes); by wiki, actor_type"),
    ("read the rows directly; each wiki has one row per actor type", "rows as published"),
])
def test_the_grammar_reads(text, described):
    assert plan(text).describe() == described


def test_a_filter_key_is_a_condition():
    p = ops.parse({"rows": "wiki = 'enwiki'"}, COLUMNS, [], [])
    assert p.describe() == "filter wiki = 'enwiki'"


def test_sum_per_group_then_count_the_groups_below_zero():
    p = ops.parse({"aggregation": "sum per award_key, then count the awards whose sum is below zero"},
                  COLUMNS, [], ["net_obligations"])
    assert p.group == ["award_key"] and p.count_groups_below_zero


@pytest.mark.parametrize("text", [
    "wiki = dim_wiki.dbname where dim_wiki.site_host = 'en.wikipedia.org'",  # a join
    "Also read other_mart and net_obligations",                               # another mart
    "average net_obligations by agency_code",                                  # not in the grammar
    "Sum edit_count per window",                                               # `window` is not a column
])
def test_what_the_grammar_cannot_read_is_unresolved(text):
    with pytest.raises(ops.Unresolved):
        plan(text)


def test_commentary_without_columns_or_operation_words_is_skipped():
    assert plan("September 2024. Counts every consumed edit, on time or late.").empty()


# ------------------------------------------------------------------- applied to a candidate's marts


def write_mart(repo: Path, name: str, columns: str, rows: list[tuple]) -> None:
    folder = repo / "out" / "marts" / name
    folder.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"create table t ({columns})")
    con.executemany(f"insert into t values ({', '.join('?' * len(rows[0]))})", rows)
    con.execute(f"copy t to '{(folder / 'data.parquet').as_posix()}' (format parquet)")


def check(repo: Path, n: str, entry: dict) -> dict:
    (repo / "oracle_map.yml").write_text(yaml.safe_dump({"checks": [{"check": int(n), **entry}]}), encoding="utf-8")
    return _grade_from(repo)["checks"][n]


def award_rows(answer: int, extra_positive: int = 5) -> list[tuple]:
    return [(f"a{i}", Decimal("-1.00")) for i in range(answer)] + \
           [(f"p{i}", Decimal("2.00")) for i in range(extra_positive)]


def test_a_stated_count_answers_check_3(tmp_path):
    write_mart(tmp_path, "awards", "award_key varchar, net_obligations decimal(18,2)", award_rows(KEY["batch"]["checks"]["3"]["answer"]))
    entry = {"table": "awards", "columns": ["award_key", "net_obligations"], "how": "count rows where net_obligations < 0"}
    assert check(tmp_path, "3", entry)["pass"]
    # the same mart without the stated filter: the row count, which is not the answer
    assert not check(tmp_path, "3", {"table": "awards", "columns": ["award_key", "net_obligations"]})["pass"]


def test_the_answer_check_is_as_strict_as_before(tmp_path):
    n = KEY["batch"]["checks"]["3"]["answer"]
    write_mart(tmp_path, "awards", "award_key varchar, net_obligations decimal(18,2)", award_rows(n - 1))
    entry = {"table": "awards", "columns": ["award_key", "net_obligations"], "how": "count rows where net_obligations < 0"}
    got = check(tmp_path, "3", entry)
    assert not got["pass"] and got["got"] == str(n - 1)


def test_an_unresolved_entry_fails_with_its_reason_and_no_fallback(tmp_path):
    write_mart(tmp_path, "awards", "award_key varchar, net_obligations decimal(18,2)", award_rows(KEY["batch"]["checks"]["3"]["answer"]))
    got = check(tmp_path, "3", {"table": "awards", "columns": ["net_obligations"],
                                "how": "count the distinct award_key having net_obligations below the median"})
    assert not got["pass"] and got["error"].startswith("unresolved:")


def test_divide_is_exact_and_needs_one_divisor_per_group(tmp_path):
    top = KEY["batch"]["checks"]["2"]["answer"]
    rows = []
    for fips, per_person in top:
        pop = 1000
        total = Decimal(per_person) * pop  # two months adding up to it
        rows += [(date(2024, 1, 1), fips, total - 1, pop), (date(2024, 2, 1), fips, Decimal(1), pop)]
    write_mart(tmp_path, "monthly", "month_start date, county_fips varchar, net_obligations decimal(18,2), population bigint", rows)
    entry = {"table": "monthly", "columns": ["county_fips", "net_obligations", "population"],
             "how": "sum net_obligations by county_fips, divide by population, order by the result, take ten"}
    assert check(tmp_path, "2", entry)["pass"]
    rows[1] = (rows[1][0], rows[1][1], rows[1][2], 999)
    write_mart(tmp_path, "monthly", "month_start date, county_fips varchar, net_obligations decimal(18,2), population bigint", rows)
    got = check(tmp_path, "2", entry)
    assert not got["pass"] and "more than one value" in got["error"]


def test_a_mart_file_path_resolves_to_its_mart(tmp_path):
    write_mart(tmp_path, "awards", "n bigint", [(KEY["batch"]["checks"]["3"]["answer"],)])
    assert check(tmp_path, "3", {"table": "out/marts/awards/data.parquet", "column": "n"})["pass"]


def test_a_nested_answer_query_is_read(tmp_path):
    write_mart(tmp_path, "awards", "award_key varchar, net_obligations decimal(18,2)", award_rows(KEY["batch"]["checks"]["3"]["answer"]))
    entry = {"table": "awards", "queries": {"answer": "select count(*) from awards where net_obligations < 0"}}
    assert check(tmp_path, "3", entry)["pass"]
    entry = {"table": "awards", "queries": {"a": "select 1", "b": "select 2"}}
    assert check(tmp_path, "3", entry)["error"].startswith("unresolved:")


def test_p4_reads_maps_as_before():
    con = duckdb.connect()
    con.execute("create view awards as select 1 as n")
    res = oracle.resolve({"table": "awards", "how": "count rows where n < 0"}, con)
    assert res.rows == [(1,)]  # the P4 grader does not apply stated operations
