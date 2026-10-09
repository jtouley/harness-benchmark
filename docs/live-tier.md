# Live tier (Harbor)

Tier 3 asks the question the first two tiers cannot: **does the harness change
outcomes?** It runs Claude Code on the six golden tasks with each framework
installed, then grades the result with hidden tests. [Harbor](https://github.com/harbor-framework/harbor)
(pinned to 0.24.0) runs the trials, grades them and records tokens and cost.
Nothing here is run by CI by default. A run spends money.

## Design

| Arm | Model | Why |
|---|---|---|
| `baseline` | Haiku 5.5 | Control: the same small model with no framework. |
| `cadence`, `superpowers`, `spec-kit`, `openspec`, `gsd-core`, `bmad` | Haiku 5.5 | The cheap model with each harness. |
| `baseline` | Sonnet 5.5 | One-shotting in Claude Code with a stronger model. |

The comparison of note is **cost per resolved task**, and whether *Haiku + harness*
meets or beats *Sonnet one-shot*. A trial is *resolved* only when every hidden test
passes. Three trials per cell; a task has three tests of code, so report rates, not
rankings, until more tasks exist.

## What Harbor does and does not do

Checked against Harbor 0.24.0's docs and source:

- **Custom tasks.** A task is a directory: `instruction.md`, `task.toml`,
  `environment/` (Dockerfile), `tests/test.sh` (writes `/logs/verifier/reward.json`),
  optional `solution/`. `python -m cbench harbor-build` generates all of them from
  `frameworks.lock.json` and `golden/tasks/`. The Dockerfile fetches the pinned sha,
  then runs the lockfile's own build and install steps.
- **Skills only, not hooks.** Harbor's `--skill` and `skills_dir` install directories that
  contain a `SKILL.md`. They do not install hooks, slash commands or plugins, and most
  frameworks need those. So each arm installs itself inside the image, the way its own
  README says (`harbor/tasks/*/environment/Dockerfile`), and Harbor only runs the agent.
- **Config directory.** Harbor's `claude-code` agent sets `CLAUDE_CONFIG_DIR` to a fresh
  directory and copies only `~/.claude/skills` into it, which would drop Cadence's hooks and
  Superpowers' plugin. [`harbor/agents/cbench_claude.py`](../harbor/agents/cbench_claude.py)
  is a 10-line subclass that also seeds that directory from `~/.claude`. Everything else is stock.
- **Tokens and cost.** Each trial's `result.json` has `agent_result.n_input_tokens`
  (including cache), `n_cache_tokens`, `n_output_tokens` and `cost_usd`. For Claude Code,
  `cost_usd` is the `total_cost_usd` Claude Code reports; Harbor falls back to a LiteLLM
  estimate. `python -m cbench harbor-collect` copies these into `results/live.json`.

## Run it

Needs Docker, [uv](https://docs.astral.sh/uv/), and an Anthropic API key.

```bash
uv tool install harbor==0.24.0
uv run python -m cbench harbor-build --check        # tasks match the lockfile
harbor run -p harbor/tasks -i 't01-slugify-bugfix--cadence' -a oracle -y   # reference patch passes: no API cost
harbor run -p harbor/tasks -i 't01-slugify-bugfix--baseline' -a nop -y     # untouched repo fails: no API cost

export ANTHROPIC_API_KEY=...
CBENCH_BUDGET_USD=1 scripts/live.sh smoke           # one Haiku trial, capped at $1
CBENCH_BUDGET_USD=90 scripts/live.sh                # the full matrix
uv run python -m cbench harbor-collect jobs && uv run python -m cbench report
```

> [!WARNING]
> `scripts/live.sh` refuses to start until `CBENCH_BUDGET_USD` is at least the worst case
> (trials × the per-trial `--max-budget-usd` cap). The full matrix is 63 Haiku trials at a
> $1 cap plus 9 Sonnet trials at a $3 cap, so the worst case is $90. Typical spend is a
> fraction of that, and the cap is enforced per trial by Claude Code.

## Notes for restricted networks

The Dockerfile pulls base images from `mirror.gcr.io` and installs from npm, PyPI and GitHub.
In a sandbox that re-terminates TLS, build with `python -m cbench harbor-build --proxy-ca CA.pem`
and `docker build --network host`.
