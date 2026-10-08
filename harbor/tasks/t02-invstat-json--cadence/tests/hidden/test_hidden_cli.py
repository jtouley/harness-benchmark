import json

import pytest

from invstat.cli import main

CSV = "sku,qty,price\nB2,10,1.00\nA1,3,2.50\nC3,0,9.99\n"


@pytest.fixture
def inv(tmp_path):
    path = tmp_path / "inv.csv"
    path.write_text(CSV)
    return str(path)


def test_text_unchanged_without_low_stock(tmp_path, capsys):
    path = tmp_path / "ok.csv"
    path.write_text("sku,qty,price\nA1,30,2.50\nB2,10,1.00\n")
    assert main([str(path)]) == 0
    assert capsys.readouterr().out == "items: 2\nquantity: 40\nvalue: 85.00\n"


def test_text_low_stock_line(inv, capsys):
    assert main([inv]) == 0
    assert capsys.readouterr().out == "items: 3\nquantity: 13\nvalue: 17.50\nlow stock: A1, C3\n"


def test_json_exact(inv, capsys):
    assert main([inv, "--format", "json"]) == 0
    out = capsys.readouterr().out
    expected = {"items": 3, "low_stock": ["A1", "C3"], "quantity": 13, "value": "17.50"}
    assert out == json.dumps(expected, indent=2, sort_keys=True) + "\n"


def test_low_stock_threshold(inv, capsys):
    assert main([inv, "--format", "json", "--low-stock", "11"]) == 0
    assert json.loads(capsys.readouterr().out)["low_stock"] == ["A1", "B2", "C3"]
    assert main([inv, "--format", "json", "--low-stock", "0"]) == 0
    assert json.loads(capsys.readouterr().out)["low_stock"] == []


def test_missing_file(tmp_path, capsys):
    missing = str(tmp_path / "nope.csv")
    assert main([missing]) == 2
    captured = capsys.readouterr()
    assert captured.err.strip() == f"invstat: cannot read {missing}"
    assert "Traceback" not in captured.err


def test_rejects_unknown_format(inv):
    with pytest.raises(SystemExit):
        main([inv, "--format", "xml"])
