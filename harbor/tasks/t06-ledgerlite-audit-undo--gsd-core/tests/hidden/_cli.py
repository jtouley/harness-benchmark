import pytest


def _shell_code(value):
    """The exit code a shell sees: None is 0, an int is itself, anything else is 1."""
    if value is None:
        return 0
    return value if isinstance(value, int) else 1


@pytest.fixture
def cli(tmp_path, capsys):
    from ledgerlite.cli import main

    store = tmp_path / "ledger.json"

    def call(*args):
        # A return value and a SystemExit both become the code the CLI exits with.
        try:
            code = _shell_code(main(["--store", str(store), *args]))
        except SystemExit as exc:
            code = _shell_code(exc.code)
        out = capsys.readouterr()
        return code, out.out.strip().splitlines(), out.err

    call.store = store
    call.tmp = tmp_path
    return call
