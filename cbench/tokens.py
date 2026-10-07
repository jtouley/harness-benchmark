"""Pinned, offline token counter.

The counter is the Claude tokenizer that ships inside ``anthropic==0.37.1``
(``anthropic/tokenizer.json``), loaded with ``tokenizers==0.20.3``. Its bytes
are pinned by sha256, so every machine produces identical counts.

It is an older Claude tokenizer, not the one current models use. Counts are a
deterministic proxy suited to comparing frameworks against each other; absolute
billing figures come from the usage that live runs record (tier 3).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

TOKENIZER_SHA256 = "c241737df24b4e7f7c9af4fdcee29a0ca903dcb288a8b753bc346a3092911767"
TOKENIZER_ID = "anthropic==0.37.1:anthropic/tokenizer.json"


def tokenizer_path() -> Path:
    import anthropic  # pinned in bench/pyproject.toml; used only for this asset

    return Path(anthropic.__file__).resolve().parent / "tokenizer.json"


@lru_cache(maxsize=1)
def _tokenizer():
    from tokenizers import Tokenizer

    from .util import sha256_file

    path = tokenizer_path()
    digest = sha256_file(path)
    if digest != TOKENIZER_SHA256:
        raise RuntimeError(f"tokenizer.json sha256 {digest} != pinned {TOKENIZER_SHA256}")
    return Tokenizer.from_file(str(path))


def count(text: str) -> int:
    if not text:
        return 0
    return len(_tokenizer().encode(text, add_special_tokens=False).ids)


def provenance() -> dict:
    _tokenizer()
    return {"id": TOKENIZER_ID, "sha256": TOKENIZER_SHA256, "kind": "deterministic-proxy"}
