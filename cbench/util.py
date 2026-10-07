"""Shared helpers: canonical JSON, hashing, sanitized subprocess env, paths."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path
from typing import Any

BENCH_ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = BENCH_ROOT / "frameworks.lock.json"
PRICING_PATH = BENCH_ROOT / "pricing.json"
GOLDEN_DIR = BENCH_ROOT / "golden"
RESULTS_DIR = Path(os.environ.get("CBENCH_RESULTS") or BENCH_ROOT / "results")

# Variables that would let a hook or installer reach the network or the
# operator's own config. Every child process starts from a fixed allowlist.
_PASSTHROUGH = ("PATH", "SYSTEMROOT")


def cache_dir() -> Path:
    root = os.environ.get("CBENCH_CACHE") or str(Path.home() / ".cache" / "cadence-bench")
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    return path


def canonical_json(data: Any) -> str:
    """Byte-stable JSON: sorted keys, 2-space indent, trailing newline."""
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False, default=_default) + "\n"


def _default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(data), encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_env(home: Path | None = None, extra: dict[str, str] | None = None, *, network: bool = False) -> dict[str, str]:
    """Deterministic child env. Network proxies are dropped unless network=True."""
    env = {k: os.environ[k] for k in _PASSTHROUGH if k in os.environ}
    env.update(
        {
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TZ": "UTC",
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "NO_COLOR": "1",
            "FORCE_COLOR": "0",
            "CI": "1",
            "DO_NOT_TRACK": "1",
            "OPENSPEC_TELEMETRY": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "cbench",
            "GIT_AUTHOR_EMAIL": "cbench@example.invalid",
            "GIT_COMMITTER_NAME": "cbench",
            "GIT_COMMITTER_EMAIL": "cbench@example.invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
        }
    )
    if home is not None:
        env["HOME"] = str(home)
        env["UV_CACHE_DIR"] = str(cache_dir() / "uv")
        env["npm_config_cache"] = str(cache_dir() / "npm")
    if network:
        for key in ("HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY", "https_proxy", "http_proxy", "no_proxy",
                    "SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS", "REQUESTS_CA_BUNDLE", "UV_NATIVE_TLS"):
            if key in os.environ:
                env[key] = os.environ[key]
    if extra:
        env.update(extra)
    return env


def run(argv: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 600,
        stdin: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        argv, cwd=str(cwd), env=env, input=stdin, capture_output=True, text=True,
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(argv)}\n--- stdout\n{proc.stdout[-4000:]}\n--- stderr\n{proc.stderr[-4000:]}"
        )
    return proc


def rmtree(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def git_init(path: Path, env: dict[str, str]) -> None:
    run(["git", "init", "-q", "-b", "main"], cwd=path, env=env)
    run(["git", "config", "commit.gpgsign", "false"], cwd=path, env=env)
