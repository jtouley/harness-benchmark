# Evidence: the cadence-core pipeline runs of 21–22 October 2026

Checkable records for the six Haiku 5.5 runs of cadence-core reported in
[the write-up](../docs/evidence/2026-10-21-pipeline-cadence-core-subscription.md) (all 0 of 7), the grader
defect #49, and the baselines they are compared with. Every command below runs from the repository root
of this branch. The model sessions themselves cannot be replayed (a model run is not deterministic);
everything a session produced can be rechecked: its transcript, its Cadence records, its delivered
working tree, and its grade.

*Disclosure: the owner of this benchmark wrote Cadence.*

## Versions

| What | Value |
|---|---|
| cadence-core | `29315c4e64ff318a80a1a7d2c809beb4b3c15611` (each run's `provenance.json`) |
| harness-benchmark during the runs | `77b9ce8` (code); `golden/`, `scripts/pipeline_trial.py` and `runner/` are identical at `d8b9611`, the commit the regrades below ran on (`git diff --stat 77b9ce8 d8b9611 -- golden/ scripts/pipeline_trial.py runner/` prints nothing) |
| Task data | `golden/pipeline/data/MANIFEST.json` sha256 `f8ec37e9dd739bdcff692b889cccf33d275d42a1c3972cf633ec147f076fafa5`; answer key sha256 `571a059a15d054d38d6a37bdeafbc9012a6316af44cd96795abe0a433bf34b11` ([provenance.txt](outputs/issue49/provenance.txt)) |
| Model | requested `claude-haiku-5-5` for the orchestrator and every peer; served: `claude-haiku-5-5` for all 1,650 assistant messages of the six counted runs (claim 1) |
| Claude Code | 2.1.306 (P1-1, P1-2, P2-1, both lost runs), 2.1.307 (P1-3, P2-2, P2-3) |
| Host | Linux cloud container, 4 CPUs, 15 GB, no Docker daemon; auth: the operator's Claude subscription |

## Claims

| # | Claim | Artifact | Command to reproduce | Status |
|---|---|---|---|---|
| 1a | Each run's driver command | [`scripts/host_trial.sh`](scripts/host_trial.sh), [`scripts/queue.sh`](scripts/queue.sh); the commands as run, with times: [`docs/.../queue.log`](../docs/evidence/2026-10-21-pipeline-cadence-core-subscription/queue.log) | `PIPE_ROOT=DIR bash evidence/scripts/host_trial.sh P1 P1-cadence-core-haiku-1` (one run; `queue.sh` runs the six) | VERIFIED (see note 1) |
| 1b | The model that served each run is `claude-haiku-5-5` | [`outputs/check_runs.txt`](outputs/check_runs.txt), from [`runs/*/transcript.jsonl.gz`](runs/) | `uv run --frozen python evidence/scripts/check_runs.py` | VERIFIED |
| 1c | Each run's stop point (P4, P4, E4, P7, E4, P7) | Cadence's own record in each run's `context/sessions/by-worktree/*.json` (`hard_stop` class, reason, time; P1-1 has no hard stop, 3 stop refusals, and its last refused handoff is P4); printed in [`outputs/check_runs.txt`](outputs/check_runs.txt) | same | VERIFIED |
| 1d | The grader's output per check, for each run (all 0 of 7) | each run's `grade.json` under [`docs/.../<run>/`](../docs/evidence/2026-10-21-pipeline-cadence-core-subscription/); regraded from the delivered tree: [`outputs/regrade/`](outputs/regrade/) | `bash evidence/scripts/regrade.sh <run> OUT_DIR` | VERIFIED: the six regrades with the committed grader reproduce the six grades |
| 1e | The pushed records match the table reported to the owner | [`outputs/check_runs.txt`](outputs/check_runs.txt): 42 values compared | `uv run --frozen python evidence/scripts/check_runs.py` | VERIFIED with one correction: 41 match; P1-3 "phase commits 7" is 7 numbered phases in 8 commits (correction 1) |
| 2 | #49: a correct pipeline that publishes single-file marts scores 0, and passes with the fix | [`issue49/repro.sh`](issue49/repro.sh), [`issue49/mart_digests-single-file.patch`](issue49/mart_digests-single-file.patch), [`outputs/issue49/results.txt`](outputs/issue49/results.txt) and the four `grade-*.json` | `bash evidence/issue49/repro.sh OUT_DIR` (about 12 min) | VERIFIED: the P1 reference with single-file batch marts passes 7/7 checks and gets reward 0.0 (`idempotent: false`) from the committed grader, and 1.0 with the patch; the patch leaves the unmodified reference at 1.0 |
| 3 | The true score of the two built pipelines (P1-3, P2-2) with #49 fixed | [`outputs/regrade/regrade.log`](outputs/regrade/regrade.log), `outputs/regrade/<run>/grade-patched.json` | `bash evidence/scripts/regrade.sh P1-cadence-core-haiku-3 OUT_DIR` (and `P2-cadence-core-haiku-2`) | VERIFIED: both still 0 of 7 (`idempotent: true` with the patch; every check fails on the answer map). #49 did not decide these grades (correction 4) |
| 4a | No run read the answer key, the grader, the reference solutions or the benchmark's repository | [`scripts/isolation_search.py`](scripts/isolation_search.py), [`outputs/isolation_search.txt`](outputs/isolation_search.txt) | `python3 evidence/scripts/isolation_search.py` | VERIFIED for reads: 0 tool calls in all eight transcripts touch `/home/user/harness-benchmark`, `answer_key`, the grader (`pipetask`, `grader.pyz`, `golden/pipeline`) or `P[123]/reference`. Two `find` listings (P1-3, P2-3) returned file names under `harness-benchmark/docs/evidence/2026-10-13-pilot/`, never opened (correction 3) |
| 4b | Peers read a second copy of cadence-core | same | same | VERIFIED: tool calls with `/home/user/cadence-core` in every run (5 to 106 per run); that checkout is at `29315c4`, the arm's own commit. No tool call touches another harness's files |
| 5a | One-shot baselines: P1 Haiku 0/7, Sonnet 3/7, Opus 6/7; P2 0/7, 3/7, 5/7 | `docs/evidence/2026-10-15-pipeline-trials.json` on `origin/main` `ec54dbc` (added in `d058fb0`, moved in `19d441e`); [`outputs/baselines.txt`](outputs/baselines.txt) | `git fetch origin main ccr-3d2e0c73-lr6bdt && python3 evidence/scripts/baselines.py` | VERIFIED for the scores and the requested model |
| 5b | The one-shots were served by the model they name | — | — | UNPROVEN: the rows record the requested model; the session results that would show the served model (`results/runs/`) are git-ignored and not in the repository |
| 5c | The 19 October cadence run scored 5 of 7 on P1 with Haiku 5.5 | `docs/evidence/2026-10-19-pipeline-cadence-core/P1-cadence-core-haiku-1/` at `d4f9b00` (branch `ccr-3d2e0c73-lr6bdt`) | `python3 evidence/scripts/baselines.py` | VERIFIED: reward 0.7143, 5/7; served `claude-haiku-5-5` (its `result.json` modelUsage). It ran Cadence `b1bbdcd` on the old `jtouley/cadence` branch, not cadence-core |

## Corrections to what was reported

1. **P1-3 phase commits.** Reported 7; the run has 7 numbered phases in 8 commits (a refactor
   commit's message also names phase 3). The write-up's table now says "7 (8 commits)".
2. **Claude Code version.** The write-up said 2.1.306 for all runs; P1-3, P2-2 and P2-3 ran on
   2.1.307 (each run's `provenance.json`; the container updated Claude Code after a restart).
3. **Isolation.** "No session read anything under the benchmark's repository" holds for reads (tool
   calls), but two directory listings showed file names under `harness-benchmark/docs/evidence/`.
   The write-up now says so.
4. **#49.** The write-up said #49 "zeroed both runs that built a pipeline". It does set
   `idempotent: false` on both, but with the fix both still score 0 of 7, so it did not decide their
   grades. It does zero a correct pipeline (claim 2).

## Notes

1. The committed `host_trial.sh` is the version the six counted runs used. The first lost run
   (P1-0-killed) ran an earlier version that did not drop the operator's Claude Code session variables;
   that is why its transcript carries the operator's session id (`5b20bc6c-…`), as `check_runs.txt`
   shows. The other seven sessions each have their own id.
2. `runs/<run>/worktree-from-skeleton.patch` is the run's working tree as the grader snapshots it
   (`git add -A`, which honours the run's `.gitignore`), against the task's starting commit, without
   `data/raw/` (it is in the starting repository). `regrade.sh` applies it to a fresh
   `pipetask.assemble` repository.
3. Transcripts (`runs/<run>/transcript.jsonl.gz`) are the sessions' `stream-json` output as written,
   gzipped. They were searched for credentials and account data before publishing (no match).
4. `check_runs.py` exits 1 because of the one mismatch in 1e; the mismatch is the record, not a failure
   of the script.
