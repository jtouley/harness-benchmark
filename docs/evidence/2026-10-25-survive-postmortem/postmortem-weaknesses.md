# Postmortem: where Cadence falls short (from the review evidence)

Date: 2026-10-25. Read-only. No network, no agents launched.
Tags: **[V]** means I checked it with my own tool calls on the cited source. **[I]** means I inferred it. **[L]** means I took it from the postmortem log without checking it again.

## Sources I read

- The postmortem doc (WbaPy7W4Qc2EZL9R68B1oA, node 4da1cefd-e759, rev 313): the front matter and the log entries from Oct 25 00:05 to 03:45.
- `survive/run2/`: `t1/findings-t1-{A,B,C}.txt`, `t1/final-review-t1.md`, `t1/explain-t1.md`, `t1/PR-description.md` (the spec), `20261023-P1-oneshot-{haiku-1,sonnet-1-r2}/findings-*-{A,B,C}.txt`.
  - **Missing:** `survey-shapes-r2.md` does not exist yet, and the two one-shot consolidations are not written. Only core-6 has a final review.
- cadence at the pinned commit `2100c6e`: `SKILL.md`, `stages.json`, `commands/pr-review-local.md`, `references/review-rigor.md`, `skills/test-benchmark/SKILL.md`, `scripts/test_benchmark_gate.py`, ADR-0009 and ADR-0028.
  - Local branches (no network): `r1-deterministic`/`fix/gate-asserts-output` @9314a61 (I take this to be #228's line), `fix/enforcement-gate` @4c437ca, `fix/speed-slo` @4d36756 (#229, the head matches the log), and `feat/antagonistic-review` @cc367f5.
- harness-benchmark (the `/home/user/work/hb-audit` checkout): `runs/20261024-*/record.json`, `scores.jsonl`, `audit.json`, `postmortems/2026-10-24-shapes-r2.md` and `baselines.json`.
  - Transcripts from `runs-store/blobs`, and the core-6 transcript `work/scratch/core6.jsonl`. Its sha256 870ecb7c… matches record.json **[V]**. Transcript line numbers below are 1-based lines of that file.
  - The core-6 git history is in `work/scratch/core6.git`.

## The numbers that underlie all four questions [V]

- **The batch.** The shapes-r2 batch has 11 runs at cadence 2100c6e (P1 full-5 has no record).
  - Scores, round(reward×7): P1 core-6 4/7. P1 full-6, P2 core-6 and P2 full-6 2/7 each. The other 7 runs 0/7.
  - Mean 0.73/7. The P1 core mean is 1.33 and the P2 core mean is 0.67.
- **Voided runs.** Five of the zeros passed 1–3 checks, but `stream_ok=false` voided the reward (postmortem `2026-10-24-shapes-r2.md` Timeline, lines 16-28). Two runs do not count because of isolation hits.
- **Agent time.** Agent wall time averages 128 min (P1 163, P2 99). The ratio to the pinned Haiku one-shot runs from 2.27 to 8.35, with a mean of 4.4 (postmortem lines 54-64).
- **Cost.** `reported_usd` runs from $2.04 to $5.75, with a mean of $3.41.
- **The Oct 23 one-shots,** graded on the same grader tree 8a0977e:
  - The Haiku one-shot regraded to **5/7** at $0.95.
  - The Sonnet r2 one-shot scored **5/7** at $2.25.
  - Under the owner's rule they are not the baseline (that is Oct 15), but on the same grader they beat Cadence's best run.

## Q1. "Robustness is about even with the one-shots, and the shared defects come from the stack"

**Verdict: half right, and not yet measurable.**

**The comparison is not like for like [V]:**
- core-6's findings are consolidated: reproduced, with severities adjusted against the spec. The one-shots have raw A/B/C files only.
- Each arm has n=1.
- The one-shot code was rebuilt by replaying the transcripts' Bash commands (`findings-sonnet-A.txt:5-10`). The Cadence code came from the bundle.

**Defects shared by core-6 and at least one one-shot [V]:**

| Defect | Haiku one-shot | Sonnet one-shot | core-6 |
|---|---|---|---|
| A crash between dlt normalize and load loses events | B-F1 | A-F2 is related | H2 |
| An empty external mart publishes an all-NULL row, so check 7 is wrong | A-L1, B-F3, C-F2 | — | M2 |
| `make stream` fails on a fresh tree | A-L3, B-F6, C-F5 | C-F4 | M1 |
| Check 4 is a tautology | B-F8, C-F7 | B-F3 | M5 |
| The lake is not raw | B-F10 | A-F9, C-F6 | M4 |

**Where the shared defects come from:**
- Only the first two are stack behaviour: dlt pending packages, and dbt-duckdb's placeholder row for an empty `external` table.
- The other three come from the task. They are the easy reading of the spec (spec lines 40-48 and check 4 at line 67). **[I]**

**Where Cadence did better or worse than the one-shots:**
- **Better, through R1 fixes:**
  - The CT 2021 fallback (MF-3). Sonnet C-F2 double-counts Connecticut.
  - Place-of-performance geography. The Haiku one-shot A-H2 has this wrong.
  - Reconnect handling. Sonnet A-F1 and C-F1 are a HIGH crash on timeout or reset; core-6 survived 41 restarts (final-review M-section).
- **Not better:** the core-6 classes that only a crash, a fresh clone, empty input or malformed input brings out.

**Root cause:** no Cadence block tests those input conditions.
- `references/review-rigor.md:30-33` (R1/R2 adversarial inputs) lists Cadence's own CLI cases: "another ticket's leftovers, `--resume`, an adjacent id (`cd-1` vs `cd-12`), an offline host without `gh`". That list is unchanged on #228, on #229 and in the new skill **[V]**.
- The core-6 R1 wrote these off as "not applicable to this CLI" (its review, in transcript line 1570) **[V]**.
- E1's contract (`commands/spec-driven.md`) has no rule for a crash at a stage boundary or for a fresh-clone run of each entry point **[I]**: I grepped it and found nothing; dispatch item 5 checks this.

## Q2. "Of the 28 issues on core-6, R flagged and fixed none"

**Verdict: true as stated, but by construction, so it is the wrong metric.**

The outside reviewers saw the final code (736d6fe, after the fixes). An item that R fixed fully cannot appear among their 28.

**What R did [V], from the R1 review (transcript line 1570) and the commits in `core6.git`:**
- R1 raised MF-1 to MF-9 and N-1 to N-7.
- The fix round committed MF-1 to MF-9, plus R2-F01 to F03.
- Per the log **[L]**, 2 of the 12 fixes would have been outside findings, 8 of the 28 were flagged but left open, and 20 were never flagged.

**Root causes, each with its file:**
1. **The adversarial-input list fits a different domain.** See `review-rigor.md:30-33` above. R1 never tried a kill during a write, a fresh-tree `make stream`, or an empty mart. That gives M1, M2 and H2 **[V]**.
2. **R1 counted a pass it never saw.**
   - R1's End-to-end walk step 4 says "PASS=12 including … test_late_events_count".
   - In R1's tool results, that test name appears only in a diffstat, a file listing, DECISIONS and the complexity record (transcript lines 1429, 1451, 1455, 1461, 1531). It never appears in dbt output.
   - Step 6 checked `oracle_map.yml` "Cleared by reading", which missed M5 **[V]**.
   - The walk rule at `review-rigor.md:24-26` (2100c6e) allowed this.
   - #228/#229 now require an observed-output table (`8fefa55`). The gate checks the table's form. It does not check that a claimed test name or count appears in captured output **[I]**.
3. **The fixes covered the instance, not the class.**
   - `commands/pr-review-local.md:40` says "write each must-fix item so that one fix commit can settle it".
   - MF-1 named only `length` and `timestamp`. Commit `acd9d90` checks exactly those fields, so the namespace, bot and type crashes remain (M6) **[V]**.
4. **A HIGH issue was filed as a nit.**
   - R1's N-3 is the HIGH H1 silent exit 0 ("Not probed; read from code").
   - `review-rigor.md:6` ("If you can't reproduce a finding, drop it") and ADR-0009 / `pr-review-local.md:64-65` (open nits go to Follow-ups with no fix) put it there.
   - Nothing ties severity to a spec line. The outside consolidation did tie them (`final-review-t1.md:34-43`) **[V]**.
5. **Nothing reviewed the deferrals.**
   - The deferral review is in packs that core does not turn on: P8 (`stages.json:167`, deferral-register) and R4 (`stages.json:299`, deferrals).
   - core-6 hard-stopped at R2 (record.json `stop_point`), so R3, R5 and R7 never ran on it **[V]**.

## Q3. "About 7x slower and 2.5–6x costlier"

**Verdict: the figures are wrong for the batch.**

**Time [V]:**
- The batch mean is 4.4x the pinned Haiku one-shot.
- 7x holds only for P1 against Sonnet's 22 min (163/22.5), or for core-6 and full-6 on their own (8.35x and 7.05x).

**Cost [V]:**
- P1: 3.4–6.1x the Haiku one-shot ($0.95) and 1.4–2.6x the Sonnet one-shot.
- P2: no one-shot cost is recorded, so "2.5–6x" cannot be checked.
- The pinned baselines carry no cost at all.

**Root causes [V] on core-6. It is the slowest run: 261.8 min, of which E1 is 153.**
1. **The plan turned "the replayed hour" (spec line 66) into a 3600-second wall-clock run.**
   - The spec also says (line 56) that the replay runs faster than real time. The full replay lands in under 60 s (`final-review-t1.md` L5).
   - The plan's A-18 (transcript line 330) and P4's added data step "run the consumer directly for DURATION=3600" (transcript line 345) carried this into E1.
   - E1 ran it twice (lines 689 and 1077) and polled it in 9-minute sleeps (lines 900-1240). That is about 130 min.
   - **Responsible:** `commands/plan-create.md` and `plan-update.md`, which make no cost check on the commands a plan names, and P3 `plan-review.md`, which did not test this against spec line 56.
2. **61 minutes passed idle after the hard stop.**
   - The run sat in `ScheduleWakeup` "waiting on your reply" (lines 2515-2544). That is agent_wall minus active, 3695 s.
   - `SKILL.md:54` says a headless run has no user to ask, and nothing ends the session after `--hard-stop` (`SKILL.md:57-60`).
3. **Batch-wide, review loops and gate reruns ran without a limit:**
   - test-benchmark-pr had 20 repeat rounds and 149 peer min (postmortem line 74).
   - The R3 gate ran 12–22 times per run, and the R2 gate 3–14 times (my count of transcript Bash calls).
   - **Responsible:** the R2 floor in `skills/test-benchmark/SKILL.md:39-41` and `test_benchmark_gate.py:106-133`. Model-written scores under 7 force a re-score. The front matter says gates decide "never from text a model wrote".
   - Nothing in 2100c6e counts gate runs. #229 adds the caps **[L]**.
4. **E1 ran in the main thread** in 5 of 11 runs (no `/spec-driven` Agent call), as `SKILL.md:209` says: "The main agent runs E1". This conflicts with the Oct 25 owner rule **[V]**.

## Q4. "Consistency: core-6 is the best of 11"

**Verdict: true (4/7) [V], but it is an outlier, not a sign of consistency.**
- 7 of 11 runs score 0.
- core-6 is also the slowest and costliest run, and it is below both Oct 23 one-shots on the same grader.

**Root causes:**
1. **Stream fault handling decides the score.**
   - `stream_ok=false` voided 5 runs that had passed checks.
   - Commit `8fefa55` gives the mechanism: R1 cleared the consumer step on its exit code, and the agent's test fake sent the bad frame once and then intact **[V]** (the commit message; I did not open those transcripts).
   - **Responsible:** R1's walk rule (`review-rigor.md:24-26`) and E1's test-fake practice. #228 targets both.
2. **Gate stops do not track correctness.**
   - core-6 hard-stopped at R2 and scored best.
   - Three runs that reached R7 scored 0.
   - Two runs stopped at R5 because the plan named the wrong test file after P9 froze it (`SKILL.md:53`).
   - Three runs ended at E4 after 3 Stop-hook refusals.
   - Every run logs "FAIL no active cadence session" (postmortem Timeline) **[V]**. The cause is not checked **[I]**: the stop guard or `activate_session.py` loses the session id.

## Which blocks buy correctness

### Where the place-of-performance decision was made [V]

**In core-6, the decision was made in A5, the vibe-test block.**
- A5's gap G-11 ("the spec does not say which location counts") was answered by "A-11: the place is the place of performance" (core6.jsonl line 111, rewritten at line 164).
- P1 carried it into the plan as A-11, with a settling test, `test_county_state_source_reconcile` (line 232).
- E1 implemented it (DECISIONS.md, line 494).
- P3, P4 and R1 did not touch it.

**It does not separate core-6 from the zero-score runs.** I searched every Write and Edit in the 11 transcripts.
- All 11 runs chose place of performance. None chose recipient.
- 9 of the 11 made the choice in A5, as an A-n assumption, and P1 copied it:
  - P1: core-4 (line 82), core-5 (line 67), core-6, full-6 (line 59).
  - P2: core-4 (line 62), core-5 (line 72), core-6 (line 77), full-5 (line 118), full-6 (line 76).
- The other two:
  - **P1 full-4:** the P6 adversarial review raised the choice as open (line 330), and E1 settled it in DECISIONS (line 1391).
  - **P2 full-4:** E1 settled it in DECISIONS, "A-n not assigned" (line 1487).

**The one-shots that chose recipient still outscored core-6 on the same grader tree:**
- The Oct 23 Haiku one-shot (findings-haiku-A H2) scored 5/7.
- The Oct 23 Sonnet one-shot (findings-sonnet-B F2) scored 5/7.
- **[I]** So the geography choice is not what made core-6 4/7. The records hold only a passed count, not a per-check grade, so I cannot say which check it won. The likely deciders are stream_ok and the other stream checks: five runs lost their whole reward on stream_ok=false.

### Time and cost by block, core-6 (261.8 min, $5.75)

- **Minutes [V]:** from each Agent call to its result. They match postmortem lines 54-64.
- **Cost [I, estimated]:** reported_usd is split by each block's token weight from the per-message usage, using relative weights with the Haiku over-100K-token tier. This is not a price list, which is known to be wrong (log, Oct 24 23:55).

| Block | Min | Est. $ | What it changed | Group | Evidence |
|---|---|---|---|---|---|
| A5 vibe-test | 1.8 | 0.01 | Made the place-of-performance decision (A-11), the Amendment A gap list and others | **changed** answers, though every run made the same choice | line 111 [V] |
| P1 plan-create | 2.5 | 0.02 | Carried A-11 into the plan; wrote A-18, the "DURATION=3600" step | changed (carried) | line 232 [V] |
| P3 plan-review | 1.5 | 0.01 | MF-1 to MF-7 on the plan; effect on answers not traced | **neither** shown | line 298 [I] |
| P4 plan-update | 0.8 | 0.01 | Added the 3600-s data step, which cost about 130 min of E1 and changed no answer | **neither**; it was cost | line 345 [V] |
| E1 spec-driven | 152.9 | 4.23 | Wrote all the graded code and both HIGH defects. About 130 of its minutes were waits on two hour-long consumer runs | **changed** | lines 689, 1077, 900-1240 [V] |
| Deslop | 2.8 | 0.00 | Cleanup; no graded or defect change seen | neither [I] | line 1291 |
| E4 commit-push-pr | 1.0 | 0.01 | Local PR (auditability) | neither | line 1353 |
| R1 pr-review-local | 9.8 | 0.18 | 9 MF items, 7 N items | changed defects (see the fix round) | line 1570 [V] |
| Fix round (MF-1 to MF-9) | about 10 (20:54 to 21:04; its Agent call returns at once, so this time sits under orchestrator) | in orchestrator | MF-3 changed `dim_place` population (CT 2021 fallback). MF-1, -2 and -4 changed code but not graded output: the replay has no wrong-typed events (final-review M6), and the container is UTC (R1 MF-4). Per the log, it prevented 2 would-be findings | changed defects; changed a graded answer only through MF-3, if at all [I] | `git show` of acd9d90..35a2dcf [V] |
| R2 test-benchmark, 2 rounds, plus R2-F01 to F03 | 5.9 | 0.04 | Changed tests only. R2-F03 *added* `tests/test_rerun.py`, which is the reproduced defect L6 | changed a defect for the worse; no answer change | commit 75b8993 files [V] |
| R3 gate, 14 runs | in orchestrator | in orchestrator | mypy and ruff fixes (MF-6, MF-7, types) | neither | Bash count [V] |
| Orchestrator, main thread | 82.9 | 1.24 | Dispatch, gate runs, and the 61 min idle after the hard stop | neither | lines 2515-2544 [V] |

**Split for core-6:**
- Blocks that changed a graded answer or a reproduced defect (A5, P1, E1, R1 plus the fix round, R2) took about 183 min and $4.5. But about 130 of those minutes are E1 waiting on a run that changed nothing.
- The productive part is about 50 min.
- The rest, about 79 min (P3, P4, deslop, E4, R3 and orchestrator turns, including the 61 idle minutes), changed neither.

### Batch-wide, by block (11 runs) [V minutes, I cost]

| Block | Min | Est. $ | Runs | Group (from core-6) |
|---|---|---|---|---|
| Orchestrator main thread (includes E1 in the 5 runs with no `/spec-driven` call, plus R3 and all gate runs) | 594.0 | 20.62 | 11 | mixed: it holds E1 where E1 ran in the main thread |
| E1 /spec-driven | 379.6 | 12.94 | 6 | changed |
| R2 /test-benchmark | 155.4 | 1.38 | 10 | neither in core-6; 20 repeat rounds |
| R1 /pr-review-local | 105.2 | 1.24 | 11 | changed defects |
| Free-form fix and other prompts | 72.9 | 0.30 | 14 calls | changed defects (fix rounds) |
| P1 plan-create | 29.4 | 0.38 | 11 | carries A5's choices |
| A5 vibe-test | 21.8 | 0.17 | 11 | made the data-model choices |
| P3 plan-review | 18.1 | 0.17 | 11 | not shown |
| P4 plan-update | 18.1 | 0.17 | 11 | not shown; cost in core-6 |
| P6 de-adversarial | 7.8 | 0.09 | 5 | raised the geography choice in P1 full-4 |
| E4 commit-push-pr | 7.7 | 0.07 | 7 | auditability only |

**[I]** The blocks that decide correctness are A5, which makes the data-model choices, and E1, which writes the code. Together they take about 70 min of peer time per run, out of 128. Every other block took the rest without changing a graded answer in the one run I could trace end to end.
- I cannot prove this for the other ten runs. They have no outside review and no per-check grade. Dispatch item 8 asked for the per-check grade; its answer was reverted (2026-10-25, see README), so there is still none.

## Dispatch list (skill reviews)

Every brief: read only, no network requests, no agents or `claude -p`, scratch deleted at the end. Read the pinned skill with `git show 2100c6e:<path>` in `/home/user/cadence`.

| # | Skill path(s) | Question for the reviewer | Inputs | Output |
|---|---|---|---|---|
| 1 | `commands/pr-review-local.md`, `references/review-rigor.md` (R1) | For each of the 28 core-6 findings: was it in R1's reach under the rigor rules, and which rule line let it through? Do #228 and #229 close each gap? | R1 review = Write at core6.jsonl line 1570; `survive/run2/t1/final-review-t1.md`, `findings-t1-{A,B,C}.txt`; branches `fix/gate-asserts-output`, `fix/speed-slo` | `survive/skill-review-R1.md` |
| 2 | `SKILL.md` (Review phase, lines 228-240), `commands/pr-review-update.md` (fix round) | Did each of the 12 fix commits fix the class or only the named instance? What rule wording drives that? | `work/scratch/core6.git` commits 76ed6c8..998515a; the R1 MF list; final-review M6 and L2 | `survive/skill-review-fixround.md` |
| 3 | `skills/test-benchmark/SKILL.md`, `scripts/test_benchmark_gate.py` (R2) | Did R2 catch any of the 28? What did its floor cost in stops, re-scores and minutes across 11 runs? Is a model-written score a lawful gate input under the front matter? | `postmortems/2026-10-24-shapes-r2.md`; the 11 transcripts (`runs-store` via record.json); the core-6 R2 at core6.jsonl lines 2044 and 2402 | `survive/skill-review-R2.md` |
| 4 | `commands/plan-create.md`, `plan-review.md`, `plan-update.md` (P1/P3/P4) | How did "the replayed hour" become a 3600-s data step (lines 330, 345)? Why did P3 not test it against spec line 56? Why did the P2 full-5 and full-6 plans name test files that do not exist? | core6.jsonl lines 184-363; P2 full-5 and full-6 transcripts; `t1/PR-description.md` | `survive/skill-review-plan.md` |
| 5 | `commands/spec-driven.md`, `references/execution-protocol.md` (E1) | Where did E1's 336 peer minutes go? Does E1 require a fresh clone per entry point, a crash at stage boundaries, and empty and malformed input? Does #228's spec-driven change hold? | 6 runs with `/spec-driven` and 5 without; core6.jsonl lines 391-1287 | `survive/skill-review-E1.md` |
| 6 | `hooks/pipeline_stop_guard.py`, `scripts/activate_session.py` (A1/R7) | Why does every run log "no active cadence session"? Why did 3 runs end at E4 after 3 refusals? Why did core-6 idle 61 min after its hard stop? | record.json `stop_point` for all 11 runs; core6.jsonl lines 2480-2546 | `survive/skill-review-stopguard.md` |
| 8 | Not a skill: the harness grader output | For each of the 11 shapes-r2 runs and the two Oct 23 one-shots, which of checks 1 to 7 passed? For each check, which block's commit or artifact produced the answer, so the correctness split can be extended past core-6? | stored grader logs, if any, for these runs; `refs/graded` where present; the bundles; the per-block table in this file | `survive/check-attribution.md` (reverted 2026-10-25: its regrade source was deleted and it was never independently evaluated; see README) |
| 7 (low) | `skills/vibe-test/SKILL.md` (A5) | Do A5's assumptions reach the plan and change E1 (22 peer min across 11 runs)? | `.context/vibetest` Writes (core6.jsonl lines 111, 164); the plans | `survive/skill-review-A5.md` |

## For the pr-review-local agent

These notes are about `feat/antagonistic-review` @cc367f5, `skills/antagonistic-review/SKILL.md`.

1. **Items 5 and 8 conflict.** Item 5 says to fix the class; item 8 says one must-fix per fix commit, kept from `pr-review-local.md:40`. That wording produced the instance-only MF-1 fix (`acd9d90`, see M6). Make it one commit per class, with a parametrized test over the instances.
2. **Item 6's crash test must hit a stage boundary.** "A stop or a kill in the middle of a write" has to target the gap between stages (for example dlt normalize→load). `explain-t1.md:43` claims exactly-once under `kill -9`, while H2 reproduced the loss. A random kill proves nothing.
3. **H1 was reproduced against the rules.** The 403 came only from an external request the rules forbid (`final-review-t1.md:56-62`, log 02:50). Item 6 ("a live endpoint as well") invites this.
   - Check documented endpoint requirements without contacting the endpoint, or use a local stub.
   - In the eval set, mark H1 "reproduced locally only", so the eval does not reward breaking the rule.
4. **Use one head for the eval.** R1 reviewed 76ed6c8, before the fixes. The outside reviewers saw the final head. Score every candidate and both baselines on the same head, and do not use "flagged-and-fixed of 28" as a metric: it is 0 by construction.
5. **Keep item 3's selection proof.** "Show the test runner selects it" is the gap R1 actually had (check 7). Generalize it to every claimed pass: `dbt ls` / `pytest --collect-only`, plus the count quoted from captured output.
6. **Replace the adversarial-input list before any merge.** `review-rigor.md:30-33` is Cadence-specific, and the candidate still inherits it unchanged. The domain-neutral classes in item 6 should replace it.
7. **Keep severity apart from reproduction.** `review-rigor.md:6` ("can't reproduce, drop it") pushed R1's N-3 (the HIGH H1 silent exit) down to a nit. Keep `reproduced: no` and severity as separate fields, and tie severity to a quoted spec line.
8. **Label the one-shot trees in the eval set.** They were rebuilt from transcript replays (`findings-sonnet-A.txt:5-10`). Label them that way, and wait for the one-shot consolidations before comparing survivability.
