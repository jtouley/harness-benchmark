# Harness Benchmark

A reproducible comparison of seven ways to run Claude Code on a coding task: six workflow harnesses
([Cadence](https://github.com/jtouley/cadence), [Superpowers](https://github.com/obra/superpowers),
[Spec Kit](https://github.com/github/spec-kit), [OpenSpec](https://github.com/Fission-AI/OpenSpec),
[GSD Core](https://github.com/open-gsd/gsd-core), [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD))
and a no-harness baseline.

> *Disclosure: the owner of this benchmark wrote Cadence.*

## What this repository shows, and what it does not

| Claim | Evidence | Status |
|---|---|---|
| What each harness costs in context, and which agent actions its installed hooks actually block | Tiers 1–2 below, recomputed byte for byte by `cbench verify` | **Measured, reproducible** (Cadence row: see note) |
| Whether a harness produces better outcomes than a strong model alone | Seven exploratory rounds ([index](docs/experiments/README.md), [whitepaper](docs/whitepaper.md)) | **Exploratory.** Mostly one run per cell, one grader. Not a pre-registered result |
| Cost per resolved task across all harnesses (the live tier, 240 trials) | [`docs/live-tier.md`](docs/live-tier.md), [criteria v1](docs/criteria.md) | **Not run yet** |

What the exploratory rounds suggest so far: on small, precisely specified tasks a harness did **not**
write better code than Opus 5.5 alone (8.00 vs 7.33 for Cadence, at about 1/30 of the time). What
harnesses did give was verification: no crashes shipped, an audit trail, and, on a multi-cause bug, an
independent review loop that recovered a defect cheap one-shots missed (3 of 3 runs vs 1 of 10). Those are
signals on small samples, not measurements. Details and limits: [whitepaper](docs/whitepaper.md).

## Tiers 1–2: footprint and enforcement

Each harness is installed the way its own README says, at a pinned commit, then measured:

- **Footprint:** tokens always loaded, tokens to load the whole workflow.
- **Enforcement:** ten replayed agent actions (forge an approval, self-certify a verdict, edit before the
  plan is approved, stop mid-run, read `.env`, overwrite the plan, plus controls) run through each
  harness's real installed hooks. Not every scenario applies to every harness, so denominators differ.

| Harness | Pinned commit | Always-on tokens | Workflow tokens (lower–upper) | Hook probes meeting intent |
|---|---|---|---|---|
| `cadence`¹ | `jtouley/cadence@e5c3a92` | 671 | 9,078 – 62,141 | **7/9** |
| `gsd-core` | `open-gsd/gsd-core@83aba44` | 3,457 | 4,701 – 124,702 | 4/9 |
| `superpowers` | `obra/superpowers@8ca22db` | 1,483 | 21,696 – 33,518 | 2/7 |
| `spec-kit` | `github/spec-kit@b9e08bf` | 291 | 15,889 | 2/9 |
| `openspec` | `Fission-AI/OpenSpec@9111a76` | 520 | 10,074 | 2/8 |
| `bmad` | `bmad-code-org/BMAD-METHOD@bda3c59` | 2,004 | 411 – 20,044 | 2/6 |
| `baseline` | none | 0 | 0 | 2/6 |

Measured on Linux with Claude Code 2.1.294. Full report: [`results/REPORT.md`](results/REPORT.md).
Pins and install steps: [`frameworks.lock.json`](frameworks.lock.json).

¹ **Cadence is a private repository**, so CI and outside readers cannot fetch it, and its row was measured
on macOS with Claude Code 2.1.287. Cadence main has also changed since this pin
([whitepaper §4.1](docs/whitepaper.md#41-cadence-after-the-benchmarks-pin-status-16-october-2026)).
Cadence is in private beta: **DM [@jtouley](https://github.com/jtouley) if you want to beta test it.**

**Reading:** only Cadence's hooks block a forged approval, a self-certified verdict, a shell edit before
plan approval and a stop mid-run; GSD Core blocks reading `.env` and overwriting the plan, which Cadence
does not. Enforcement is what Cadence is designed for; the other harnesses never claimed it, so this shows
a different category, not a better one. Loading any harness's whole workflow costs cents.

## Reproduce it

Requires Linux or macOS, Python 3.11+, [uv](https://docs.astral.sh/uv/), Node.js 22+, git, and Claude Code
2.1.294 (`npm install -g @anthropic-ai/claude-code@2.1.294`).

```bash
git clone https://github.com/jtouley/harness-benchmark && cd harness-benchmark
uv run --frozen --with tokenizers python -m cbench fetch    # clone and build the pinned commits (network, once)
uv run --frozen --with tokenizers python -m cbench verify   # recompute everything, byte-compare with results/
```

`verify` prints `VERIFIED` when every footprint number, probe verdict and the report reproduce exactly,
and each install reproduces identically twice. It needs every framework, so without Cadence access run
`cbench install-check` on the public ones instead (that is what CI does). Installs use the fixed root
`/tmp/cbench`: do not run two `cbench` commands at once.

Other commands: `python -m cbench --help`. The live tier spends money and refuses to start without a
budget that covers the worst case: see [`docs/live-tier.md`](docs/live-tier.md).

## Limitations

- **No pre-registered outcome result exists yet.** Everything about outcomes is exploratory.
- **Six golden tasks** for the live tier. Report rates, not rankings, until more exist.
- **Token counts use a proxy tokenizer** (`anthropic==0.37.1`, pinned by sha256): good for comparing arms,
  not exact billing.
- **Cursor verdicts follow Cursor's documented hook semantics.** No Cursor binary was available to validate them.
- **Each harness's drive prompt is a choice**, versioned in the lockfile.

## Where things are

| Path | What |
|---|---|
| [`docs/whitepaper.md`](docs/whitepaper.md) | The argument: method, results, limits, what comes next |
| [`docs/experiments/`](docs/experiments/README.md) | Every outcome round with its n, status and data |
| [`docs/criteria.md`](docs/criteria.md) · [`criteria-v2.md`](docs/criteria-v2.md) | Pre-registered criteria for the live tier (v1, in force) and the next run set (v2, draft) |
| [`docs/methodology.md`](docs/methodology.md) · [`process.md`](docs/process.md) · [`quality-model.md`](docs/quality-model.md) | What "deterministic" means here, how rounds were run, what "good code" means |
| [`docs/next-steps.md`](docs/next-steps.md) · [`talk.md`](docs/talk.md) | Planned experiments; a 20-minute talk track |
| `cbench/` | The benchmark tool (`python -m cbench --help`) |
| `golden/` | Probe scenarios, live-tier tasks, pipeline tasks |
| `harbor/tasks/` | Generated Harbor tasks; CI fails if they drift from the lockfile |
| `harnesses/` | Minimal harnesses used as arms (review loop, verification loop) |
| `results/` | Committed outputs and `REPORT.md` |

## Contributing

Pull requests are welcome. A change to a number must come with the regenerated `results/`, and
`cbench verify` must pass.

Thanks to [Harbor](https://github.com/harbor-framework/harbor) for the task format and runner, and to the
maintainers of the harnesses measured here.
