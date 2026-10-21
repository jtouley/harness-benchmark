# cadence-core in tiers 1 and 2, added by following the docs (21 October 2026)

Status: measured and reproducible (tiers 1 and 2 only). No model ran. `results/` is not regenerated:
this machine cannot fetch the private `cadence` pin, so `footprint`, `probes`, `install-check --write`
and `verify` cannot run without names (see "What was not run").

*Disclosure: the owner of this benchmark wrote Cadence.*

## Question

Two questions at once:

1. What do Cadence's public successor, [`jtouley/cadence-core`](https://github.com/jtouley/cadence-core),
   cost in context, and what do its hooks block?
2. Can someone add a new repository to this benchmark on a fresh machine by following
   [Add a harness](../method/add-a-harness.md), and what gets in the way?

## Setup

- Machine: a fresh Linux cloud container. Python 3.12 (through uv), Node.js 22.22, git, Docker.
- Claude Code **2.1.306**, not the pinned 2.1.294. That made this a test of how much Claude Code version
  drift matters too.
- No `ANTHROPIC_API_KEY`, so no live tier.
- cadence-core pinned at `29315c4e64ff318a80a1a7d2c809beb4b3c15611` (its `main` on 21 October),
  installed with its own `install.sh`, the same way as the `cadence` entry, so the two rows compare.
- Probe fixtures: the `cadence` entry's fixtures, then corrected (finding 2 below).

## Results

Raw output of step 3 of the doc: [footprint.json](2026-10-21-cadence-core-tiers-1-2/footprint.json),
[probes.json](2026-10-21-cadence-core-tiers-1-2/probes.json).

| | `cadence` (`e5c3a92`, committed row) | `cadence-core` (`29315c4`) |
|---|---|---|
| Install | 650 files, deterministic | 823 files, deterministic |
| Installed items | 6 skills, 7 commands | 4 skills, 8 commands |
| Always-on tokens | 671 | 444 |
| Workflow tokens (lower–upper) | 9,078 – 62,141 | 16,364 – 138,606 |
| Hook probes meeting intent (Claude Code / Cursor) | 7/9 / 7/9 | 9/9 / 9/9 |

- **Probes.** cadence-core blocks the two probes the old pin missed: S09 (read `.env`; the new
  `guard_secret_read.py` hook) and S10 (overwrite the approved plan; the plan freeze while the P9
  marker exists). Both controls (S02 edit after approval, S07 stop when done) are allowed. S08 (no
  run active) is allowed, as before. All verdicts are the same on both hosts.
- **Workflow tokens.** The workflow is derived the same way as for `cadence` (skill `cadence`, then
  each `always` slash-command stage in `stages.json`): 10 steps. The lower count is about 1.8 times the
  old pin's. The upper count is 2.2 times, and most of it is the `cadence` skill package (128,606 of
  138,606 tokens). cadence-core installs the whole repository as the skill root, so the upper count
  includes `docs/`: about 238 KB of the 456 KB of text the count reads, mostly ADRs. The agent loads
  none of that unless it opens it. This is an upper bound by design, but for cadence-core about half
  of it is documentation.
- **Stability.** `footprint` and `probes` printed byte-identical JSON on two runs.

### The committed public rows reproduce on a newer Claude Code

With the lockfile fix in finding 3, the install trees, footprint rows and probe rows of all six public
setups (`baseline`, `superpowers`, `spec-kit`, `openspec`, `gsd-core`, `bmad`) recomputed on this
machine are byte-identical to `results/`, on Claude Code 2.1.306.

## Findings: what got in the way

1. **`fetch` with no names stops at the first repository it cannot reach.** `cadence` is second in
   the lockfile, so without Cadence access nothing after it is fetched. Workaround: name the public
   frameworks. The doc now says so.
2. **Copied probe fixtures can be silently stale.** The `cadence` fixtures write the P9 marker as
   `.context/gates/entry-invariant.ok`. cadence-core keys it per run
   (`.context/gates/entry-invariant-<pipeline_run_id>.ok`, its cd-76). With the old fixtures, `probes`
   ran without error and scored 8/9, and the miss was the S02 *control*: the fixture never reached the
   approved state. A harness that blocked everything would score the same. Fixed in
   `golden/probes/states.json` (the `approved` and `executing` states and the S04 target). The doc
   now says to check the controls first.
3. **Newer Claude Code writes new cache files during `claude plugin install`.** On 2.1.306, logged in,
   it writes `home/.claude/policy-limits.json.signature.json` and
   `home/.claude/remote-settings.json.synced-at`. Both change on every run, so `superpowers` was
   `deterministic=False`. The lockfile's `ignore` list named only the older file names. Fixed by
   widening the two rules to `policy-limits.json*` and `remote-settings.json*`. The signature file
   also carries account and organization ids, which the ignore rule keeps out of the hashed tree.
4. **`install-check` did not say which file differed.** Finding 3 needed a throwaway script. It now
   prints each path that differs between the two installs.
5. **`derive: cadence-stages` is the one harness-specific path in `cbench/`.** It worked unchanged for
   cadence-core because the repository has the same `stages.json` and `references/bundled-peers.json`
   layout. The doc now says when it applies.
6. **The doc's no-access path works, but cannot produce a README row from `results/`.** Without
   every framework, `results/` cannot be rewritten, so `REPORT.md` has no cadence-core row. The README
   row cites this page instead.

What did not get in the way: the lockfile entry and fixtures were data only; `fetch`, `install-check`,
`footprint`, `probes` and `harbor-build` ran first time for the new entry, and the full test suite
passed. The one step that took real work was reading cadence-core's gate code to correct the fixtures.

## What was not run

- `install-check --write`, `footprint`, `probes`, `report` and `verify` without names: they need the
  private `cadence` pin. cadence-core is public, so if it replaces the `cadence` pin, CI can run
  `verify` for the first time (README "Reproduce everything"). That is the owner's decision.
- The live tier: no API key here, and it spends money. `scripts/live.sh` does not list cadence-core.
- The cadence-core toy run (`examples/toy-run/run.py`) ran as a smoke check of the checkout and passed
  its gates; it is not a benchmark measurement.

## Reproduce

```bash
uv run --frozen python -m cbench fetch cadence-core
uv run --frozen python -m cbench install-check cadence-core   # cadence-core files=823 deterministic=True
uv run --frozen python -m cbench footprint cadence-core
uv run --frozen python -m cbench probes cadence-core
```
