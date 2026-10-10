import pytest


@pytest.fixture
def cli(tmp_path, capsys):
    from ledgerlite.cli import main

    store = tmp_path / "ledger.json"

    def call(*args):
        # argparse exits through SystemExit; the code it carries is the CLI exit code.
        try:
            code = main(["--store", str(store), *args])
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 2)
        out = capsys.readouterr()
        return code, out.out.strip().splitlines(), out.err

    call.store = store
    call.tmp = tmp_path
    return call
