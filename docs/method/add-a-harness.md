# Add a harness

How to measure another harness in tiers 1 and 2 (footprint and hook probes). The benchmark knows a
harness through two data files: its pinned install in [`frameworks.lock.json`](../../frameworks.lock.json)
and its probe fixtures in [`golden/probes/states.json`](../../golden/probes/states.json). The code in
`cbench/` does not change.

## Or ask Claude Code

Open Claude Code in a clone of this repository and paste this, with your own URL and commit:

```text
Add my harness to this benchmark: <repo URL>, pinned at commit <full sha>, installed the
way its README says. Follow docs/method/add-a-harness.md step by step. Use only `run` and
`mkdir` install ops. Write its probe fixtures in golden/probes/states.json from the files the
harness itself writes. Run every command in that doc, then the tests. Do not change other
harnesses' entries, golden/probes/scenarios.json or cbench/. At the end, list the commands
you ran, their results, and any step you could not run and why.
```

## What you need

The same as "Reproduce everything" in the [README](../../README.md#reproduce-everything): Linux or
macOS, Python 3.11+, uv, Node.js 22+, git and Claude Code 2.1.294. The harness must be in a public git
repository, so CI can fetch it.

Every command below runs as `uv run --frozen python -m cbench ...`. Installs use the fixed root
`/tmp/cbench/<name>`, because installers write absolute paths into files whose tokens are counted. Do
not run two `cbench` commands at once.

## 1. Add the lockfile entry

Add an entry under `frameworks` in `frameworks.lock.json`. The key is the harness's name in every
command and result:

```json
"my-harness": {
  "title": "My Harness",
  "repo": "https://github.com/you/my-harness",
  "sha": "<full 40-character commit>",
  "build": [],
  "install": [
    {"op": "run", "cwd": "{src}", "argv": ["bash", "./install.sh", "{proj}"]}
  ],
  "plugin_dirs": [],
  "workflow": {
    "source": "README.md 'Usage': plan, then build",
    "steps": ["skill:my-plan", "skill:my-build"]
  },
  "drive_prompt": "Use my-plan, then my-build, for this change.\n\nIssue:\n{issue}"
}
```

| Field | What it holds |
|---|---|
| `title` | The display name. |
| `repo`, `sha` | The git URL and the full commit. `fetch` fails if the checkout is not at this sha. |
| `build` | `run` steps, run once in the checkout at fetch time, with network. |
| `install` | Steps that install into a fresh sandbox. |
| `plugin_dirs` | Directories Claude Code loads as plugins. Usually `[]`. |
| `workflow` | `source`: where the README documents the workflow. `steps`: that workflow. |
| `drive_prompt` | The prompt for live runs. `{issue}` becomes the task text. |

Rules for the steps:

- A step is `{"op": "run", "cwd": ..., "argv": [...]}` or `{"op": "mkdir", "path": ...}`. Use only
  these two: `copytree` works locally, but `harbor-build` cannot translate it.
- Placeholders: `{src}` is the pinned checkout, `{home}` the sandbox home, `{proj}` the sandbox project.
  `build` steps take only `{src}`: there is no sandbox at fetch time, and `{home}` stops `fetch` with a
  `KeyError`.
- Install the way the harness's README says, but from `{src}` instead of a URL, so the sha stays
  pinned. The `superpowers` and `bmad` entries do this.
- Install steps run with no proxy variables and with `HOME` set to the sandbox. Download anything they
  need in a `build` step.
- A note for readers goes in an extra key such as `install_note`. cbench keeps it and ignores it.

Always-on tokens are not declared. `footprint` finds them in the installed sandbox: the listing line of
every skill, command and agent under `home/.claude`, `proj/.claude` and each plugin directory, the
memory files `home/.claude/CLAUDE.md`, `proj/CLAUDE.md`, `proj/.claude/CLAUDE.md` and
`proj/CLAUDE.local.md`, and the text SessionStart hooks print. Workflow tokens come from the declared
steps, each `skill:NAME` or `command:NAME`. The lower count is each step's own file; the upper count adds its
`@file` includes and the rest of its skill package.

## 2. Add the probe fixtures

The ten scenarios in [`golden/probes/scenarios.json`](../../golden/probes/scenarios.json) are the same
for every harness. Do not change them. Each puts the project into an abstract state and replays one
action through the installed hooks:

- `planning`: S01, S03, S04. `approved`: S02. `executing`: S05, S06, S09, S10. `done`: S07. `none`: S08.

Add an entry under `frameworks` in `golden/probes/states.json` that says what each state looks like in
the harness's own files:

```json
"my-harness": {
  "states": {
    "none": {},
    "planning": {"PLAN.md": "@@LONG_PLAN@@"},
    "approved": {"PLAN.md": "@@LONG_PLAN@@", "APPROVED": "ok\n"},
    "executing": {"PLAN.md": "@@LONG_PLAN@@", "APPROVED": "ok\n"},
    "done": {"PLAN.md": "@@LONG_PLAN@@", "APPROVED": "ok\n"}
  },
  "targets": {
    "forge_approval": {"path": "APPROVED", "content": "ok\n"},
    "self_verdict": null,
    "plan_doc": "PLAN.md"
  }
}
```

- `states`: project paths and their contents. `@@LONG_PLAN@@` becomes a 300-line plan. Every state also
  gets `src/app.py` and `.env` (the `common` entry).
- `targets`: the file S04 writes to forge an approval, the file S05 writes as its own passing verdict,
  and the plan S10 overwrites. Each is a path, a `{"path", "content"}` pair, or `null` when the harness
  has no such file. S04 and S05 carry no content of their own, so a bare path makes them write an empty
  file: give a `{"path", "content"}` pair with what the forged approval or verdict would say. A `null`
  target makes that scenario `n/a`, and it is not scored.

A harness with no hooks still needs an entry (see `bmad`). Without one, `probes` stops with a
`KeyError`. Verdicts are classified by the rules in [`cbench/hookrun.py`](../../cbench/hookrun.py). The
Cursor host is probed only when the install writes a `.cursor/hooks.json`.

## 3. Measure the harness

```bash
uv run --frozen python -m cbench fetch my-harness          # clone at the sha, run build steps
uv run --frozen python -m cbench install-check my-harness  # install twice, compare the trees
uv run --frozen python -m cbench footprint my-harness      # print tier 1 for this harness
uv run --frozen python -m cbench probes my-harness         # print tier 2 for this harness
```

`install-check` must print `deterministic=True`. If it does not, the installer writes something that
changes between runs, such as a timestamp. Add a rule to the lockfile's top-level `normalize` list
(`pattern`, `replace`, `why`) or `ignore` list, as the Spec Kit entry does for its timestamps.

With a name, `footprint` and `probes` print JSON and write nothing (`footprint` prints a one-line
summary per harness first, so its output is not pure JSON). A workflow step that does not match
exactly one installed skill or command stops `footprint` with a `LookupError`. Read the probe verdicts
and check that each one is what the harness's hooks should do.

## 4. Regenerate and verify

```bash
uv run --frozen python -m cbench harbor-build           # rewrite harbor/tasks
uv run --frozen python -m cbench fetch                  # every other framework, once (needs Cadence access)
uv run --frozen python -m cbench install-check --write  # rewrite results/install.json
uv run --frozen python -m cbench footprint              # rewrite results/footprint.json
uv run --frozen python -m cbench probes                 # rewrite results/probes.json
uv run --frozen python -m cbench report                 # rewrite results/REPORT.md
uv run --frozen python -m cbench verify                 # must print VERIFIED
uv run --frozen python -m pytest -q
```

`footprint.json`, `probes.json`, `install.json` and every Harbor task record the lockfile's hash, so a
new entry rewrites all of them, not only the new rows. `harbor-build` also adds one task per golden task
for the new harness.

Without names, `install-check`, `footprint`, `probes` and `verify` need every framework fetched,
Cadence included. Cadence is a private repository. Without access to it, run `harbor-build` and the
tests, and open the pull request with the JSON from step 3 and a note that `results/` is not
regenerated. The maintainer regenerates `results/` and runs `verify` before the merge (see
Contributing in the [README](../../README.md#contributing)).

What fails when a step is missing:

- `harbor/tasks` not regenerated: `test_committed_tasks_are_in_sync`, and `verify`.
- `results/` not regenerated: `verify` ("recomputed bytes differ").
- No probe fixtures: `probes` and `verify`.
- A repository CI cannot reach, or a wrong sha: the fetch step in CI.

CI fetches and install-checks every public framework and runs the tests. It runs `verify` only when no
framework is private, so while Cadence is in the lockfile, run `verify` locally.

## 5. Update the README

Add the harness's row to the table in the [README](../../README.md), with the numbers from
`results/REPORT.md`, and update the harness count. It appears in the README's first paragraph and its
first list ("all seven setups"), and in [`docs/claims.md`](../claims.md). For the live tier, also add
the name to `haiku_arms` in [`scripts/live.sh`](../../scripts/live.sh). Each Haiku arm adds 30 trials
(6 tasks, 5 trials each) and $30 to the worst case, and `live.sh` refuses a budget below the worst case.
Update the trial count and the budget in [`live-tier.md`](live-tier.md) and the trial count in
`docs/claims.md` to match.
