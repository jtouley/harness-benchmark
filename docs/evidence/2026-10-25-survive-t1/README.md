# Review of the P1 core-6 Cadence run (commit 736d6fe, "change under review")

Three independent antagonistic reviews of the tree delivered by run `20261024-P1-cadence-haiku-core-6`, a
consolidated final review, a plain explanation of the PR, and the probe and oracle scripts the reviewers wrote.

- **Produced by:** read-only reviewer subagents of the coordinator session. The files name them only as
  reviewers A, B and C (`findings-t1-{A,B,C}.txt`), plus a consolidation (`final-review-t1.md`) and an explainer
  (`explain-t1.md`). No agent ran with write access to the reviewed tree.
- **Date:** 2026-10-25 (file times 01:40 to 02:38 UTC). Committed by the evidence agent the same day.
- **Copied from:** the coordinator's scratchpad, `survive/run2/t1/`, `review-t1A/` and `review_t1C/w/`.

## Files

| Path | What it is |
|---|---|
| `findings-t1-A.txt`, `-B.txt`, `-C.txt` | The three reviews. Each states its method at the top. |
| `final-review-t1.md` | Merges A, B and C, re-checks each item, verdict **Request changes**, with a tested patch. |
| `explain-t1.md` | What the PR does, what the explainer verified, verdict that it does what the description asks. |
| `PR-description.md` | The task description given to the run (the reviews call it "the spec"). |
| `scripts/` | Reviewer B's probes (`probe_*.py`) and batch oracle (`oracle_batch.py`). |
| `probes/drift/*.parquet` | Three tiny schema-drift inputs used by the probes. |
| `reviewers/review-t1A/` | Reviewer A's oracles: `oracle.py` (fresh SSE capture), `batch_oracle.py`, `compare.py`, `anyv.py`, `q.py`, `probes/probe_ns*.py`. |
| `reviewers/review-t1C/` | Reviewer C's oracles (`oracle_batch.py`, `oracle_stream.py`, `restarts.py`, `pending.py`, `q.py`), its build and stream logs, and `stream_consumer.orig.py`, the unmodified consumer it probed. |

## Verified versus inferred (as the files state it)

- **Verified by the reviewers' own runs:** checks 1 to 4 against independent Decimal oracles reading the raw
  USAspending zips and Census CSVs (all three reviewers); the stream numbers on the replay (21,502 events,
  12,876 edits, 60 late, 674 windows); `make stream` failing on a fresh tree (A F1); one malformed event
  crashing the consumer and sticking on restart (B F1); the check-7 test never running (C F1). Each fix in
  `final-review-t1.md` marked "Fix (verified)" was run in a scratch clone.
- **Not verifiable:** `spec/spec.md` is not in the tree or its history, so every finding that depends on the
  spec's wording is marked spec-dependent (A F0, B F0, C P0).
- **Not tested:** the live Wikimedia endpoint (no network). The missing `User-Agent` finding is an inference.

## Paths and what was left out

The scripts expect the reviewed tree and the local replay on `localhost:8099`. Paths inside the files point at
the coordinator's scratchpad, which is not kept. Left out: the reviewed tree and its scratch clones
(`tree/`, `work/`, `work2/`, `review-t1A/fresh`, `review-t1A/w`, `review_t1C` outside `w/`), the probes' `lake/`
and `out/` data, `review-t1A/replay.pkl` (25 MB, the pickled replay capture that `compare.py` reads; `oracle.py`
re-creates it) and `review-t1A/award_a.parquet` (oracle output data).
