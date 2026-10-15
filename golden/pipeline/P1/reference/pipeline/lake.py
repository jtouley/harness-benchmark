"""The Parquet lake: one dlt filesystem destination shared by the batch and the stream loads.

Every source table lands under lake/<table>/ as Parquet. dlt adds its own load metadata
(`_dlt_load_id`, `_dlt_id`) and keeps its bookkeeping in lake/_dlt_*.
"""

from __future__ import annotations

from pathlib import Path

import dlt

ROOT = Path(__file__).resolve().parent.parent
LAKE_DATASET = "lake"


def pipeline(name: str) -> dlt.Pipeline:
    destination = dlt.destinations.filesystem(
        bucket_url=ROOT.as_uri(), layout="{table_name}/{load_id}.{file_id}.{ext}"
    )
    return dlt.pipeline(
        pipeline_name=name,
        destination=destination,
        dataset_name=LAKE_DATASET,
        pipelines_dir=str(ROOT / "out" / ".dlt"),
    )
