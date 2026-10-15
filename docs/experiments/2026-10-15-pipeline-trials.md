# Pipeline family: first trials on the isolated runner (2026-10-15)

The first runs of the pipeline tasks ([P1, P2, P3](../tasks/pipeline-family.md)) through the isolated
runner (`runner/`, wired in this change: [golden/pipeline/README.md](../../golden/pipeline/README.md#a-trial-on-the-isolated-runner)).
The machine was the test laptop: Apple Silicon, Docker Desktop with 8 CPUs and 16 GB, arm64 images, one
trial at a time. The spec asks for an x86-64 host with 32 GB, so treat these times as laptop times.

Each trial: the starting repository (`pipetask.assemble`), the prompt word for word, the dev replay
(seed 0) during the agent's session, then the grader (seed 1) running the candidate's `make` as the agent
user with a fresh HOME and no network. Rows come from `scripts/pipeline_trial.py summary`. Cost is from
token counts at [`pricing.json`](../../pricing.json) list prices.

## Step 2: smoke trials and negative controls (no agent)

| Run | Task | Repository | Reward | Checks | Grading s | First build s | Grading s without first build |
|---|---|---|---|---|---|---|---|
| P1-ref-smoke | P1 | reference | 1.0 | 7/7 | 244.2 | 46.3 | 198.0 |
| P1-ref-1 | P1 | reference | 1.0 | 7/7 | 168.2 | 23.5 | 144.7 |
| P1-ref-2 | P1 | reference | 1.0 | 7/7 | 156.5 | 16.0 | 140.5 |
| P1-ref-deadline | P1 | reference, with the P1 deadline | 1.0 | 7/7 | 155.3 | 14.6 | 140.7 |
| P1-skel-1 | P1 | skeleton unchanged | 0.0 | 0/7 | 5.5 | — | — |
| P2-ref-1 | P2 | reference | 1.0 | 7/7 | 158.2 | 16.1 | 142.1 |
| P2-ref-2 | P2 | reference | 1.0 | 7/7 | 153.7 | 14.7 | 139.0 |
| P2-skel-1 | P2 | skeleton unchanged | 0.0 | 0/7 | 2.2 | — | — |
| P3-ref-1 | P3 | reference | 1.0 | 7/7 | 350.3 | 94.3 | 256.0 |
| P3-ref-2 | P3 | reference | 1.0 | 7/7 | 357.4 | 99.9 | 257.5 |
| P3-skel-1 | P3 | skeleton unchanged | 0.0 | 0/7 | 2.3 | — | — |

- Every reference scores 1.0 and every untouched skeleton 0, on all three tasks.
- Every grading run had the agent user's network blocked, so every build used the image's warm cache
  only: uv for P1 and P2; coursier, ivy and the pip wheelhouse for P3 (`timing.json`:
  `agent_network_during_grading: blocked`).
- `P1-ref-smoke` ran while the P3 image was being built beside it, so it is slower. It is not one of the
  measurements for the caps.

### Measured caps (owner default: worst case of the reference trials plus 50%)

| Task | Reference grading runs (s) | Worst | Grading deadline (`--deadline`) | Runner backstop (`--grader-timeout`) |
|---|---|---|---|---|
| P1 | 168.2, 156.5 | 168.2 | 253 s | 373 s |
| P2 | 158.2, 153.7 | 158.2 | 238 s | 358 s |
| P3 | 350.3, 357.4 | 357.4 | 537 s | 657 s |

A grading run includes two `make build` runs and two `make stream` runs of 30 s and 90 s
(DURATION), so about 120 s of every deadline is the stream durations themselves. The values are in
`runner/pipeline/caps.json`. The agent's guard cap is 7,200 s for every one-shot trial.
