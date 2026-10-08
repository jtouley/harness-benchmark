Use the cadence skill to ship this change end to end through R7.

Issue (ticket gh-1):
Add machine-readable output and low-stock reporting to `invstat`.

1. New option `--format {text,json}`, default `text`. Text output stays exactly as it is today.
2. New option `--low-stock N` (integer, default `5`). A row is low stock when its `qty` is
   strictly less than `N`.
3. With `--format json`, print exactly `json.dumps(obj, indent=2, sort_keys=True)` followed by a
   newline, where `obj` has these keys:
   - `items`: number of rows (int)
   - `quantity`: total of `qty` (int)
   - `value`: total of `qty * price`, as a string with exactly two decimals (e.g. `"17.50"`)
   - `low_stock`: the SKUs that are low stock, sorted ascending (list of strings)
4. Text output gets one extra final line only when there are low-stock SKUs:
   `low stock: A1, C3` (sorted, comma and space separated).
5. If the CSV file cannot be opened, print `invstat: cannot read <path>` to stderr and return `2`
   (no traceback).

`main(argv)` must keep returning the exit code instead of calling `sys.exit`.
