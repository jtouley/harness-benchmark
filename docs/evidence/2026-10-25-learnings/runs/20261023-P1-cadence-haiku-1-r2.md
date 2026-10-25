RUN_BY_COMMAND: run-learnings
Run: 20261023-P1-cadence-haiku-1-r2
Cadence: 748a729d53b401d74d7a081ec4ba08b9db444650
Packet sha256: b20f5147b3a1541abb88a48487c1cce6a56ac1d8416a1d9aa5c72348295f9a82

# Learnings: 20261023-P1-cadence-haiku-1-r2

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: yes
- transcript: yes

## Evidence counts

- dispatch: 1
- gate: 4
- hard-stop: 1
- stop-point: 1

## Proposals

### L-1
- Target: skills/vibe-test/SKILL.md
- Status: candidate
- Evidence: E-7
- Rule: hard-stop
- Key: hard-stop|vibe-test|A5|a5-gap
- Change: A5 recorded a `a5-gap` hard stop: a# vibe-test not ready # blocking gaps b# late watermark b# key. The contract names how the block avoids that state.
- Eval: pending. python -m revieweval.compare layout --config old_skill=vibe-test@748a729d53b401d74d7a081ec4ba08b9db444650 --config new_skill=vibe-test@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: SKILL.md
- Status: candidate
- Evidence: E-1
- Rule: early-stop
- Key: early-stop|cadence|A1|hard stop a#-gap a# vibe-test
- Change: The run stopped at A1: hard stop a#-gap a# vibe-test not ready # blocking gaps b# late watermark b. The block's contract names this state and the step that gets past it.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@748a729d53b401d74d7a081ec4ba08b9db444650 --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-1 | stop-point | A1 | hard stop a5-gap: A5 vibe-test NOT READY: 7 blocking gaps (B1 late watermark, B2 dedup/resume key, B3 late_events vs check 5 conflict, B4 batch idempotency, B5 CT census geography, B6 unplaced obligations, B7 award key). Report: .context/vibetest/open-data-pipeline-p1_2026-10-23.md (FAIL no active |
| E-7 | hard-stop | orchestrator | A5 vibe-test NOT READY: 7 blocking gaps (B1 late watermark, B2 dedup/resume key, B3 late_events vs check 5 conflict, B4 batch idempotency, B5 CT census geography, B6 unplaced obligations, B7 award key). Report: .context/vibetest/open-data-pipeline-p1_2026-10-23.md |
