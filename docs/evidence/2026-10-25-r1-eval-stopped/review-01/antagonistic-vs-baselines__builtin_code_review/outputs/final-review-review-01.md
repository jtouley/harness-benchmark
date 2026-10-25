Code review of commit c176f99 ("Change under review", on top of d176e80) in /var/tmp/revieweval/antagonistic-vs-baselines/review-01/builtin_code_review/run-1/repo. The review did not modify the repo. I ran the tests in a scratch copy, at /tmp/claude-0/-home-user/fd6221f8-f79d-5dc4-b0f6-aa7efcbaf9ac/scratchpad/repo.

Verification
- `uv run python -m unittest discover -s tests -t .`: 49 tests, OK (1 skipped).
- The dbt build (26 tests) and `tests/check_rerun.py` both passed.
- The obligations_per_person macro's integer rounding is correct (half away from zero, scale 0.0001).
- The late rule is consistent between pipeline/lateness.py and the SQL oracle macro stream_raw_arrivals().
- sitematrix.json has no duplicate dbnames, so the fact_edit left join cannot fan out.

Findings

1. Medium: a malformed HTTP reply crashes the stream consumer. pipeline/stream_consumer.py:157-160 catches only OSError around `self._connect()`. `_connect` (lines 184-189) can raise http.client.HTTPException, for example BadStatusLine from `getresponse()`. That exception escapes `run()` and ends the process. I confirmed this with a local server that replies "GARBAGE": `run()` raised `BadStatusLine`. The spec's intent, reconnect and keep going, is not met. Fix: catch `(OSError, http.client.HTTPException)` at line 159. Also close `conn` if `request()` or `getresponse()` raises inside `_connect`, since that currently leaks the connection.

2. Low: pipeline/batch_load.py robustness in `_extract_usaspending`.
   - Line 31 takes `archive.namelist()[0]` as the CSV. It should select the `.csv` member explicitly, because a directory entry or extra file first in the archive would be extracted as the data.
   - Line 29, `next(k for k in USASPENDING_KINDS ...)`, has no default. A zip that matches the `FY2024_*_Full_*.zip` glob but is neither Contracts nor Assistance fails with a bare StopIteration. A clear error message would help.

Not changed or flagged: the code path around the window_5min incremental watermark. I read it and did not find a concrete failure, so I did not report it.
