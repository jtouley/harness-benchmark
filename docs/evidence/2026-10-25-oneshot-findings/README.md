# Antagonistic reviews of the Oct 23 P1 one-shots

Three reviews (A, B, C) each of two one-shot runs on P1: `20261023-P1-oneshot-haiku-1` and
`20261023-P1-oneshot-sonnet-1-r2` (the grader-v3 P1 baseline, per the owner's Oct 24 amendment).

- **Produced by:** read-only reviewer subagents of the coordinator session; the files call themselves
  `findings-<model>-{A,B,C}` (sonnet A signs as "Reviewer: Claude").
- **Date:** 2026-10-25. Committed by the evidence agent the same day.
- **Copied from:** the coordinator's scratchpad, `survive/run2/20261023-P1-oneshot-*/`.

## Verified versus inferred (as the files state it)

- **Verified:** the one-shot code exists only in the transcript, so each reviewer rebuilt the tree by replaying
  the transcript's writes onto the P1 skeleton plus `data/raw`, checked it against the agent's final state,
  then ran the golden grader, the answer key and targeted probes locally. Haiku A, for example, reports the
  shipped tree scores 0/7 under the grader and that three small verified fixes take it to 7/7.
- **Inferred:** anything that depends on behaviour the replay could not reproduce (network, kill commands, which
  were stubbed) is the reviewer's reading; each file says where.

## Left out

The transcripts (`transcript.jsonl`, already in runs-store) and the run directories' `PR-description.md`
(the same task text as `../2026-10-25-survive-t1/PR-description.md`).
