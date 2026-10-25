# Second independent /code-review of harness-benchmark #152 (97c8e41), verbatim summary of findings

1. compare.py:193 – clone-without-base fix doesn't help runs laid out under #130: `source` points at WORK/built/<case>/repo, which has no `base`; setup re-clones from the same source and fails again on every setup. Only a full re-layout fixes it; README doesn't say so.
2. compare.py:190 – setup deletes the clone whenever `git rev-parse` fails for any reason (dubious ownership, git unavailable), losing reviewer probes. `git -C` on a folder without .git searches parents, so a broken run/repo can pass if the outer checkout has `base`.
3. compare.py:146 – the overwrite guard only runs when cases are named; a full `layout --iteration it` still silently rewrites dispatch.jsonl, configs.json, steps.json, grader.md, source over an in-progress iteration.
4. compare.py:146 – the same guard blocks redoing an identical subset layout.
5. tests/test_revieweval.py:110 – no test of setup on a run whose source points at built/repo, nor a full re-layout over an existing iteration.
6. test_revieweval.py:99 – unused setup (names[:2], uses names[0]); imports inside functions.
7. compare.py:143 – cases() reads cases.json twice; unknown-case check runs after names already dropped.
8. compare.py:148 – meta moved for no reason.
9. survey-shapes-r2.md:14 – still states "match in 9 of 10 runs" citing deleted v3work/grade_all.log:64, unlabelled.
10. review-skill/sources/postmortem-weaknesses.md:222 – frozen source points at deleted check-attribution.md; needs a note in that folder's README.
