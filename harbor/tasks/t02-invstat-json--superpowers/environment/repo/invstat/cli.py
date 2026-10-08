import argparse
import csv


def summarize(rows):
    quantity = sum(int(r["qty"]) for r in rows)
    value = sum(int(r["qty"]) * float(r["price"]) for r in rows)
    return {"items": len(rows), "quantity": quantity, "value": value}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="invstat")
    parser.add_argument("csv_path")
    args = parser.parse_args(argv)
    with open(args.csv_path, newline="") as handle:
        rows = list(csv.DictReader(handle))
    summary = summarize(rows)
    print(f"items: {summary['items']}")
    print(f"quantity: {summary['quantity']}")
    print(f"value: {summary['value']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
