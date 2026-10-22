"""Run records: runs/<run_id>/record.json (written once) and scores.jsonl (appended to).

The schemas are in loop/schema/. `validate` implements the JSON Schema keywords they use (type, enum,
pattern, required, properties, additionalProperties, items, minimum, $ref), so no new dependency.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMAS = Path(__file__).resolve().parent / "schema"
RECORD_SCHEMA = json.loads((SCHEMAS / "record.schema.json").read_text(encoding="utf-8"))
SCORE_SCHEMA = json.loads((SCHEMAS / "score.schema.json").read_text(encoding="utf-8"))
# A run id: the run's start date (YYYYMMDD), then dash-separated words, e.g. 20261021-P1-cadence-core-haiku-1.
RUN_ID = re.compile(RECORD_SCHEMA["properties"]["run_id"]["pattern"].strip("^$"))

_TYPES = {"string": str, "boolean": bool, "object": dict, "array": list, "null": type(None)}


class RecordError(Exception):
    pass


def _is(value, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES[name])


def validate(value, schema: dict, root: dict | None = None, path: str = "") -> list[str]:
    """Every way `value` breaks `schema`, as 'path: problem' lines; empty when it is valid."""
    root = root or schema
    if "$ref" in schema:
        node = root
        for part in schema["$ref"].removeprefix("#/").split("/"):
            node = node[part]
        return validate(value, node, root, path)
    where = path or "(record)"
    if "enum" in schema and value not in schema["enum"]:
        return [f"{where}: {value!r} is not one of {schema['enum']}"]
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is(value, t) for t in types):
            return [f"{where}: {value!r} is not {' or '.join(types)}"]
    errors = []
    if isinstance(value, str) and "pattern" in schema and not re.search(schema["pattern"], value):
        errors.append(f"{where}: {value!r} does not match {schema['pattern']}")
    if _is(value, "number") and "minimum" in schema and value < schema["minimum"]:
        errors.append(f"{where}: {value} is below {schema['minimum']}")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors += validate(item, schema["items"], root, f"{path}[{i}]")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        errors += [f"{path + '.' if path else ''}{k}: required" for k in schema.get("required", []) if k not in value]
        for k, v in value.items():
            sub = f"{path}.{k}" if path else k
            if k in props:
                errors += validate(v, props[k], root, sub)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{sub}: not allowed")
    return errors


def _dump(value: dict) -> str:
    return json.dumps(value, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def write_record(runs: Path, rec: dict) -> Path:
    """Write runs/<run_id>/record.json, once. Refuses an invalid record or one that exists."""
    errors = validate(rec, RECORD_SCHEMA)
    if errors:
        raise RecordError("invalid record: " + "; ".join(errors))
    path = runs / rec["run_id"] / "record.json"
    if path.exists():
        raise RecordError(f"{path} already exists; records are append-only, use a new run id")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8") as f:
        f.write(_dump(rec))
    return path


def append_score(runs: Path, score: dict) -> Path:
    """Append one grader score to runs/<run_id>/scores.jsonl."""
    errors = validate(score, SCORE_SCHEMA)
    if errors:
        raise RecordError("invalid score: " + "; ".join(errors))
    grader = score["grader"]
    if score["source"] != "backfill" and (grader["commit"] is None or grader["tree"] is None or "basis" in grader):
        raise RecordError("a driver or regrade score names the grader commit and tree it ran; only a backfill "
                          "may leave them unknown or inferred")
    if score["source"] == "backfill" and (grader["commit"] is None or grader["tree"] is None) and "basis" not in grader:
        raise RecordError("a backfilled score with an unknown grader says why in grader.basis")
    run = runs / score["run_id"]
    if not (run / "record.json").exists():
        raise RecordError(f"no record for run_id {score['run_id']} in {runs}")
    path = run / "scores.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(score, sort_keys=True, ensure_ascii=False) + "\n")
    return path


def load(run: Path) -> dict:
    return json.loads((run / "record.json").read_text(encoding="utf-8"))


def scores(run: Path) -> list[dict]:
    path = run / "scores.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
