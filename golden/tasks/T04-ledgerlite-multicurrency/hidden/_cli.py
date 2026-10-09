import sys

import pytest


@pytest.fixture
def cli(tmp_path, capsys):
    from ledgerlite.cli import main

    store = tmp_path / "ledger.json"

    def call(*args):
        code = main(["--store", str(store), *args])
        out = capsys.readouterr()
        return code, out.out.strip().splitlines(), out.err

    call.store = store
    call.tmp = tmp_path
    return call
