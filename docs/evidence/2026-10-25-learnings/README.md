# Learnings from every stored Cadence run (25 October 2026)

Status: analysis only. No run was started, no agent ran, and no skill was changed. Each proposal here is a
candidate. It changes a skill only after the revision-against-current eval on stored diffs (`revieweval`,
PR #130) finds no regression.

The owner's request (25 October): "for all the cadence runs we have, have it run a postmortem that will have
it look at if there are potential learning from the skills they should come from the run? This should be added
as an optional run, but it's around self healing recursion."

## What ran

The logic of Cadence's optional R8 block `run-learnings` (pack `learning`, ADR-0031, cadence draft PR #232 at
`d9046981b0a487562573f59bb53835ef5b2fc7f6`), over each of the 86 Cadence runs in `runs/` at harness-benchmark `1262fac`:

1. `run_learnings.py collect` read the run's own records only: `record.json` (stop point), the transcript from
   the record's store, and the delivered repository bundle (fix commits). It wrote a packet of numbered
   evidence items (`E-<n>`).
2. `run_learnings.py propose` wrote the seed document with the fixed rules of R8.
3. `run_learnings.py --check` (the R8 gate) passed on all 86 documents.
4. `run_learnings.py rollup` ranked the proposal keys by the number of runs that support each.

[`run_analysis.py`](run_analysis.py) is the driver. Packets and blobs were read into a temporary folder and
deleted; each document's `Packet sha256` line names its packet.

## Files

- [`runs/<run id>.md`](runs/): one learnings document per run, with its proposals and the evidence rows they cite.
- [`ROLLUP.md`](ROLLUP.md): 205 proposal keys, ranked by run count; 88 are supported by two or more runs.

## Coverage and limits

- 71 runs have a transcript and 64 have a delivered repository. The 15 runs of 19 to 22 October with neither
  (benchmark runs before the driver stored blobs) give only their stop point.
- No delivered repository has `.context/findings.jsonl` in its git history, so the final status of findings and
  the deferrals are not in these documents. Review findings come from the `findings_io.py append` output in
  the transcript.
- The rules are fixed text matching, not judgment. In a Cadence run, the R8 command edits the seed
  document; here no agent ran, so the seed is the document.
- A proposal whose `Latest` run is older than a later Cadence change may already be addressed: for example,
  the `plan-review-round` gate is from before ADR-0028 (one plan review).
- The grader's check names are not used: the score is not an R8 input, and no proposal text carries task detail.
