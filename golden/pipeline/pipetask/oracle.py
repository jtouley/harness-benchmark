"""Read a candidate's oracle_map.yml and turn each entry into rows from the published marts.

The spec asks for "for each question in the Checks list, the table and column (or SQL view) that
answers it" and fixes no format. So this reader accepts the shapes an engineer would write:

- the seven entries as a mapping keyed by anything that contains the check number (`1`, `check_1`,
  `q1`, `check1_net_obligations`), or as a list in order; optionally under a top-level `checks:` key
  (also beside other top-level keys, such as an index of the marts, when no top-level key is numbered)
  or under a single top-level key;
- each entry as a mapping with a query (`sql`, `query`, `view`, `sql_view`) or a table (`table`,
  `model`, `mart`, `relation`, `path`) plus optional column hints (`column`, `columns`, `measure`...),
  or as a plain string (a SQL statement, a table name, or `table.column`).

Each published mart (a folder under out/marts/) is a DuckDB view named after its folder, so a query can
name marts directly. Only out/marts/ is visible: the spec says anything downstream reads only that.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import yaml

QUERY_KEYS = ("sql", "query", "view", "sql_view", "select")
TABLE_KEYS = ("table", "model", "mart", "relation", "path", "source", "name")
COLUMN_KEYS = ("column", "columns", "measure", "measures", "value", "values", "metric", "metrics", "field", "fields")
CHECKS = tuple(str(n) for n in range(1, 8))
# A top-level key that names a check (`1`, `check_1`, `q1`, `check1_net_obligations`), not just any key
# with a digit (`v2`, `schema_v3`): only such keys stop the unwrap of a `checks:` key beside them.
CHECK_KEY = re.compile(r"^(?:check|q|question)?[_\- ]?0*[1-7](?:\D|$)", re.IGNORECASE)


class MapError(Exception):
    """The map or one entry cannot be read; the check fails with this message."""


@dataclass
class Result:
    columns: list[str]
    types: list[str]
    rows: list[tuple]
    hints: list[str] = field(default_factory=list)  # column names the map named, lower case
    source: str = ""


def load_map(repo: Path) -> dict[str, object]:
    path = repo / "oracle_map.yml"
    if not path.exists():
        alt = repo / "oracle_map.yaml"
        if not alt.exists():
            raise MapError("oracle_map.yml is missing")
        path = alt
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise MapError(f"oracle_map.yml is not valid YAML: {exc}") from exc
    numbered = isinstance(doc, dict) and any(CHECK_KEY.match(str(k)) for k in doc)
    wrapper = next((v for k, v in doc.items() if str(k).lower() == "checks" and isinstance(v, (dict, list))),
                   None) if isinstance(doc, dict) and not numbered else None
    if wrapper is not None:
        doc = wrapper  # {checks: ...}, also beside other keys such as {marts: {...}, checks: [...]}
    elif isinstance(doc, dict) and len(doc) == 1 and isinstance(next(iter(doc.values())), (dict, list)):
        doc = next(iter(doc.values()))  # e.g. {oracle: [...]}
    if isinstance(doc, list):
        out = {}
        for i, item in enumerate(doc, 1):
            num = _number(item.get("check", item.get("id", i))) if isinstance(item, dict) else str(i)
            out[num or str(i)] = item
        return {k: v for k, v in out.items() if k in CHECKS}
    if isinstance(doc, dict):
        out = {}
        for key, value in doc.items():
            num = _number(key)
            if num in CHECKS and num not in out:
                out[num] = value
        return out
    raise MapError("oracle_map.yml is neither a mapping nor a list")


def _number(key) -> str | None:
    m = re.search(r"\d+", str(key))
    return str(int(m.group())) if m else None


def sql_string(text: str) -> str:
    """A SQL string literal."""
    return "'" + text.replace("'", "''") + "'"


def sql_name(text: str) -> str:
    """A quoted SQL identifier."""
    return '"' + text.replace('"', '""') + '"'


def connect(repo: Path) -> duckdb.DuckDBPyConnection:
    """One view per published mart, then file access locked to out/marts/ for the map's SQL.

    The views read Parquet lazily, so out/marts/ must stay readable; everything else (the grader's own
    files, the rest of the repository) is not, and the map's SQL cannot change the settings back. A
    symbolic link under out/marts/ would lead out of it, so a tree with one is refused.
    """
    con = duckdb.connect()
    con.execute("set TimeZone = 'UTC'")
    if any(p.is_symlink() for p in (repo / "out", repo / "out" / "marts")):
        raise MapError("out/ or out/marts/ is a symbolic link; publish the files themselves")
    marts = (repo / "out" / "marts").resolve()
    if marts.is_dir():
        links = sorted(p.relative_to(marts).as_posix() for p in marts.rglob("*") if p.is_symlink())
        if links:
            raise MapError(f"out/marts/ holds a symbolic link ({links[0]}); publish the files themselves")
        for folder in sorted(p for p in marts.iterdir() if p.is_dir()):
            if any(folder.rglob("*.parquet")):
                glob = sql_string((folder / "**" / "*.parquet").as_posix())
                con.execute(f"create or replace view {sql_name(folder.name)} as "
                            f"select * from read_parquet({glob}, union_by_name=true)")
        for file in sorted(marts.glob("*.parquet")):  # a mart published as a single file
            con.execute(f"create or replace view {sql_name(file.stem)} as "
                        f"select * from read_parquet({sql_string(file.as_posix())})")
    con.execute(f"set allowed_directories = [{sql_string(marts.as_posix() + '/')}]")
    con.execute("set enable_external_access = false")
    con.execute("set lock_configuration = true")
    return con


def _strings(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings(v)]
    if isinstance(value, (list, tuple)):
        return [s for v in value for s in _strings(v)]
    return [str(value)]


def _looks_like_sql(text: str) -> bool:
    return bool(re.match(r"\s*(with|select|from)\b", text, re.IGNORECASE))


def _table_name(text: str, con) -> str:
    """Resolve 'out/marts/x', 'main.x', 'x.parquet' or 'x' to a registered mart view."""
    views = {r[0].lower(): r[0] for r in con.execute("select view_name from duckdb_views() where not internal").fetchall()}
    candidates = [text.strip().rstrip("/")]
    base = re.split(r"[/\\]", candidates[0])[-1]
    candidates += [base, base.split(".")[-1], re.sub(r"\.parquet$", "", base)]
    if "." in base:
        candidates.append(base.split(".")[0])
    for c in candidates:
        if c.lower() in views:
            return views[c.lower()]
    # a path to a mart folder or file that exists but is named differently
    raise MapError(f"no published mart named {text!r} under out/marts/")


def resolve(entry, con) -> Result:
    hints: list[str] = []
    query = table = None
    if isinstance(entry, str):
        if _looks_like_sql(entry):
            query = entry
        elif "." in entry and not entry.endswith(".parquet") and "/" not in entry:
            table, col = entry.rsplit(".", 1)
            hints.append(col)
        else:
            table = entry
    elif isinstance(entry, dict):
        lower = {str(k).lower(): v for k, v in entry.items()}
        for k in QUERY_KEYS:
            v = lower.get(k)
            if isinstance(v, str) and (_looks_like_sql(v) or k in ("sql", "query", "select")):
                query = v
                break
            if isinstance(v, str) and k in ("view", "sql_view"):
                table = v
                break
        if query is None and table is None:
            for k in TABLE_KEYS:
                if isinstance(lower.get(k), str):
                    table = lower[k]
                    break
        for k in COLUMN_KEYS:
            hints += _strings(lower.get(k))
        if query is None and table is None:
            raise MapError(f"entry names no table or query: {entry!r}")
    else:
        raise MapError(f"entry is not a string or mapping: {entry!r}")

    if query is not None:
        sql, source = query.strip().rstrip(";"), "query"
    else:
        name = _table_name(table, con)
        sql, source = f"select * from {sql_name(name)}", f"table {name}"
    try:
        rel = _without_time_zones(con.sql(sql))
        rows = rel.fetchall()
    except duckdb.Error as exc:
        raise MapError(f"{source} failed: {str(exc).splitlines()[0]}") from exc
    return Result(columns=list(rel.columns), types=[str(t) for t in rel.types], rows=rows,
                  hints=[h.lower() for h in hints], source=source)


def _without_time_zones(rel: duckdb.DuckDBPyRelation) -> duckdb.DuckDBPyRelation:
    """Timestamps with a time zone as UTC timestamps without one. DuckDB hands TIMESTAMPTZ to Python
    only with pytz installed, which the grader does not need otherwise; Spark, for one, writes its
    TIMESTAMP to Parquet as an instant (isAdjustedToUTC), which DuckDB reads as TIMESTAMPTZ."""
    types = [str(t) for t in rel.types]
    if "TIMESTAMP WITH TIME ZONE" not in types:
        return rel
    cols = [f'"{c}"::timestamp as "{c}"' if t == "TIMESTAMP WITH TIME ZONE" else f'"{c}"'
            for c, t in zip(rel.columns, types)]
    return rel.project(", ".join(cols))
