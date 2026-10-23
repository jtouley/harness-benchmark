# Golden inputs for Cadence runs

Cadence's prompt is only the initial spec passed into Cadence. Each file here is one saved golden
input: exactly the text a run is given, and nothing else. A run of Cadence is `/cadence <spec>`,
where `<spec>` is the content of one of these files. No harness instruction, hint, answer or grader
text is added to it, and none sits in this folder. A run record (`runs/<run_id>/record.json`) names
the file in its `task` field.

| File | Scenario | Source |
|---|---|---|
| `d1.md` | The CSV export ticket LOCAL-4 with one deferral candidate (the portal upload) | Request 3 of `jtouley/cadence@9008b0e:evidence/live-runs/requests.md` |
| `d2.md`, `d3.md`, `d4.md` | The same ticket, with two deferrals asked for. The three scenarios differed in the plugin build, not in the spec, so the three files hold one text. The drivers of the d2, d3 and d4 runs name no plugin commit, so their records have `cadence` null, and the difference in build is not traceable from the records | Request 4 of the same file |
| `P1.md`, `P2.md` | The pipeline tasks P1 and P2 | Equal to `golden/pipeline/P1/prompt.md` and `golden/pipeline/P2/prompt.md`, which `pipetask/prompt.py` builds word for word from the specs |

The live runs started each spec with the `/cadence:cadence ` command prefix. The prefix is the
execution, not the spec, so it is not in the files. Each file ends with one newline.

`tests/test_golden_cadence.py` checks that the files are specs only: the P1 and P2 copies equal the
pipeline prompts, and no file shares a fingerprint (`loop/fingerprints.py`) with the answer key, the
hidden tests or the reference solutions. `python -m loop.fingerprints` fingerprints these inputs too,
so Cadence's contamination test can show that Cadence carries none of them.
