# Third independent /code-review of harness-benchmark #152 (f2250fc), findings summary (not reproduced by the reviewer)

1. compare.py:194 – has_base refusal sits inside `if not (run/"repo").exists()`; #130-era runs already have run/repo without base, so setup skips them silently. README claim "setup refuses them" is false for these runs.
2. compare.py:146 – re-layout guard only checks dispatch.jsonl; a crashed layout or deleted dispatch.jsonl lets `layout --runs 1` overwrite run-1 while old run-2/run-3 and their grading.json survive and are counted by compare() (glob run-*).
3. build.py:59 – design: clone with `-b review` leaves no local base; `git fetch <src> base:base` in setup or creating base in build.py would remove the special case.
4. compare.py:188 – has_base treats any git failure as "no base", hiding the real cause.
5. compare.py:143 – set(args.cases) raises TypeError when cases is None (programmatic callers only).
6. compare.py:145 – removed ability to add/re-lay one case within an iteration.
7. tests/test_revieweval.py:99 – hand-written subprocess git calls; prepare.py git() helper would be shorter.
8. tests/test_revieweval.py:92 – three blank lines (E303).
