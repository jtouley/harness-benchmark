"""The P4 reference: raw CSV files -> Parquet lake -> DuckDB models -> published marts under out/marts/.

    uv run --frozen python -m pipeline.build

Every step replaces its outputs, so a second run gives the same files. All work is DuckDB SQL; money is
DECIMAL(18,2); codes are text.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW, LAKE, MARTS = ROOT / "data" / "raw", ROOT / "lake", ROOT / "out" / "marts"
LOAN_DAYS = 21
SOURCES = {"branches": ["branches.csv"], "items": ["items.csv"], "patrons": ["patrons.csv"],
           "fines": ["fines.csv"], "loan_events": ["loans_2025_h1.csv", "loans_2025_h2.csv"]}

MODELS = {
    # staging: typed, deduplicated views of the lake
    "stg_branches": "select branch_code, branch_name, region from lake_branches",
    "stg_items": """
        select item_id, title, category, home_branch,
               cast(replace(replace(replacement_cost, '$', ''), ',', '') as decimal(18,2)) as replacement_cost
        from lake_items""",
    "stg_patrons": "select patron_id, home_branch, cast(joined_year as integer) as joined_year from lake_patrons",
    "stg_fines": """
        select fine_id, loan_id, branch_code, strptime(assessed_time, '%Y-%m-%dT%H:%M:%SZ') as assessed_at,
               cast(amount as decimal(18,2)) as amount
        from lake_fines""",
    "stg_loan_events": """
        select distinct loan_id, event, strptime(event_time, '%Y-%m-%dT%H:%M:%SZ') as event_at,
               branch_code, item_id, patron_id
        from lake_loan_events""",
    # core: one row per loan, with its checkout, its return and its due time
    "fct_loans": f"""
        with checkouts as (
            select loan_id, event_at as checkout_at, branch_code, item_id, patron_id
            from stg_loan_events where event = 'checkout'),
        returns as (
            select loan_id, min(event_at) as returned_at from stg_loan_events where event = 'return' group by loan_id),
        renewals as (
            select e.loan_id, count(*) as renewals
            from stg_loan_events e join returns r using (loan_id)
            where e.event = 'renew' and e.event_at < r.returned_at group by e.loan_id)
        select c.loan_id, c.branch_code, c.item_id, c.patron_id, c.checkout_at, r.returned_at,
               coalesce(n.renewals, 0) as renewals,
               c.checkout_at + to_days({LOAN_DAYS} * (1 + coalesce(n.renewals, 0))) as due_at,
               r.returned_at is not null and r.returned_at > c.checkout_at + to_days({LOAN_DAYS} * (1 + coalesce(n.renewals, 0))) as returned_late
        from checkouts c left join returns r using (loan_id) left join renewals n using (loan_id)""",
    # marts
    "mart_branch_checkouts": """
        select l.branch_code, b.branch_name, count(*) as checkouts
        from fct_loans l join stg_branches b using (branch_code) group by 1, 2 order by 1""",
    "mart_item_checkouts": """
        select l.item_id, i.title, count(*) as checkouts
        from fct_loans l join stg_items i using (item_id) group by 1, 2 order by checkouts desc, item_id""",
    "mart_late_returns": "select loan_id, branch_code, checkout_at, due_at, returned_at from fct_loans where returned_late",
    "mart_monthly_fines": """
        select date_trunc('month', assessed_at)::date as month_start, branch_code,
               sum(amount) as net_fines, sum(case when amount > 0 then amount else 0 end) as assessed,
               sum(case when amount < 0 then -amount else 0 end) as waived
        from stg_fines group by 1, 2 order by 1, 2""",
    "mart_active_patrons": """
        select p.home_branch as branch_code, count(distinct l.patron_id) as active_patrons
        from fct_loans l join stg_patrons p using (patron_id) group by 1 order by 1""",
    "mart_items_on_loan": """
        with last_event as (
            select item_id, arg_max(event, (event_at, event)) as last_event
            from stg_loan_events group by item_id)
        select i.item_id, i.title, i.replacement_cost
        from last_event e join stg_items i using (item_id)
        where e.last_event in ('checkout', 'renew') order by i.item_id""",
}
PUBLISHED = ("mart_branch_checkouts", "mart_item_checkouts", "mart_late_returns", "mart_monthly_fines",
             "mart_active_patrons", "mart_items_on_loan")


def land(con: duckdb.DuckDBPyConnection) -> None:
    """Every raw file into the lake as Parquet, every column as text plus the load metadata."""
    if LAKE.exists():
        shutil.rmtree(LAKE)
    for table, files in SOURCES.items():
        folder = LAKE / table
        folder.mkdir(parents=True)
        for name in files:
            src = (RAW / name).as_posix().replace("'", "''")
            dest = (folder / f"{Path(name).stem}.parquet").as_posix().replace("'", "''")
            con.execute(f"copy (select *, '{name}' as _source_file from read_csv('{src}', all_varchar=true, "
                        f"header=true)) to '{dest}' (format parquet)")
        glob = (folder / "*.parquet").as_posix().replace("'", "''")
        con.execute(f"create or replace view lake_{table} as select * from read_parquet('{glob}')")


def model(con: duckdb.DuckDBPyConnection) -> None:
    for name, sql in MODELS.items():
        con.execute(f"create or replace table {name} as {sql}")


def publish(con: duckdb.DuckDBPyConnection) -> None:
    """One folder per mart under out/marts/, written whole and then moved into place."""
    fresh = MARTS.parent / "marts.next"
    for folder in (MARTS, fresh):
        if folder.exists():
            shutil.rmtree(folder)
    for name in PUBLISHED:
        (fresh / name).mkdir(parents=True)
        dest = (fresh / name / "data.parquet").as_posix().replace("'", "''")
        con.execute(f"copy (select * from {name}) to '{dest}' (format parquet)")
    fresh.rename(MARTS)


def main() -> None:
    con = duckdb.connect()
    con.execute("set TimeZone = 'UTC'")
    land(con)
    model(con)
    publish(con)
    print(f"published {len(PUBLISHED)} marts under {MARTS}")


if __name__ == "__main__":
    main()
