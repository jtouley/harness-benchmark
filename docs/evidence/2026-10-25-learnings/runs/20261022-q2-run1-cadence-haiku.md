RUN_BY_COMMAND: run-learnings
Run: 20261022-q2-run1-cadence-haiku
Cadence: fb0270d010cbfb284df5af992e1db36ed45cbeda
Packet sha256: a5f3bbe7dd23a56033c8757a8c0472657bd2ce991d902c8712c18f78b8238c16

# Learnings: 20261022-q2-run1-cadence-haiku

Each proposal is a candidate. This block changes no file but this document. A proposal changes a skill only after the revision-against-current eval on stored diffs shows no regression.

## Sources

- ledger: no
- record: yes
- repo: no
- transcript: yes

## Evidence counts

- finding: 9
- gate: 44
- orchestrator-runner: 1
- stop-refusal: 4

## Proposals

### L-1
- Target: SKILL.md
- Status: candidate
- Evidence: E-9, E-15, E-19, E-20
- Rule: gate-repeat
- Key: gate-repeat|cadence|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 4 times in orchestrator: fail plan-review-round round # waits on plan-review; fail plan-review-round round # has # must-fix; fail plan-review-round the plan has no.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-2
- Target: skills/test-benchmark/SKILL.md
- Status: candidate
- Evidence: E-11, E-12
- Rule: gate-repeat
- Key: gate-repeat|test-benchmark|plan-review-round
- Change: Before the return, run the `plan-review-round` gate once and fix every class it names in one pass. In this run it failed 2 times in test-benchmark: fail plan-review-round no open round names test-benchmark-plan; fail plan-review-round round # waits on plan-review.
- Eval: pending. python -m revieweval.compare layout --config old_skill=test-benchmark@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=test-benchmark@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-3
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-31, E-34
- Rule: gate-repeat
- Key: gate-repeat|spec-driven|cognitive-complexity
- Change: Before the return, run the `cognitive-complexity` gate once and fix every class it names in one pass. In this run it failed 2 times in spec-driven: fix step run r# without --check to; % duplicated # of # code lines; duplication.max_percent is # reuse the code that.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-4
- Target: SKILL.md
- Status: candidate
- Evidence: E-45
- Rule: orchestrator-runner
- Key: orchestrator-runner|cadence|runner
- Change: The orchestrator ran 1 project commands. It runs the manifest only; project commands run inside a block subagent or a gate.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-5
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-49, E-50, E-51, E-52, E-54
- Rule: review-finding
- Key: review-finding|spec-driven|core:implement
- Change: E1 checks `core:implement` before E4: the review found 5 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-6
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-53
- Rule: review-finding
- Key: review-finding|spec-driven|core:dry-extension
- Change: E1 checks `core:dry-extension` before E4: the review found 1 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-7
- Target: commands/spec-driven.md
- Status: candidate
- Evidence: E-56, E-57, E-58
- Rule: review-finding
- Key: review-finding|spec-driven|core:test-quality
- Change: E1 checks `core:test-quality` before E4: the review found 3 must-fix items of this rule in this run. Add the check to the TDD phase gate, stated without task detail.
- Eval: pending. python -m revieweval.compare layout --config old_skill=spec-driven@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=spec-driven@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-8
- Target: SKILL.md
- Status: candidate
- Evidence: E-8, E-24
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked lean peer return the final
- Change: The hooks refused 2 times with `blocked lean peer return the final`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

