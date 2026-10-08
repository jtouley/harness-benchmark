"""Load the lockfile and fetch + build each framework at its pinned commit."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .util import LOCK_PATH, cache_dir, clean_env, load_json, run, sha256_file


@dataclass(frozen=True)
class Framework:
    name: str
    title: str
    repo: str | None
    sha: str | None
    build: list[dict[str, Any]]
    install: list[dict[str, Any]]
    plugin_dirs: list[str]
    workflow: dict[str, Any]
    drive_prompt: str
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def src(self) -> Path | None:
        if not self.repo:
            return None
        return cache_dir() / "src" / f"{self.name}@{self.sha}"


@dataclass(frozen=True)
class Lock:
    canonical_root: Path
    normalize: list[dict[str, str]]
    ignore: list[str]
    frameworks: dict[str, Framework]
    drive_suffix: str
    sha256: str


def load_lock(path: Path = LOCK_PATH) -> Lock:
    raw = load_json(path)
    fws = {}
    for name, spec in raw["frameworks"].items():
        known = {"title", "repo", "sha", "build", "install", "plugin_dirs", "workflow", "drive_prompt"}
        fws[name] = Framework(
            name=name,
            title=spec["title"],
            repo=spec.get("repo"),
            sha=spec.get("sha"),
            build=spec.get("build", []),
            install=spec.get("install", []),
            plugin_dirs=spec.get("plugin_dirs", []),
            workflow=spec.get("workflow", {}),
            drive_prompt=spec.get("drive_prompt", "{issue}"),
            extra={k: v for k, v in spec.items() if k not in known},
        )
    return Lock(
        canonical_root=Path(raw["canonical_root"]),
        normalize=raw.get("normalize", []),
        ignore=raw.get("ignore", []),
        frameworks=fws,
        drive_suffix=raw.get("drive_suffix", ""),
        sha256=sha256_file(path),
    )


def select(lock: Lock, names: list[str] | None) -> list[Framework]:
    if not names:
        return list(lock.frameworks.values())
    unknown = [n for n in names if n not in lock.frameworks]
    if unknown:
        raise SystemExit(f"unknown framework(s): {', '.join(unknown)}; known: {', '.join(lock.frameworks)}")
    return [lock.frameworks[n] for n in names]


def _built_marker(fw: Framework) -> Path:
    return fw.src / ".cbench-built"


def fetch(fw: Framework, *, rebuild: bool = False) -> None:
    """Clone at the pinned SHA (verified), then run the lockfile build steps once."""
    if fw.src is None:
        return
    env = clean_env(home=cache_dir() / "build-home", network=True)
    (cache_dir() / "build-home").mkdir(parents=True, exist_ok=True)
    if not (fw.src / ".git").is_dir():
        fw.src.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "init", "-q", str(fw.src)], cwd=fw.src.parent, env=env)
        run(["git", "remote", "add", "origin", fw.repo], cwd=fw.src, env=env)
        run(["git", "fetch", "-q", "--depth", "1", "origin", fw.sha], cwd=fw.src, env=env, timeout=900)
        run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], cwd=fw.src, env=env)
    head = run(["git", "rev-parse", "HEAD"], cwd=fw.src, env=env).stdout.strip()
    if head != fw.sha:
        raise RuntimeError(f"{fw.name}: checkout is at {head}, lockfile pins {fw.sha}")
    if _built_marker(fw).exists() and not rebuild:
        return
    # Builds may regenerate tracked files, so cleanliness is checked before building.
    dirty = run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=fw.src, env=env).stdout.strip()
    if dirty:
        raise RuntimeError(f"{fw.name}: tracked files modified in {fw.src}:\n{dirty}")
    for step in fw.build:
        argv = [a.format(src=fw.src) for a in step["argv"]]
        cwd = Path(step.get("cwd", "{src}").format(src=fw.src))
        run(argv, cwd=cwd, env=env, timeout=1800)
    _built_marker(fw).write_text(fw.sha + "\n", encoding="utf-8")


def tracked_tree_sha(fw: Framework) -> str | None:
    if fw.src is None:
        return None
    env = clean_env()
    return run(["git", "rev-parse", "HEAD^{tree}"], cwd=fw.src, env=env).stdout.strip()


def ensure_fetched(fws: list[Framework]) -> None:
    for fw in fws:
        if fw.src is not None and not (fw.src.is_dir() and _built_marker(fw).exists()):
            raise SystemExit(f"{fw.name} is not fetched/built; run: python -m cbench fetch {fw.name}")
    os.environ.setdefault("CBENCH_FETCHED", "1")
