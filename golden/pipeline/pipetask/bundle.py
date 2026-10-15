"""Build the two single-file executables a trial container needs (Python zipapps).

    python -m pipetask.bundle --out dist/

- `replay.pyz`: the replay server with the frozen capture inside. Stdlib only. The runner starts it as
  root before the agent, from a path the agent cannot read, so the arm can develop against
  http://localhost:8099/v2/stream/recentchange:  `python3 replay.pyz --seed <dev seed>`.
- `grader.pyz`: the grader with the answer key and the capture inside. The runner copies it in after
  the agent has finished and runs it as `grader.pyz /trial/repo` (runner/README.md). The key is read
  from the archive into memory and never written to disk, because the candidate's `make` runs while
  the grader does. The archive itself must still be unreadable to the user that runs `make` (a runner
  change, golden/pipeline/README.md). It stops nothing
  itself: the dev replay server must be stopped first, because the grader serves the grading seed on
  the same port. It needs duckdb and pyyaml, so it re-runs itself under
  `uv run --with duckdb==... --with pyyaml==...` when they are missing.
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
import zipapp
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CAPTURE = HERE / "data" / "capture" / "recentchange.jsonl.gz"
KEY = HERE / "key" / "answer_key.json"
GRADER_DEPS = ("duckdb==1.5.6", "pyyaml==6.0.3")

REPLAY_MAIN = """\
import sys, zipfile, tempfile, pathlib
from pipetask import replay
with tempfile.TemporaryDirectory() as tmp:
    with zipfile.ZipFile(sys.argv[0]) as zf:
        zf.extract("recentchange.jsonl.gz", tmp)
    args = sys.argv[1:]
    if "--capture" not in args:
        args += ["--capture", str(pathlib.Path(tmp) / "recentchange.jsonl.gz")]
    replay.main(args)
"""

GRADER_MAIN = """\
import os, sys, json, zipfile, tempfile, pathlib, subprocess
DEPS = {deps!r}
try:
    import duckdb, yaml  # noqa: F401
except ImportError:
    if os.environ.get("HB_GRADER_REEXEC"):
        raise
    cmd = ["uv", "run", "--no-project", "--python", "3.12"]
    for dep in DEPS:
        cmd += ["--with", dep]
    env = dict(os.environ, HB_GRADER_REEXEC="1")
    sys.exit(subprocess.call(cmd + ["python", sys.argv[0], *sys.argv[1:]], env=env))
from pipetask import trial
if len(sys.argv) < 2:
    sys.exit("usage: grader.pyz REPO [trial options]")
with tempfile.TemporaryDirectory() as tmp:
    with zipfile.ZipFile(sys.argv[0]) as zf:
        zf.extract("recentchange.jsonl.gz", tmp)
        key = json.loads(zf.read("answer_key.json"))  # in memory only: make runs while we do
    trial.main(["--repo", sys.argv[1], "--capture", str(pathlib.Path(tmp) / "recentchange.jsonl.gz"),
                "--seed", str(key["stream"]["seed"]), *sys.argv[2:]], key=key)
"""


def _build(out: Path, modules: list[str], data: list[Path], main: str) -> Path:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "pipetask").mkdir()
        for name in ["__init__.py", *modules]:
            shutil.copy2(HERE / "pipetask" / name, root / "pipetask" / name)
        for path in data:
            shutil.copy2(path, root / path.name)
        (root / "__main__.py").write_text(main, encoding="utf-8")
        zipapp.create_archive(root, out, interpreter="/usr/bin/env python3", compressed=True)
    out.chmod(0o755)
    return out


def bundle(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    return [
        _build(out_dir / "replay.pyz", ["schedule.py", "replay.py"], [CAPTURE], REPLAY_MAIN),
        _build(out_dir / "grader.pyz", ["schedule.py", "replay.py", "oracle.py", "grade.py", "trial.py"],
               [CAPTURE, KEY], GRADER_MAIN.format(deps=GRADER_DEPS)),
    ]


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Build replay.pyz and grader.pyz.")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    for path in bundle(args.out):
        print(path)


if __name__ == "__main__":
    main()
