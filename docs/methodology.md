# Methodology

How the three tiers work and what "deterministic" means here. Results and the conclusion are in the [README](../README.md).

## The three tiers

**Tier 1, context footprint (deterministic).** For each install, `cbench`
discovers what Claude Code would load: skills, commands, agents, `CLAUDE.md`
memory, plus the text that SessionStart hooks inject (the hooks are actually
run). It reports:

- *always-on* tokens, paid on every request;
- the whole *corpus*;
- the documented *workflow* path, given as a lower and upper bound. Lower is each
  step's own file. Upper adds the step's `@file` references and its whole skill
  package.

Costs come from [`pricing.json`](pricing.json).

**Tier 2, golden hook probes (deterministic).** [`golden/probes/`](golden/probes/)
defines 10 scenarios. Examples: "edit `src/` before the plan is approved",
"forge the approval marker", "stop mid-execution", "read `.env`". Each framework
gets fixture files for each workflow state, in its own artifact layout. The
probe builds the exact JSON payload the host would send, runs every registered
hook, and classifies the result with an explicit rule table
([`cbench/hookrun.py`](cbench/hookrun.py)). Each verdict records the rule that
produced it (`via`), so a deliberate deny can be told apart from a hook that
crashed while registered fail-closed.

**Tier 3, live golden tasks (observed).** Three golden tasks live in
[`golden/tasks/`](../golden/tasks/): a bugfix, a CLI feature and a spec-to-code module. Each has
hidden tests and a reference patch, and `golden-check` proves the hidden tests fail before the patch
and pass after it. [`python -m cbench harbor-build`](../cbench/harbor.py) turns each (task, arm) into a
[Harbor](https://github.com/harbor-framework/harbor) task whose image installs the arm from the
lockfile. Harbor runs Claude Code, grades with the same hidden tests, and records tokens and cost.
See [live-tier.md](live-tier.md).

## What "deterministic" means here

| Deterministic and verified by `verify` | Not deterministic, and how it's handled |
|---|---|
| Framework sources (pinned SHA, checked after fetch) | Model sampling in live runs: treated as an observation. Run `--trials 3+` and compare medians. |
| Installs (each installed twice; normalized tree hashes must match) | Wall-clock time (recorded, never used in grades) |
| Token counts (tokenizer file pinned by sha256) | Spec Kit's npm/PyPI dependency drift: resolved with `uv lock --exclude-newer` at the commit date |
| Hook verdicts (fixed payloads, fixed env, no network) | |
| The Harbor tasks (regenerated and compared by `verify`) | |
| The report (a pure function of `results/*.json`) | |

The tokenizer is the Claude tokenizer shipped in `anthropic==0.37.1`. It is an
older tokenizer, so Tier 1 counts are a stable proxy for comparing arms with
each other, not exact billing for current models. Tier 3 reports the usage and cost
Claude Code itself records for each trial.

## Limitations

- Cursor verdicts follow Cursor's documented hook semantics. No running Cursor
  binary was available, so they are not validated against one.
- The drive prompt that starts each framework (`drive_prompt` in the lockfile)
  is a choice. It is versioned, and its hash is stored in every run record.
- Three golden tasks are a small sample, and adding tasks is cheap. A task is a
  directory with `repo/`, `issue.md`, `hidden/` and `reference.patch`, plus a
  `task.json`. `golden-check` rejects any task whose hidden tests don't
  separate the untouched repo from the reference.
