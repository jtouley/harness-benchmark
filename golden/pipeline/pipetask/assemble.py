"""Assemble the repository a trial starts from: the task's skeleton plus the frozen raw data.

    python -m pipetask.assemble P1 --out /tmp/p1-repo [--with-reference]

The result is what the runner copies into the trial container as /trial/repo (`run_trial.sh --repo`).
Only `<task>/skeleton/` and `data/raw/` go in (`<task>/data/raw/` when the task has its own inputs, as P4 does). The prompt is passed separately (`--prompt
<task>/prompt.md`). Nothing else under golden/pipeline/ (the capture, the replay server, the answer key,
the grader, the reference solutions, the trap catalog) is ever copied into a trial.

`--with-reference` overlays `<task>/reference/` on top: that is how the reference solution is run and
graded. It is never used for an arm's trial.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent  # golden/pipeline
RAW = HERE / "data" / "raw"
IGNORE = shutil.ignore_patterns(".venv", "__pycache__", "target", "logs", "lake", "out", ".DS_Store")


def assemble(task: str, out: Path, *, with_reference: bool = False, git: bool = True) -> Path:
    task_dir = HERE / task
    if not (task_dir / "skeleton").is_dir():
        raise SystemExit(f"no skeleton for task {task}")
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} exists and is not empty")
    shutil.copytree(task_dir / "skeleton", out, dirs_exist_ok=True, ignore=IGNORE)
    raw = task_dir / "data" / "raw" if (task_dir / "data" / "raw").is_dir() else RAW
    shutil.copytree(raw, out / "data" / "raw", dirs_exist_ok=True, ignore=IGNORE)
    if with_reference:
        shutil.copytree(task_dir / "reference", out, dirs_exist_ok=True, ignore=IGNORE)
    if git:
        run = lambda *a: subprocess.run(["git", *a], cwd=out, check=True, capture_output=True)  # noqa: E731
        run("init", "-q", "-b", "main")
        run("add", "-A")
        run("-c", "user.name=harness-benchmark", "-c", "user.email=noreply@example.invalid",
            "commit", "-q", "-m", f"{task} skeleton")
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Assemble a pipeline task's starting repository.")
    ap.add_argument("task", help="P1, P2, P3 or P4")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--with-reference", action="store_true")
    ap.add_argument("--no-git", action="store_true")
    args = ap.parse_args(argv)
    print(assemble(args.task, args.out, with_reference=args.with_reference, git=not args.no_git))


if __name__ == "__main__":
    main()
