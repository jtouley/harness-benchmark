# Harness Benchmark

A reproducible benchmark of AI coding-workflow harnesses for Claude Code: [Cadence](https://github.com/jtouley/cadence), [Superpowers](https://github.com/obra/superpowers), [Spec Kit](https://github.com/github/spec-kit), [OpenSpec](https://github.com/Fission-AI/OpenSpec), [GSD Core](https://github.com/open-gsd/gsd-core) and [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD), against a no-harness baseline. Every number is recomputed from pinned commits by one command.

## Findings so far

> **Does a harness beat a strong model working alone?** Two exploratory rounds on three feature tasks
> (T04–T06, one run per cell, one blind grader) found **no quality gain**: Opus 5.5 alone scored 8.00
> out of 10 and Cadence on Opus 7.33, at about 1/30 of the time. Most of that gap is single-run noise.
> **What the harness did show:** no crash reached its delivered code (each one-shot shipped two), an
> audit trail a reviewer can check, completion on every task or a recorded stop, and rules the model
> cannot skip.
>
> **Since then (October 13–14):** full Cadence on Haiku 5.5 delivered nothing in the pilot (it stopped in
> its own loops). On a real multi-cause bug, Haiku and Sonnet one-shots fixed the main path but the second
> defect in only 0/5 and 1/5 runs, against Opus 10/10; an independent review loop recovered it in 3/3 runs,
> at about the Opus one-shot's cost. The cheap models miss by **scope narrowing and coverage**, not
> reasoning depth. On a 20-task SWE-bench Pro sample (one try per model), a one-shot Haiku 5.5 passed
> 17 against Opus 5.5's 18 at about one tenth of the cost; the open questions there are the tasks where
> Opus is unreliable and pass rates over repeats. **Next:** cheap verification (contracts before code, real-time deferral review),
> long-horizon pipeline tasks, and traceability when work goes wrong. Full argument: the
> [**whitepaper**](docs/whitepaper.md).
> *Disclosure: the owner of this benchmark wrote Cadence.*

| Arm (iteration 4) | Delivered | Blind quality | Major or critical defects per run | Crashes shipped | Time per task | Audit trail |
|---|---|---|---|---|---|---|
| Opus 5.5 one-shot | 3 of 3 | 8.00 | 1.00 | 2 | 2 min | 1 commit |
| ship-feature (Opus) | 2 of 3 | 7.88 (2 tasks) | 0.67 | 0 | 42 min | plan and reviews |
| Cadence (Opus) | 3 of 3 | 7.33 | 0.67 | 0 | 63 min | plan, 6 reviews by separate agents, verified ledger |
| Sonnet 5.5 one-shot | 3 of 3 | 7.08 | 1.33 | 2 | 2 min | 1 commit |
| Haiku 4.5 one-shot | 1 of 3 | 3.50 (1 task) | 2.67 | 2 | 4 min | none |

| Read | For |
|---|---|
| [**Whitepaper**](docs/whitepaper.md) | The whole argument, iteration 4 to now: method, results, why cheap models miss, what a harness is for |
| [**What a harness buys you**](docs/findings.md) | The conclusions: what we got from Cadence, what we did not, and what one-shotting gives |
| [**20-minute talk track**](docs/talk.md) | Slides, numbers and speaker notes, with the questions to expect |
| [**Next steps**](docs/next-steps.md) | The cheapest model that matches Opus with an audit trail: Claude Code, Cursor CLI and OpenAI arms |
| [Iteration 4](docs/experiments/2026-10-12-iteration-4.md) · [Iteration 3](docs/experiments/2026-10-10-harness-vs-oneshot.md) | Full write-ups, data, confounds |
| [How the rounds were run](docs/process.md) | The process end to end, what went wrong, and the clean-room check |
| [**Quality model**](docs/quality-model.md) | What "great code" means here: ISO/IEC 25010, measured by published tools and thresholds |
| [Pilot](docs/experiments/2026-10-13-pilot.md) · [Calibration](calibration/README.md) | Cadence on Haiku 5.5; how tasks are chosen against the Opus one-shot; SWE-bench Pro sample |
| [**Pipeline task family**](docs/tasks/pipeline-family.md) | Long-horizon tasks: one spec on three stacks (dlt and dbt; Arrow, Polars and DataFusion; Spark), a follow-up change, and a traceability audit |
| [Harness arms](harnesses/) | Minimal harnesses used as arms: a review loop and a verification harness (contracts before code) |

These rounds ran outside the Harbor live tier, so they are not [criteria v1](docs/criteria.md) results.

## Overview

Each harness is installed the way its own README says, at a pinned commit, then measured in three tiers:

- **Footprint** (deterministic): tokens always loaded, tokens to load the whole workflow, and the dollar cost of both.
- **Enforcement** (deterministic): ten replayed agent actions (forge an approval, self-certify a verdict, edit before the plan is approved, stop mid-run, read `.env`, overwrite the plan, plus controls) run through each harness's real installed hooks.
- **Outcomes** (live, runs on [Harbor](https://github.com/harbor-framework/harbor)): six golden coding tasks with hidden tests (three small, three multi-module features). The question of note is whether a cheaper model *with* a harness meets or beats a stronger model one-shotting in Claude Code, measured as **cost per resolved task**.

## Harnesses evaluated

| Arm | Pinned commit | Installed with |
|---|---|---|
| `baseline` | none | nothing (control) |
| `cadence` | `jtouley/cadence@812998f` (main) | `install.sh` |
| `superpowers` | `obra/superpowers@8ca22db` | `claude plugin marketplace add` + `claude plugin install` |
| `spec-kit` | `github/spec-kit@b9e08bf` | `specify init --integration claude` |
| `openspec` | `Fission-AI/OpenSpec@9111a76` | `openspec init --tools claude` |
| `gsd-core` | `open-gsd/gsd-core@83aba44` | `bin/install.js --claude --local` |
| `bmad` | `bmad-code-org/BMAD-METHOD@bda3c59` | `skills add` (the Skills CLI route) |

The installers differ in kind, and that is part of the result: Cadence runs a shell script,
Spec Kit, OpenSpec and GSD run their own CLIs, Superpowers is a Claude Code plugin, and BMAD is a
set of skills. Pinned sources are installed from local checkouts of the pinned sha, so the
documented command runs but the commit cannot drift. See [`frameworks.lock.json`](frameworks.lock.json).

### Benchmark Results (October 2026)

Tiers 1 and 2, measured on Linux with Claude Code 2.1.294. Source: [`results/REPORT.md`](results/REPORT.md).

| Harness | Always-on tokens | Workflow tokens (lower–upper) | Hook probes meeting intent |
|---|---|---|---|
| `cadence` | 671 | 8,965 – 59,055 | **7/9** |
| `gsd-core` | 3,457 | 4,701 – 124,702 | 4/9 |
| `superpowers` | 1,483 | 21,696 – 33,518 | 2/7 |
| `spec-kit` | 291 | 15,889 | 2/9 |
| `openspec` | 520 | 10,074 | 2/8 |
| `bmad` | 2,004 | 411 – 20,044 | 2/6 |
| `baseline` | 0 | 0 | 2/6 |

**Conclusion (tiers 1–2):** only Cadence's installed hooks block a forged approval, a self-certified verdict, a shell edit before plan approval and a stop mid-run; GSD Core blocks reading `.env` and overwriting the plan, which Cadence does not. That is the axis Cadence is designed for. The other harnesses never claimed to enforce, so this shows a different category, not a better one. Loading any harness's whole workflow costs cents. **The live tier has not run, so no criteria v1 outcome result exists yet.** Two exploratory outcome rounds ran outside it: see [Findings so far](#findings-so-far) and [`docs/live-tier.md`](docs/live-tier.md).

**Criteria:** what counts as a harness being worth its cost, the neutral one-shot baseline, the measures and the pre-registered decision rule are in [`docs/criteria.md`](docs/criteria.md) (v1).

## Setup Requirements

- Linux or macOS, Python 3.11+, [uv](https://docs.astral.sh/uv/), Node.js 22+, git
- Claude Code 2.1.294 (`npm install -g @anthropic-ai/claude-code@2.1.294`): the `superpowers` install uses its `claude plugin` command
- Docker and `harbor==0.24.0` for the live tier only

## Installation

```bash
git clone https://github.com/jtouley/harness-benchmark
cd harness-benchmark
uv run --frozen --with tokenizers python -m cbench fetch      # clone the pinned commits, build (network, once)
```

## Running Benchmarks

### Verify the committed results

```bash
uv run --frozen --with tokenizers python -m cbench verify     # recompute everything, byte-compare with results/
```

It prints `VERIFIED` when every footprint number, probe verdict and the report reproduce exactly,
and each install reproduces identically twice.

> [!NOTE]
> The installs use the fixed root `/tmp/cbench`, so do not run two `cbench` commands at once.

### Individual tiers

```bash
python -m cbench footprint        # tier 1 -> results/footprint.json
python -m cbench probes           # tier 2 -> results/probes.json
python -m cbench golden-check     # hidden tests fail on the untouched repo, pass with the reference patch
python -m cbench report           # results/*.json -> results/REPORT.md
```

### Live tier (spends money)

```bash
uv tool install harbor==0.24.0
python -m cbench harbor-build --check
CBENCH_BUDGET_USD=1 ANTHROPIC_API_KEY=... scripts/live.sh smoke   # one Haiku trial, capped at $1
```

> [!WARNING]
> The full matrix is 240 trials (6 harnesses and a bare control on Haiku 5.5, plus a Sonnet 5.5 baseline,
> 6 tasks, 5 trials each as [criteria](docs/criteria.md) §6 fixes). `scripts/live.sh` refuses to start unless
> `CBENCH_BUDGET_USD` covers the worst case (trials × the per-trial cap, $300 for the full matrix). Typical
> spend is a fraction of that.

Design, what Harbor does and does not support, and how to read the results: [`docs/live-tier.md`](docs/live-tier.md).

### CI

`.github/workflows/verify.yml` runs `fetch`, `verify` and the tests on every push and uploads `results/`.
`.github/workflows/live.yml` is manual-only, needs the `ANTHROPIC_API_KEY` repository secret, and refuses
to start without a budget that covers the worst case.

## Results

| File | Contents |
|---|---|
| `results/footprint.json` | Tier 1: tokens and cost per harness and model |
| `results/probes.json` | Tier 2: one verdict per harness, host and scenario, with the rule that produced it |
| `results/golden.json` | Golden task validity and hashes |
| `results/install.json` | Install tree hashes and the install-twice check |
| `results/live.json` | Tier 3: one record per Harbor trial (written by `harbor-collect`) |
| `results/REPORT.md` | All of the above, as a report |

## Limitations

- **No criteria v1 outcome evidence yet.** Tiers 1 and 2 measure cost and enforcement. The two exploratory outcome rounds ([findings](docs/findings.md)) ran once per cell with one grader, on small precise tasks. They found no quality gain from a harness on those tasks.
- **Six golden tasks is a small sample.** Report rates, not rankings, until more tasks exist. Adding a task is a directory: `repo/`, `issue.md`, `hidden/`, `reference.patch`, `task.json`.
- **Token counts use a proxy tokenizer** (`anthropic==0.37.1`, pinned by sha256), good for comparing arms with each other and not exact billing.
- **The Cursor verdicts follow Cursor's documented hook semantics.** No Cursor binary was available to validate them.
- **The drive prompt for each harness is a choice.** It is versioned in the lockfile.
- Methodology and what "deterministic" means here: [`docs/methodology.md`](docs/methodology.md).

## Project Structure

```
harness-benchmark/
├── frameworks.lock.json     # pinned arms: commits, build and install steps, drive prompts
├── pricing.json             # $/MTok per model, with source and date
├── cbench/                  # the harness (python -m cbench --help)
├── golden/
│   ├── probes/              # tier 2 scenarios and per-harness fixtures
│   └── tasks/               # tier 3 tasks: repo, issue, hidden tests, reference patch
├── harbor/
│   ├── tasks/               # generated Harbor tasks (python -m cbench harbor-build)
│   └── agents/              # Claude Code agent that keeps each harness's install
├── scripts/live.sh          # live tier with a spend guard
├── results/                 # committed outputs and REPORT.md
├── docs/                    # findings.md, talk.md, next-steps.md, process.md, criteria.md,
│                            # live-tier.md, methodology.md, experiments/
└── .github/workflows/       # verify.yml, live.yml
```

## Customizing the Benchmark

1. Add or bump a harness: edit `frameworks.lock.json` (repo, sha, build and install steps from its README), then `fetch`, `install-check --write`, `footprint`, `probes`, `report`.
2. Add a golden task or probe scenario under `golden/`, then `golden-check`.
3. Regenerate the Harbor tasks with `python -m cbench harbor-build`. CI fails if `harbor/tasks` drifts from the lockfile.

## Contributing

Pull requests are welcome. A change to a number must come with the regenerated `results/`, and `cbench verify` must pass.

## Acknowledgments

[Harbor](https://github.com/harbor-framework/harbor) for the task format and runner, and the maintainers of the harnesses measured here.
