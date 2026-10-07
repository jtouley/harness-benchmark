"""Install a framework into its canonical sandbox and fingerprint the result.

Every framework installs to ``<canonical_root>/<name>/{home,proj}``. The path
is fixed because several installers bake absolute paths into the prompts they
write, and those bytes are counted as tokens.
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .lock import Framework, Lock
from .util import cache_dir, canonical_json, clean_env, git_init, rmtree, run, sha256_bytes

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".cache", ".pytest_cache", ".npm"}
SKIP_FILES = {".cbench-built"}


@dataclass(frozen=True)
class Sandbox:
    root: Path
    home: Path
    proj: Path
    src: Path | None
    plugin_dirs: tuple[Path, ...]

    def fmt(self, value: str) -> str:
        return value.format(src=self.src or "", home=self.home, proj=self.proj, root=self.root)


def sandbox_for(fw: Framework, lock: Lock) -> Sandbox:
    root = lock.canonical_root / fw.name
    sb = Sandbox(root=root, home=root / "home", proj=root / "proj", src=fw.src, plugin_dirs=())
    return Sandbox(root=sb.root, home=sb.home, proj=sb.proj, src=sb.src,
                   plugin_dirs=tuple(Path(sb.fmt(p)) for p in fw.plugin_dirs))


def _pristine_dir(fw: Framework, lock: Lock) -> Path:
    return cache_dir() / "installs" / f"{fw.name}@{fw.sha or 'none'}-{lock.sha256[:12]}"


def _copy_filter(exclude: list[str]):
    def ignore(_dir: str, names: list[str]) -> list[str]:
        return [n for n in names if n in exclude or n in SKIP_DIRS]
    return ignore


def install(fw: Framework, lock: Lock) -> Sandbox:
    """Fresh install into the canonical root, then keep a pristine copy."""
    sb = sandbox_for(fw, lock)
    rmtree(sb.root)
    sb.home.mkdir(parents=True)
    sb.proj.mkdir(parents=True)
    env = clean_env(home=sb.home)
    git_init(sb.proj, env)
    (sb.proj / "README.md").write_text("# cbench project\n", encoding="utf-8")
    run(["git", "add", "-A"], cwd=sb.proj, env=env)
    run(["git", "commit", "-q", "-m", "init"], cwd=sb.proj, env=env)
    for op in fw.install:
        kind = op["op"]
        if kind == "mkdir":
            Path(sb.fmt(op["path"])).mkdir(parents=True, exist_ok=True)
        elif kind == "copytree":
            dst = Path(sb.fmt(op["to"]))
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(sb.fmt(op["from"]), dst, symlinks=True, dirs_exist_ok=True,
                            ignore=_copy_filter(op.get("exclude", [])))
        elif kind == "run":
            argv = [sb.fmt(a) for a in op["argv"]]
            run(argv, cwd=Path(sb.fmt(op["cwd"])), env=env, timeout=900, stdin="")
        else:
            raise ValueError(f"{fw.name}: unknown install op {kind!r}")
    pristine = _pristine_dir(fw, lock)
    rmtree(pristine)
    pristine.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(sb.root, pristine, symlinks=True)
    return sb


def restore(fw: Framework, lock: Lock) -> Sandbox:
    """Reset the canonical root to the pristine install (install first if missing)."""
    pristine = _pristine_dir(fw, lock)
    if not pristine.is_dir():
        return install(fw, lock)
    sb = sandbox_for(fw, lock)
    rmtree(sb.root)
    shutil.copytree(pristine, sb.root, symlinks=True)
    return sb


def normalizer(lock: Lock):
    rules = [(re.compile(r["pattern"]), r["replace"]) for r in lock.normalize]

    def apply(text: str) -> str:
        for pattern, repl in rules:
            text = pattern.sub(repl, text)
        return text
    return apply


def iter_files(base: Path, rel: str):
    """Yield (logical_path, real_path) following symlinks, skipping caches and VCS dirs."""
    stack = [(base, rel, frozenset())]
    while stack:
        current, logical, seen = stack.pop()
        try:
            real = current.resolve()
        except OSError:
            continue
        if real in seen:
            continue
        seen = seen | {real}
        try:
            entries = sorted(os.scandir(current), key=lambda e: e.name)
        except (NotADirectoryError, FileNotFoundError, PermissionError):
            continue
        for entry in entries:
            path = Path(entry.path)
            child = f"{logical}/{entry.name}"
            if entry.is_dir(follow_symlinks=True):
                if entry.name in SKIP_DIRS:
                    continue
                stack.append((path, child, seen))
            elif entry.is_file(follow_symlinks=True):
                if entry.name in SKIP_FILES or entry.name.endswith(".pyc"):
                    continue
                yield child, path


def read_text(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\x00" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def fingerprint(sb: Sandbox, lock: Lock) -> dict:
    """Tree hash of the installed sandbox after declared normalization."""
    norm = normalizer(lock)
    rows = []
    for top in ("home", "proj"):
        for logical, real in iter_files(sb.root / top, top):
            text = read_text(real)
            digest = sha256_bytes(norm(text).encode("utf-8")) if text is not None else sha256_bytes(real.read_bytes())
            rows.append((logical, digest))
    rows.sort()
    listing = "".join(f"{p}\t{d}\n" for p, d in rows)
    return {"files": len(rows), "tree_sha256": sha256_bytes(listing.encode("utf-8"))}


def install_twice_check(fw: Framework, lock: Lock) -> dict:
    """Install twice from scratch; the normalized tree hashes must match."""
    first = fingerprint(install(fw, lock), lock)
    second = fingerprint(install(fw, lock), lock)
    return {"first": first, "second": second, "deterministic": first == second}


def describe(sb: Sandbox) -> str:
    return canonical_json({"root": sb.root, "home": sb.home, "proj": sb.proj})
