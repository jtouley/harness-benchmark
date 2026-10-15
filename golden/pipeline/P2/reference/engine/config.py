"""Read a pipeline file and check it before anything runs.

Two checks, both reported as `<file>:<line>: <problem>`:

1. The file against the JSON Schema in pipeline.schema.yml (shape, types, allowed values).
2. The references: every table a transform or sink reads is made by an earlier step, no name is
   defined twice, and in a stream pipeline every sink reads the stream (directly or through transforms).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import jsonschema
import yaml

SCHEMA = yaml.safe_load((Path(__file__).with_name("pipeline.schema.yml")).read_text(encoding="utf-8"))
ENV = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


class ConfigError(Exception):
    """One or more problems in a pipeline file, one `<file>:<line>: <problem>` per line."""


@dataclass(frozen=True)
class Pipeline:
    path: Path
    name: str
    sources: list[dict]
    transforms: list[dict]
    sinks: list[dict]
    micro_batch: dict


def _node_at(node: yaml.Node, path) -> yaml.Node:
    """The YAML node at a JSON path (keys and indexes), or the deepest one that exists."""
    for part in path:
        if isinstance(node, yaml.MappingNode):
            match = next((v for k, v in node.value if k.value == part), None)
        elif isinstance(node, yaml.SequenceNode) and isinstance(part, int) and part < len(node.value):
            match = node.value[part]
        else:
            match = None
        if match is None:
            break
        node = match
    return node


def _line(root: yaml.Node, path) -> int:
    return _node_at(root, list(path)).start_mark.line + 1


def _schema_problems(doc, root: yaml.Node) -> list[tuple[int, str]]:
    validator = jsonschema.Draft202012Validator(SCHEMA)
    problems = []
    for error in validator.iter_errors(doc):
        where = "/".join(str(p) for p in error.absolute_path) or "(top)"
        problems.append((_line(root, error.absolute_path), f"{where}: {error.message}"))
    return problems


def _reference_problems(doc: dict, root: yaml.Node) -> list[tuple[int, str]]:
    problems, defined = [], {}

    def define(name: str, path: list) -> None:
        if name in defined:
            problems.append((_line(root, path), f"'{name}' is already defined on line {defined[name]}"))
        else:
            defined[name] = _line(root, path)

    def read(name: str, path: list) -> None:
        if name not in defined:
            problems.append((_line(root, path), f"'{name}' is not defined by an earlier source or transform"))

    for i, source in enumerate(doc.get("sources", [])):
        define(source["name"], ["sources", i, "name"])
        if source.get("rejects"):
            define(source["rejects"], ["sources", i, "rejects"])
    for i, step in enumerate(doc.get("transforms", [])):
        if step["engine"] == "polars":
            read(step["input"], ["transforms", i, "input"])
        else:
            for j, name in enumerate(step["inputs"]):
                read(name, ["transforms", i, "inputs", j])
        define(step["name"], ["transforms", i, "name"])
    tables: dict[str, int] = {}
    for i, sink in enumerate(doc.get("sinks", [])):
        read(sink["input"], ["sinks", i, "input"])
        if sink["table"] in tables:
            problems.append((_line(root, ["sinks", i, "table"]), f"lake table '{sink['table']}' is written twice"))
        tables[sink["table"]] = i
    streams = [s for s in doc.get("sources", []) if s["type"] == "sse"]
    if len(streams) > 1:
        problems.append((_line(root, ["sources"]), "a pipeline reads at most one stream source"))
    if streams and any(s["mode"] != "append" for s in doc.get("sinks", [])):
        problems.append((_line(root, ["sinks"]), "a stream pipeline's sinks must use mode: append"))
    if streams:
        # Static tables are joined into every micro-batch, so a sink fed only by them would append the
        # same rows once per micro-batch. Each sink must read the stream, directly or through a transform.
        from_stream = {streams[0]["name"], streams[0].get("rejects")}
        for step in doc.get("transforms", []):
            if set(step.get("inputs") or [step.get("input")]) & from_stream:
                from_stream.add(step["name"])
        for i, sink in enumerate(doc.get("sinks", [])):
            if sink["input"] in defined and sink["input"] not in from_stream:
                problems.append((_line(root, ["sinks", i, "input"]),
                                 f"'{sink['input']}' does not come from the stream source, so the sink would "
                                 f"append it again on every micro-batch"))
    if not streams and any(s["mode"] != "replace" for s in doc.get("sinks", [])):
        problems.append((_line(root, ["sinks"]), "a batch pipeline's sinks must use mode: replace"))
    return problems


def _expand_env(value):
    if isinstance(value, str):
        return ENV.sub(lambda m: os.environ.get(m.group(1)) or (m.group(2) or ""), value)
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    return value


def load(path: Path) -> Pipeline:
    """The checked pipeline in a file; ConfigError lists every problem found."""
    text = path.read_text(encoding="utf-8")
    try:
        root = yaml.compose(text, Loader=yaml.SafeLoader)
        doc = yaml.safe_load(text)
    except yaml.MarkedYAMLError as exc:
        line = exc.problem_mark.line + 1 if exc.problem_mark else 1
        raise ConfigError(f"{path}:{line}: not valid YAML: {exc.problem}") from exc
    if root is None:
        raise ConfigError(f"{path}:1: the file is empty")
    problems = _schema_problems(doc, root)
    if not problems:
        problems = _reference_problems(doc, root)
    if problems:
        raise ConfigError("\n".join(f"{path}:{line}: {msg}" for line, msg in sorted(problems)))
    doc = _expand_env(doc)
    return Pipeline(path=path, name=doc["pipeline"], sources=doc["sources"], transforms=doc.get("transforms", []),
                    sinks=doc["sinks"], micro_batch=doc.get("micro_batch", {}))