### L-9
- Target: SKILL.md
- Status: candidate
- Evidence: E-10, E-14
- Rule: stop-refusal
- Key: stop-refusal|cadence|blocked record each finding of your
- Change: The hooks refused 2 times with `blocked record each finding of your`. The orchestrator section names the next step for this refusal, so that the run does not repeat the refused call.
- Eval: pending. python -m revieweval.compare layout --config old_skill=cadence@fb0270d010cbfb284df5af992e1db36ed45cbeda --config new_skill=cadence@<revision> --baseline old_skill (harness-benchmark revieweval, PR #130)

## Evidence index

| Id | Kind | Block | Record |
|---|---|---|---|
| E-8 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 18 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-9 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-10 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-q/scripts/plan_wave.py" add --stage test-benchmark-plan --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-q/scripts/plan_wave.py" done --stage test-benchmar… |
| E-11 | gate | test-benchmark | FAIL plan-review-round: no open round names test-benchmark-plan for this plan: run plan_wave.py first |
| E-12 | gate | test-benchmark | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review, test-benchmark-plan |
| E-14 | stop-refusal | orchestrator | BLOCKED: record each finding of your report with plan_wave.py add: `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-q/scripts/plan_wave.py" add --stage plan-review --json '{...}'`, then `python3 "/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-q/scripts/plan_wave.py" done --stage plan-review` (referen… |
| E-15 | gate | orchestrator | FAIL plan-review-round: round 1 waits on plan-review, adversarial-review |
| E-19 | gate | orchestrator | FAIL plan-review-round: round 1 has 5 must-fix rows |
| E-20 | gate | orchestrator | FAIL plan-review-round: the plan has no `## Revision ledger (review 70a15a73801b)` row for B-1, B-2, C-1, C-2, MF-1 of round-1.md. Send /plan-update again |
| E-24 | stop-refusal | orchestrator | BLOCKED: lean peer return: the final message has 22 lines; a peer returns one line. Put the details in your artifact. Then end with one line only: ARTIFACT: <path>, or ARTIFACT: <path> VERDICT: <words>, or STOPPED: <reason>. |
| E-31 | gate | spec-driven | FAIL cognitive-complexity |
| E-34 | gate | spec-driven | FAIL cognitive-complexity |
| E-45 | orchestrator-runner | orchestrator | SKILL_ROOT="/tmp/claude-0/-home-user/412420db-14a2-5603-8fea-cbe5692ee926/scratchpad/e2e/cadence-plugin-q"; C="$SKILL_ROOT/scripts"; python3 -m pytest -q 2>&1 \| tail -4; echo "PYTEST=${PIPESTATUS[0]}"; python3 "$C/architecture_review.py" --phase impl 2>&1 \| tail -4; echo "E3=${PIPESTATUS[0]}"; git status --short \| head; git diff --stat 583eb69..HEAD \| tail -3 |
| E-49 | finding | pr-review-local | --out equal to the ledger path overwrites the ledger. Repro: budgetcli --file l.json export --out l.json exits 0, prints wrote 2 rows to l.json, and l.json now holds the CSV text. The ledger data is lost. Fix: refuse an --out that resolves to the ledger path with an error line and exit 2, before any write. |
| E-50 | finding | pr-review-local | Closed output pipe prints a traceback. Repro: budgetcli --file l.json export \| head -0 ends with BrokenPipeError in sys.stdout.buffer.write and exit status 1. Fix: catch BrokenPipeError on the stdout write and exit without a traceback. |
| E-51 | finding | pr-review-local | Text that does not encode gives a traceback. Repro: a ledger note holding a lone surrogate (U+D800) makes export fail with UnicodeEncodeError on the encode in render_csv, for stdout and for --out, exit 1. Fix: an error line and exit 2 for an unencodable note, no traceback. |
| E-52 | finding | pr-review-local | A bad row in the stored ledger gives a traceback in export. Repros: a row without amount_cents gives KeyError; a row with day 2026-13-01 gives ValueError; a file with byte 0xff gives UnicodeDecodeError. All exit 1. Ledger.load is shared with add and totals, so the fix belongs in load: raise a ValueError with a message, and have cli print an error line and exit 2. |
| E-53 | finding | pr-review-local | Each of the five new acceptance scripts defines the same cli() helper, ENV and ROOT. This is a new helper that copies an existing one. Fix: one shared acceptance helper module. The five checks are pinned by P9, so the move needs a repin row in .context/acceptance/feat-local-4-csv-export.repair.jsonl, or the author records why the copies stay. |
| E-54 | finding | test-benchmark | Text that does not encode gives a traceback. Repro: a ledger note holding a lone surrogate (U+D800) makes export fail with UnicodeEncodeError on the encode in render_csv, for stdout and for --out, exit 1. Fix: an error line and exit 2 for an unencodable note, no traceback. |
| E-56 | finding | test-benchmark | No test covers --out set to the ledger path. Input: export --out <ledger>. Observed: exit 0 and the ledger is replaced by CSV text. Expected: error line, exit 2, ledger unchanged. The suite passes 27 of 27 with the defect present. Cross-reference: ledger MF-1. |
| E-57 | finding | test-benchmark | No test covers a stored row without amount_cents (KeyError, exit 1) or a note with a lone surrogate (UnicodeEncodeError, exit 1). Expected: error line, exit 2, no traceback. Cross-reference: ledger MF-3, MF-4. |
| E-58 | finding | test-benchmark | No test covers a closed stdout pipe (export \| head -0). Observed: BrokenPipeError traceback, exit 1. Expected: no traceback. Cross-reference: ledger MF-2. |
