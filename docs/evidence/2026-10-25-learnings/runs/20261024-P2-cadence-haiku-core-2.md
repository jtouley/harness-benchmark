RUN_BY_COMMAND: run-learnings
Run: 20261024-P2-cadence-haiku-core-2
Cadence: 085bfdcd00254594ed5f22387e4316f667e59ec7
Packet sha256: a12c3f3f7cccd417397da8bc88abff899909176a8e0594ffed0e97e1bd726c07

# Learnings: 20261024-P2-cadence-haiku-core-2

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- after-document: 4
- dispatch: 6
- gate: 18
- hard-stop: 1
- stop-point: 1
- stop-refusal: 1

## Proposals

### L-1
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-15, E-17, E-18
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 3 times in E1: limit is # split each function or; consume # new; % duplicated # of # code lines.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@085bfdcd00254594ed5f22387e4316f667e59ec7 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-20, E-26
- Rule: gate-repeat
- Key: gate-repeat|cadence|implement-gate
- Change: Before the return, run the `implement-gate` gate once and fix every class it names in one pass. In this run it failed 2 times in orchestrator: implement-gate the phase commits phase # deduplication.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@085bfdcd00254594ed5f22387e4316f667e59ec7 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-12, E-22
- Rule: redispatch
- Key: redispatch|spec-driven|E1
- Change: E1 was dispatched 2 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@085bfdcd00254594ed5f22387e4316f667e59ec7 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-27
- Rule: hard-stop
- Key: hard-stop|spec-driven|E1|retries
- Change: E1 recorded a `retries` hard stop: e# implement-gate fails phases #-# share one author time. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@085bfdcd00254594ed5f22387e4316f667e59ec7 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: SKILL.md
- Status: candidate
- Evidence: E-21
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked early stop in execution. continue
- Change: The hooks refused 1 times with `blocked early stop in execution. continue`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@085bfdcd00254594ed5f22387e4316f667e59ec7 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|spec-driven|E1|hard stop retries e# implement-gate
- Change: The run stopped at E1: hard stop retries e# implement-gate fails phases #-# share one author time. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@085bfdcd00254594ed5f22387e4316f667e59ec7 --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | E1 | hard stop retries: E1 implement-gate fails: phases 4-6 share one author time (04:11:20). Two peer runs failed. The second run restored the batched history from cadence/spec-e1-backup. Branch cadence/spec reset to origin/main. Backup at cadence/spec-e1-backup (d329045). Deslop diff at .context/backup |
| E-12 | dispatch | E1 | /spec-driven dispatched as E1 |
| E-15 | gate | E1 | FAIL cognitive-complexity |
| E-17 | gate | E1 | FAIL cognitive-complexity |
| E-18 | gate | E1 | FAIL cognitive-complexity |
| E-20 | gate | orchestrator | FAIL implement-gate |
| E-21 | stop-refusal | orchestrator | BLOCKED early stop in execution. Continue paceline: next E1 (implement) via `/spec-driven`: the phase commits 'Phase 5: deduplication and lateness' and 'Phase 6: polars and DataFusion transforms' have the same author time (2026-10-24T04:11:20+00:00). In a plan of 9 phases, that is one shell, not phased work. Implement, test and commit each phase in its own step. To start again, run `git reset ori… |
| E-22 | dispatch | E1 | /spec-driven dispatched as E1 |
| E-26 | gate | orchestrator | FAIL implement-gate |
| E-27 | hard-stop | orchestrator | E1 implement-gate fails: phases 4-6 share one author time (04:11:20). Two peer runs failed. The second run restored the batched history from cadence/spec-e1-backup. Branch cadence/spec reset to origin/main. Backup at cadence/spec-e1-backup (d329045). Deslop diff at .context/backups/e1-deslop-uncommitted.patch. |
