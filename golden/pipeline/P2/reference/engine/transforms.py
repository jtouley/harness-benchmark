"""Transforms: each turns one `transforms:` entry and the tables made so far into one new Arrow table.

- `polars`: dataframe steps, applied in a fixed order: filter, json_fields, with_columns, cast,
  rename, select. Expressions are SQL expressions (polars.sql_expr), so the YAML holds no Python.
- `datafusion`: one SQL statement over the named input tables.

Casts never go through a float: money stays a decimal from the text the source wrote.
A new engine is one function here and one entry in ENGINES (and in the schema).
"""

from __future__ import annotations

import re
from collections.abc import Callable

import datafusion
import polars as pl
import pyarrow as pa

DECIMAL = re.compile(r"decimal\((\d+), ?(\d+)\)")
TYPES = {"string": pl.String, "int64": pl.Int64, "int32": pl.Int32, "boolean": pl.Boolean, "date": pl.Date,
         "timestamp": pl.Datetime("us")}


def dtype(name: str) -> pl.DataType:
    m = DECIMAL.fullmatch(name)
    return pl.Decimal(int(m.group(1)), int(m.group(2))) if m else TYPES[name]


def _columns(frame: pl.DataFrame, pattern: str) -> list[str]:
    """A column name, or every column a ^regex$ matches."""
    if pattern.startswith("^") and pattern.endswith("$"):
        return [c for c in frame.columns if re.fullmatch(pattern[1:-1], c)]
    return [pattern]


def _cast(frame: pl.DataFrame, col: str, to: pl.DataType) -> pl.Expr:
    """A strict cast; text becomes a date or timestamp by parsing (Polars 2 has no string-to-date cast)."""
    expr = pl.col(col)
    if frame.schema[col] == pl.String and to == pl.Date:
        return expr.str.to_date(strict=True)
    if frame.schema[col] == pl.String and isinstance(to, pl.Datetime):
        return expr.str.to_datetime(time_unit="us", strict=True)
    return expr.cast(to, strict=True)


def run_polars(spec: dict, tables: dict[str, pa.Table]) -> pa.Table:
    frame = pl.from_arrow(tables[spec["input"]])
    if spec.get("filter"):
        frame = frame.filter(pl.sql_expr(spec["filter"]).fill_null(False))
    if spec.get("json_fields"):
        source = pl.col(spec["json_fields"]["column"])
        frame = frame.with_columns(source.str.json_path_match(path).alias(name)
                                   for name, path in spec["json_fields"]["fields"].items())
    if spec.get("with_columns"):
        frame = frame.with_columns(pl.sql_expr(expr).alias(name) for name, expr in spec["with_columns"].items())
    if spec.get("cast"):
        casts = {col: dtype(t) for pattern, t in spec["cast"].items() for col in _columns(frame, pattern)}
        frame = frame.with_columns(_cast(frame, col, t) for col, t in casts.items())
    if spec.get("rename"):
        frame = frame.rename(spec["rename"])
    if spec.get("select"):
        frame = frame.select(spec["select"])
    return frame.to_arrow()


def run_datafusion(spec: dict, tables: dict[str, pa.Table]) -> pa.Table:
    ctx = datafusion.SessionContext()
    for name in spec["inputs"]:
        table = tables[name]
        ctx.register_record_batches(name, [table.to_batches() or [pa.RecordBatch.from_pylist([], table.schema)]])
    return ctx.sql(spec["sql"]).to_arrow_table()


ENGINES: dict[str, Callable[[dict, dict[str, pa.Table]], pa.Table]] = {
    "polars": run_polars,
    "datafusion": run_datafusion,
}


def apply(steps: list[dict], tables: dict[str, pa.Table]) -> dict[str, pa.Table]:
    """Run each transform in order; each adds its output to the tables by its name."""
    tables = dict(tables)
    for step in steps:
        tables[step["name"]] = ENGINES[step["engine"]](step, tables)
    return tables
