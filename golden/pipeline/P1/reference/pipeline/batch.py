"""Batch ingestion: the raw files in data/raw/ into the Parquet lake.

Every column is landed as text, exactly as the source wrote it: codes keep their leading zeros and
amounts keep their exact decimal digits. Types are applied in the dbt staging models. Each table is
replaced on every run, so `make build` twice leaves the same lake.

    python -m pipeline.batch
"""

from __future__ import annotations

import io
import json
import zipfile
from collections.abc import Iterator

import dlt
import pyarrow as pa
import pyarrow.csv as pacsv

from .lake import ROOT, pipeline

RAW = ROOT / "data" / "raw"


def read_csv_as_text(data: bytes, encoding: str = "utf8") -> pa.Table:
    """Read a CSV with every column as a string."""
    header = data.split(b"\n", 1)[0].decode(encoding).strip().split(",")
    names = [h.strip('"') for h in header]
    return pacsv.read_csv(
        io.BytesIO(data),
        read_options=pacsv.ReadOptions(encoding=encoding),
        parse_options=pacsv.ParseOptions(newlines_in_values=True),  # quoted text spans lines
        convert_options=pacsv.ConvertOptions(column_types={n: pa.string() for n in names},
                                             strings_can_be_null=True),
    )


def usaspending(kind: str) -> Iterator[pa.Table]:
    """Each CSV inside the agency zips of one award type (Assistance or Contracts)."""
    for path in sorted((RAW / "usaspending").glob(f"FY2024_*_{kind}_Full_*.zip")):
        with zipfile.ZipFile(path) as zf:
            for member in sorted(zf.namelist()):
                if member.endswith(".csv"):
                    table = read_csv_as_text(zf.read(member))
                    yield table.append_column("source_file", pa.array([f"{path.name}/{member}"] * len(table)))


def census(vintage: str) -> pa.Table:
    # The Census Bureau publishes these files in Latin-1 (for example "Doña Ana County").
    return read_csv_as_text((RAW / "census" / f"co-est{vintage}-alldata.csv").read_bytes(), encoding="latin1")


def sitematrix() -> Iterator[dict]:
    matrix = json.loads((RAW / "sitematrix.json").read_text(encoding="utf-8"))["sitematrix"]
    for key, group in matrix.items():
        if key == "count":
            continue
        sites = group if key == "specials" else group.get("site", [])
        for site in sites:
            yield {
                "dbname": site["dbname"],
                "url": site["url"],
                "project_code": site.get("code"),
                "sitename": site.get("sitename"),
                "language_code": site.get("lang") if key == "specials" else group.get("code"),
                "language_name": None if key == "specials" else group.get("localname"),
                "is_special": key == "specials",
                "is_closed": bool(site.get("closed", False)),
                "is_private": bool(site.get("private", False)),
            }


def sources() -> list:
    replace = {"write_disposition": "replace"}
    return [
        dlt.resource(usaspending("Assistance"), name="usaspending_assistance", **replace),
        dlt.resource(usaspending("Contracts"), name="usaspending_contracts", **replace),
        dlt.resource([census("2024")], name="census_co_est2024", **replace),
        dlt.resource([census("2021")], name="census_co_est2021", **replace),
        dlt.resource(sitematrix(), name="wikimedia_sitematrix", **replace),
    ]


def main() -> None:
    info = pipeline("batch").run(sources(), loader_file_format="parquet")
    print(info)


if __name__ == "__main__":
    main()
