RUN_BY_COMMAND: run-learnings
Run: 20261024-P1-cadence-haiku-it1-1-r2
Cadence: 154e573f8455c4857982fe4e05a208e1e0bc4ecc
Packet sha256: 1866c9e79d066cee405cd855d3a238d799da416affde2a2412a92b3a82015532

# Learnings: 20261024-P1-cadence-haiku-it1-1-r2

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- after-document: 3
- dispatch: 3
- gate: 7
- hard-stop: 1
- stop-point: 1

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-7, E-9, E-11
- Rule: gate-repeat
- Key: gate-repeat|cadence|validate-gate
- Change: Before the return, run the `validate-gate` gate once and fix every class it names in one pass. In this run it failed 3 times in orchestrator: vibe-test a-# of is carried by g.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@154e573f8455c4857982fe4e05a208e1e0bc4ecc --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: skills/vibe-test/SKILL.md
- Status: candidate
- Evidence: E-6, E-8, E-10
- Rule: redispatch
- Key: redispatch|vibe-test|A5
- Change: A5 was dispatched 3 times. Name the gate's pass condition in the Deliverable section, so that one dispatch and the one fix round are enough.
- Eval: pending. python -m revieweval.compare layout --config old_skill=vibe-test@154e573f8455c4857982fe4e05a208e1e0bc4ecc --config new_skill=vibe-test@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: skills/vibe-test/SKILL.md
- Status: candidate
- Evidence: E-12
- Rule: hard-stop
- Key: hard-stop|vibe-test|A5|retries
- Change: A5 recorded a `retries` hard stop: a# validate-gate fails after three vibe-test peer rounds gap bodies cite another. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=vibe-test@154e573f8455c4857982fe4e05a208e1e0bc4ecc --config new_skill=vibe-test@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: skills/vibe-test/SKILL.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|vibe-test|A5|hard stop retries a# validate-gate
- Change: The run stopped at A5: hard stop retries a# validate-gate fails after three vibe-test peer rounds gap bodies cite. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=vibe-test@154e573f8455c4857982fe4e05a208e1e0bc4ecc --config new_skill=vibe-test@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | A5 | hard stop retries: A5 validate-gate fails after three vibe-test peer rounds: gap bodies cite another gap's A-n id (see .context/issues/public-data-pipeline-a5-gate.md) (FAIL no active cadence session) |
| E-6 | dispatch | A5 | /vibe-test dispatched as A5 |
| E-7 | gate | orchestrator | FAIL validate-gate |
| E-8 | dispatch | A5 | /vibe-test dispatched as A5 |
| E-9 | gate | orchestrator | FAIL validate-gate |
| E-10 | dispatch | A5 | /vibe-test dispatched as A5 |
| E-11 | gate | orchestrator | FAIL validate-gate |
| E-12 | hard-stop | orchestrator | A5 validate-gate fails after three vibe-test peer rounds: gap bodies cite another gap's A-n id (see .context/issues/public-data-pipeline-a5-gate.md) |
