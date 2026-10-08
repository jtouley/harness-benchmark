from invstat.cli import main


def test_text_summary(tmp_path, capsys):
    path = tmp_path / "inv.csv"
    path.write_text("sku,qty,price\nA1,3,2.50\nB2,10,1.00\n")
    assert main([str(path)]) == 0
    assert capsys.readouterr().out == "items: 2\nquantity: 13\nvalue: 17.50\n"
