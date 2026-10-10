# Harness Benchmark

A reproducible benchmark of AI coding-workflow harnesses for Claude Code: [Cadence](https://github.com/jtouley/cadence), [Superpowers](https://github.com/obra/superpowers), [Spec Kit](https://github.com/github/spec-kit), [OpenSpec](https://github.com/Fission-AI/OpenSpec), [GSD Core](https://github.com/open-gsd/gsd-core) and [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD), against a no-harness baseline. Every number is recomputed from pinned commits by one command.

## Overview

Each harness is installed the way its own README says, at a pinned commit, then measured in three tiers:

- **Footprint** (deterministic): tokens always loaded, tokens to load the whole workflow, and the dollar cost of both.
- **Enforcement** (deterministic): ten replayed agent actions (forge an approval, self-certify a verdict, edit before the plan is approved, stop mid-run, read `.env`, overwrite the plan, plus controls) run through each harness's real installed hooks.
- **Outcomes** (live, runs on [Harbor](https://github.com/harbor-framework/harbor)): six golden coding tasks with hidden tests (three small, three multi-module features). The question of note is whether a cheaper model *with* a harness meets or beats a stronger model one-shotting in Claude Code, measured as **cost per resolved task**.

## Harnesses evaluated

| Arm | Pinned commit | Installed with |
|---|---|---|
| `baseline` | none | nothing (control) |
| `cadence` | `jtouley/cadence@3ce6280` (main) | `install.sh` |
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
| `cadence` | 562 | 6,752 – 109,135 † | **7/9** |
| `gsd-core` | 3,457 | 4,701 – 124,702 | 4/9 |
| `superpowers` | 1,483 | 21,696 – 33,518 | 2/7 |
| `spec-kit` | 291 | 15,889 | 2/9 |
| `openspec` | 520 | 10,074 | 2/8 |
| `bmad` | 2,004 | 411 – 20,044 | 2/6 |
| `baseline` | 0 | 0 | 2/6 |

† Cadence's upper bound includes the `bench/` directory that its repository still ships inside the installed skill; it falls once that directory is removed.

**Conclusion (tiers 1–2):** only Cadence's installed hooks block a forged approval, a self-certified verdict, a shell edit before plan approval and a stop mid-run; GSD Core blocks reading `.env` and overwriting the plan, which Cadence does not. That is the axis Cadence is designed for. The other harnesses never claimed to enforce, so this shows a different category, not a better one. Loading any harness's whole workflow costs cents. **Whether a harness improves outcomes is not yet measured: the live tier has not run.** See [`docs/live-tier.md`](docs/live-tier.md).

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
> The full matrix is 72 trials (6 harnesses and a bare control on Haiku 5.5, plus a Sonnet 5.5 baseline,
> 3 tasks, 3 trials each). `scripts/live.sh` refuses to start unless `CBENCH_BUDGET_USD` covers the worst case
> (trials × the per-trial cap, $90 for the full matrix). Typical spend is a fraction of that.

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

- **No outcome evidence yet.** Tiers 1 and 2 measure cost and enforcement. They do not show that any harness makes the code better.
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
├── docs/                    # live-tier.md, methodology.md
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
