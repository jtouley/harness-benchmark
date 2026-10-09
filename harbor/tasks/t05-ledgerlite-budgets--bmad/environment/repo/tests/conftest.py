from pathlib import Path

import pytest

from ledgerlite.cli import run


@pytest.fixture
def ledger(tmp_path: Path):
    store = tmp_path / "ledger.json"

    def call(*args: str) -> list[str]:
        return run(["--store", str(store), *args])

    call.store = store
    call.tmp = tmp_path
    return call
