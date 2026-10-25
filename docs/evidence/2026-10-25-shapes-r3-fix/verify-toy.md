# /verify (cadence:verify) on the fix branch

Procedure: `.claude/skills/verify/SKILL.md` of the cadence repo. Sandbox HOME in the session scratchpad, a
detached worktree of the commit under test, `install.sh` twice, the Cursor hooks driven with `sh -c` from the
installed `~/.cursor/hooks.json`, and each core `stages.json` gate run as written from a toy repo
(`feature/gh-7-toy`, `.cadence.json` adapter `none`, gated prefix `src/`), with each peer played by writing
its artifact where its doc says. The activation and the gates ran with `env -i` (host `other`, as Cursor).

Commit under test: `b45c1bb` for the install and the pipeline. `22786e6` and `fdfb554` came after it. They change
the label of P4's text-check lines and the work rule for `python3 -I -c`, and ci_local covers them.

## Install

| Step | Result |
|---|---|
| `install.sh` (1) | exit 0 |
| `install.sh` (2) | exit 0. `~/.claude/settings.json` and `~/.cursor/hooks.json` are byte-equal to the first install (only `.bak` copies are added) |
| Claude Code budget hook matcher | `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash\|Read\|Grep\|Glob` (from hooks.json) |

## Cursor hooks (preToolUse, Write)

| State | `src/x.py` | `README.md` |
|---|---|---|
| repo that never ran Cadence | allow, no `.context/` written | - |
| active session, before P9 | deny (`gated path src/x.py requires entry invariant`) | allow |
| after P9 | allow | - |

## Pipeline, A1 to R7 (core)

| Block | Gate as written | Result |
|---|---|---|
| A1 | `activate_session.py --check` | OK |
| A5 | `validate_gate.py` | OK (after the Task hook wrote the lean record) |
| P1 | `plan_create_gate.py`, plan without the spec's output `NOTES.md` in Phase 1 | FAIL: `Deliverables: the spec names NOTES.md as an output (spec line 6), and the first phase ... does not write it` |
| P1 | same, `NOTES.md` in Phase 1 | OK |
| P3 | `plan_review_gate.py` | OK |
| P4 | `plan_update_gate.py` before the update | FAIL: no revision ledger for MF-1 (expected) |
| P4 played as P1 full-3 | update section with `RUN_BY_COMMAND: plan-update` at the end, acceptance row 1 narrowed in place | `plan_create_gate.py` OK (the stop guard's walk no longer loops P1/P4); `plan_update_gate.py` FAIL `row 1 does not quote item 1` |
| P4 after its fix | `plan_update_gate.py` | OK |
| P9 | `entry_invariant.py --phase execution` | OK |
| E1 | `implement_gate.py` before, after phase 1, after phase 2 | FAIL phase 1 of 2, FAIL phase 2 of 2, OK |
| E4 | `draft_pr_gate.py` (local PR record) | OK |
| R1 | `pr_review_local_gate.py` | FAIL on a walk row with an exit-code-only output, then OK |
| fix round packet | `handoff_inputs.packet_for("E1")` from the installed tree | `/spec-driven .context/plans/cd-7.plan.md --fix-round .context/findings.jsonl --must-fix cd-7-3c5ace2b-MF-1`, ledger pinned by sha256 |
| fix round lean check | Cursor Task hook | the pointer form allowed; the P2 core-1 form (`/spec-driven <plan> <review path>`) still denied |
| fix round | fix commit, `findings_io.py set-status fixed`, `ledger_verify.py` | verified 1, errors 0 |
| R2 | `test_benchmark_gate.py --code` | FAIL on adversarial inputs with no `expected`, then OK |
| R3 | `cognitive_complexity_gate.py` | OK (ruff and mypy were not in the sandbox HOME's uv cache, so the gate named them and did not fail) |
| R5 | `closure.py --check` | FAIL: clean-checkout record at the pre-fix head. After `clean_checkout.py`: OK, 1 must-fix, acceptance 2 of 2 |
| R7 | `activate_session.py --deactivate`, `--status` | deactivated, status completed |

The probes "second ticket", "resume" and "corrupt findings.jsonl" from the skill were not repeated (no change
touches them).
