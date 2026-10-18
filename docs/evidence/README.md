# Experiments index

Every outcome round so far, in order. **None of them is a criteria v1 result:** each ran outside the
Harbor live tier, and most ran once per cell with one grader. Read the n and the status before citing a
number. The synthesis is the [whitepaper](../whitepaper.md).

| Date | Round | Question | n | Graders | Status | Headline | Write-up |
|---|---|---|---|---|---|---|---|
| 10-09 – 10-10 | Iteration 3 | Do two harnesses (Cadence, ship-feature) on Opus beat Sonnet and Haiku one-shots on T04–T06? | 1 per cell | 1 blind | Exploratory; **superseded** (no Opus one-shot, so harness and model are confounded) | Harnesses scored higher, but this is evidence that Opus beats Sonnet and Haiku, not for a harness | [md](2026-10-10-harness-vs-oneshot.md) · [json](2026-10-10-harness-vs-oneshot.json) |
| 10-11 – 10-12 | Iteration 4 | Same, with the missing Opus one-shot | 1 per cell | 1 blind | Exploratory; not a clean room | Opus alone 8.00, Cadence 7.33: no quality gain shown. Harness arms shipped no crashes; one-shots shipped two each | [md](2026-10-12-iteration-4.md) · [data](2026-10-12-iteration-4/) |
| 10-13 | Pilot | Can Cadence on Haiku 5.5 deliver T05? | 1 per arm | scripted | Exploratory; clean room | No: both Cadence arms hard-stopped (P6, P9). Opus one-shot delivered in 111 s for $0.40 | [md](2026-10-13-pilot.md) · [data](2026-10-13-pilot/) |
| 10-13 – 10-14 | B01 (private bug) | Can a review loop lift cheap models on a multi-cause bug? | 5–10 per one-shot arm; 1–2 per loop arm | scripted, isolated regrade | Signal, not a reliability measure; task code is private, scores only | Both defects fixed: Opus 10/10, Sonnet 1/5, Haiku 0/5; Opus review loop 3/3 | [whitepaper §3.3](../whitepaper.md#33-a-real-multi-cause-bug-b01-a-lift-task) |
| 10-14 | SWE-bench Pro sample | Where is the Opus one-shot unreliable? | 20 tasks, 1 try per model | benchmark tests | Calibration | Opus 18, Sonnet 18, Haiku 17 of 20; Haiku at about 1/10 the cost (lower bound) | [calibration](../../calibration/README.md) · [per task](../../calibration/swebench-pro/round2.md) |
| 10-15 | Pipeline P1–P3 | First one-shots on the long-horizon pipeline tasks | 1 per model per task | scripted, 7 checks | Exploratory; some checks have open readings | Best per task: P1 Opus 6/7, P2 Opus 5/7, P3 Sonnet 5/7; Haiku 0/7 on all three. No harness has run on them | [md](2026-10-15-pipeline-trials.md) · [json](2026-10-15-pipeline-trials.json) |
| 10-10 – 10-17 | Cadence self-evidence | What did Cadence's reviews catch while building Cadence? | 10 merged runs | none (reviewer's own severity) | **Operator evidence, unsourced here**: the records are private; only the cited public PRs can be checked | 85 must-fix findings closed before merge, 73% at plan time | [md](2026-10-17-cadence-self-evidence.md) |

The scripts beside each round's data (`grade.py`, `run_arm.sh` and so on) are the exact ones used for
that round and are kept unchanged so the round can be re-graded. Current tooling lives in
[`cbench/`](../../cbench/), [`scripts/`](../../scripts/) and [`runner/`](../../runner/).

*Disclosure: the owner of this benchmark wrote Cadence.*
