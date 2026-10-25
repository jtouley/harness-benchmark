RUN_BY_COMMAND: run-learnings
Run: 20261024-P2-cadence-haiku-full-3
Cadence: d3c2ffe86a4a294335123290f6ca6ae836bc6afb
Packet sha256: fa9293a08cf05037894b7e18bcd3a10b8f3e34b37fb267deb3f832ca39d34b1b

# Learnings: 20261024-P2-cadence-haiku-full-3

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- after-document: 1
- dispatch: 1
- gate: 3
- hard-stop: 1
- stop-point: 1

## Proposals

### L-1
- Target: skills/vibe-test/SKILL.md
- Status: candidate
- Evidence: E-6
- Rule: hard-stop
- Key: hard-stop|vibe-test|A5|a5-gap
- Change: A5 recorded a `a5-gap` hard stop: a# vibe-test g-# blocking spec line # says a new mart is. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=vibe-test@d3c2ffe86a4a294335123290f6ca6ae836bc6afb --config new_skill=vibe-test@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: skills/vibe-test/SKILL.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|vibe-test|A5|hard stop a#-gap a# vibe-test
- Change: The run stopped at A5: hard stop a#-gap a# vibe-test g-# blocking spec line # says a new mart. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=vibe-test@d3c2ffe86a4a294335123290f6ca6ae836bc6afb --config new_skill=vibe-test@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | A5 | hard stop a5-gap: A5 vibe-test G-14 blocking: spec line 80 says a new mart is YAML only with no Python; spec line 88 says everything after the lake is the dbt project. The spec cannot close the conflict. Report: .context/vibetest/spec_2026-10-24.md (FAIL no active cadence session) |
| E-6 | hard-stop | orchestrator | A5 vibe-test G-14 blocking: spec line 80 says a new mart is YAML only with no Python; spec line 88 says everything after the lake is the dbt project. The spec cannot close the conflict. Report: .context/vibetest/spec_2026-10-24.md |
