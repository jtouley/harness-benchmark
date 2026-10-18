# Harness Benchmark

A reproducible comparison of seven ways to run Claude Code on a coding task: six workflow harnesses
([Cadence](https://github.com/jtouley/cadence), [Superpowers](https://github.com/obra/superpowers),
[Spec Kit](https://github.com/github/spec-kit), [OpenSpec](https://github.com/Fission-AI/OpenSpec),
[GSD Core](https://github.com/open-gsd/gsd-core), [BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD))
and a no-harness baseline.

> *Disclosure: the owner of this benchmark wrote Cadence.*

## What this repository shows, and what it does not

- Measured and reproducible: what each harness costs in context, and which agent actions its installed
  hooks actually block. One command recomputes it (see "Reproduce it" below).
- Exploratory: whether a harness gives better results than a strong model working alone. Seven small
  rounds, mostly one run per setup and one grader ([list of rounds](docs/evidence/README.md)).
- Not run yet: cost per solved task across all seven setups ([live tier design](docs/method/live-tier.md)).

The [claims register](docs/claims.md) lists every claim with its evidence level. The
[whitepaper](docs/whitepaper.md) gives the full argument.

So far, on small, clearly described tasks, a harness did not write better code than Opus 5.5 working
alone (Opus scored 8.00 out of 10, Cadence 7.33), and Opus alone took about a thirtieth of the time. What
harnesses did give was checking: no crashes in the code they delivered (ship-feature delivered 2 of 3
tasks), a record a reviewer can audit,
and on one real bug a review loop, with Opus as reviewer, that caught a defect the cheaper models
missed (Opus alone caught it too, at about the same cost). These are signals from small
samples, not measurements.

## Tiers 1–2: footprint and enforcement

Each harness is installed the way its own README says, at a pinned commit, then measured:

- Footprint: tokens always loaded, tokens to load the whole workflow.
- Enforcement: ten replayed agent actions (forge an approval, self-certify a verdict, edit before the
  plan is approved, stop mid-run, read `.env`, overwrite the plan, plus controls) run through each
  harness's real installed hooks. Not every scenario applies to every harness, so denominators differ.

| Harness | Pinned commit | Always-on tokens | Workflow tokens (lower–upper) | Hook probes meeting intent |
|---|---|---|---|---|
| `cadence` (see note) | `jtouley/cadence@e5c3a92` | 671 | 9,078 – 62,141 | 7/9 |
| `gsd-core` | `open-gsd/gsd-core@83aba44` | 3,457 | 4,701 – 124,702 | 4/9 |
| `superpowers` | `obra/superpowers@8ca22db` | 1,483 | 21,696 – 33,518 | 2/7 |
| `spec-kit` | `github/spec-kit@b9e08bf` | 291 | 15,889 | 2/9 |
| `openspec` | `Fission-AI/OpenSpec@9111a76` | 520 | 10,074 | 2/8 |
| `bmad` | `bmad-code-org/BMAD-METHOD@bda3c59` | 2,004 | 411 – 20,044 | 2/6 |
| `baseline` | none | 0 | 0 | 2/6 |

Measured on Linux with Claude Code 2.1.294. Full report: [`results/REPORT.md`](results/REPORT.md).
Pins and install steps: [`frameworks.lock.json`](frameworks.lock.json).

Note on Cadence: it is a private repository, so CI and outside readers cannot fetch it, and its row was
measured on macOS with Claude Code 2.1.287. Cadence has also changed since this pin
([what changed](docs/whitepaper.md#41-cadence-after-the-benchmarks-pin-status-16-october-2026)).
Cadence is in private beta: DM [@jtouley](https://github.com/jtouley) if you want to beta test it.

What the table says: only Cadence's hooks block a forged approval, a self-certified verdict, a shell edit before
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
budget that covers the worst case: see [`docs/method/live-tier.md`](docs/method/live-tier.md).

## Limitations

- No pre-registered outcome result exists yet. Everything about outcomes is exploratory.
- The live tier has six tasks. Report rates, not rankings, until more exist.
- Token counts use a proxy tokenizer (`anthropic==0.37.1`, pinned by sha256): good for comparing
  harnesses with each other, not for exact billing.
- Cursor verdicts follow Cursor's documented hook behavior. No Cursor binary was available to check them.
- The prompt each harness is started with is a choice, versioned in the lockfile.

## Where things are

Reading:

- [Claims register](docs/claims.md): every claim and how far to trust it
- [Whitepaper](docs/whitepaper.md): the argument, with methods, results and limits
- [Evidence](docs/evidence/README.md): each experiment round with its sample size, status and data
- [How results are graded](docs/method/grading.md): what decides each number, and where a model's judgment does
- [Method](docs/method/): pre-registered criteria ([v1, in force](docs/method/criteria.md);
  [v2, draft](docs/method/criteria-v2.md)), [methodology](docs/method/methodology.md),
  [how rounds were run](docs/method/process.md), [what "good code" means](docs/method/quality-model.md)
- [Plans](docs/plans/next-steps.md): experiments not yet run, and the [pipeline tasks](docs/plans/tasks/pipeline-family.md)
- [Talk](docs/talk/README.md): a 20-minute talk track

Code and data:

- `cbench/`: the benchmark tool (`python -m cbench --help`)
- `golden/`: probe scenarios, live-tier tasks and pipeline tasks
- `harbor/tasks/`: generated Harbor tasks; CI fails if they drift from the lockfile
- `harnesses/`: small harnesses used as test setups (a review loop, a verification loop)
- `results/`: committed outputs and the report

## Contributing

Pull requests are welcome. A change to a number must come with the regenerated `results/`, and
`cbench verify` must pass.

Thanks to [Harbor](https://github.com/harbor-framework/harbor) for the task format and runner, and to the
maintainers of the harnesses measured here.
