# Skill review 6: stop guard and activate_session (A1/R7)

Date: 2026-10-25. Read only; no network; no agents. Tags: **[V]** checked with my own tool calls, **[I]** inferred.
Pinned Cadence 2100c6e (`/home/user/work/cadence-learn`); #228 = `fix/gate-asserts-output` @9314a61; #229 = `fix/speed-slo` @4d36756; #231 = `fix/enforcement-gate` @4c437ca (the doc's log row, rev 315). Harness: `/home/user/work/hb-audit` @25dd565.
Front-matter lines applied: "Cadence does not stop or ask"; "a gate that still fails after its one allowed fix round is a hard stop for that block; the orchestrator records it and moves on"; "Enforcement ... decided by code".

## Answers

| Question | Answer | Whose defect |
|---|---|---|
| Why does every run log "FAIL  no active cadence session"? | It is the harness's probe, not the run. `host_trial.stop_point` copies `repo-as-left` to a temp dir and runs `headless.py next` there. Cadence keys a session by `sha256(git toplevel)[:16]` (`shared/scripts/session_store.py:48-59`), so the copy has no session: A1's gate (`activate_session.py --check`, `activate_session.py:398`) fails, and its line is appended as `why` to every reason (`host_trial.py:302-331`). Reproduced: activate in a repo → `--check` OK; `cp -a` → `--check` "FAIL  no active cadence session", exit 1 [V]. | harness |
| Why did 3 runs end at E4 after 3 refusals? | E4 was never open. In the stop guard's read-only walk (4 s per gate, 9 s total, `pipeline_stop_guard.py:80-81`), E4 ran `clean_checkout.record_finding`: a clone plus the build. It timed out. `find_open_block` then returns the hung row with `unknown=True` (`:198-201`), and `_continue_text` says "next E4 (draft-pr) via `/commit-push-pr --draft`" [V; #228 commit 5903fa1 gives the same cause for P2 core-4]. After `MAX_REFUSALS=3`, `decide` returns `escalate`, and `_guard` allows the stop with "escalate to user". It records nothing, so the session stays open (`:1073-1075`) [V]. | Cadence stop guard, plus each agent's choice to stop |
| Why did core-6 idle 61 min after its hard stop? | At 18:04 (A5) the orchestrator called `ScheduleWakeup` to wait on a peer (core6.jsonl line 143). That put the session in dynamic-loop mode. After `--hard-stop retries` (line 2498) and end_turn, the stale wakeup fired (line 2506). The agent then armed two more 1800 s wakeups "waiting on your reply" (lines 2514, 2524) and stopped the loop at 22:23 (line 2542). That is 21:21 to 22:23 [V]. Nothing in 2100c6e denies a wait, and nothing says to run R7 after a hard stop. `SKILL.md:58-60` only records the stop. | Cadence (no rule), already mostly closed by #229 |

### The three E4 runs: what was really open [V]

| Run | Guard's refusals (transcript line) | Real state | Why the agent stopped |
|---|---|---|---|
| P2 core-4 | 1558, 1578, 1618 (all "Progress unknown"); escalate at 1623 | R5 closure: must-fix MF-5 could not be closed. The deferral needs an adjudicated P8 register (1536-1538), and core does not run P8. `headless next` said R5 (1567). The agent timed `draft_pr_gate --check` at 0.06 s (1597). | "MF-5 needs ... a person. I ... leave the run open for that decision" (1551). This breaks "no stop or ask". |
| P1 core-5 | 1230 and 1243 at 18:33, during E1 (known, slug draft-pr); 1990 at 19:59 (unknown); escalate at 2006 | R2/R5: must-fix spec-F01 and others were open (1984). | "I've stopped the run at R2 because it can't close honestly" (1989). It recorded no hard stop. The two refusals at 18:33 carried over 86 minutes because `stop_refusal_slug` stayed `draft-pr`. So the first refusal in the R phase was already the third, and it escalated. |
| P1 full-6 | 3414, 3466, 3486 (unknown); escalate at 3496 and later | **It finished.** R5 passed 21/21 and 7/7 (3576), and `--deactivate` succeeded at 21:22:48 (3605). The harness still recorded `E4`, because `choose_stop` puts any transcript refusal ahead of a closed session (`host_trial.py:291-292`). It also waited about 23 min more on wakeups after the close (3625). | Misclassified by the harness. |

### What the open PRs already fix

- **#228 (5903fa1):** E4's clean-checkout build no longer runs in the read-only walk. That fixes this instance only. Any gate that runs longer than 4 s in the walk will still be named "open" with its command [V].
- **#229 (`hooks/guard_supervisor.py`, `mode: enforce`):** denies `ScheduleWakeup` and `CronCreate` during a run. After a deactivation or a hard stop, `pre_closed` denies waits and new blocks and says "end the turn" [V]. This would have prevented both the 18:04 wakeup and the 61 min. It also adds block-level stops (`block_stops`), so the run can move on, as the front matter asks. #229 does **not** change the stop guard's escalate path, the unknown text, or SKILL.md's hard-stop steps [V].
- **#231:** none of these files. The diff touches only `SKILL.md:211`, `hooks.json` and `guard_context_budget.py` [V].

## Proposed changes

### A. Cadence, as a diff against the #231 head (4c437ca)

1. **The escalate path records a `retries` hard stop and says nothing about the user.** The session ends recorded instead of staying open. The guard already does the same for a refused peer return (`_record_hard_stop`, `:823-831`).
2. **"Progress unknown" names the gate that timed out, but no longer gives its command.** It sends the agent to `headless.py next --json`. This fixes the class that #228 fixed only for E4.
3. **Refusals during a timed-out walk count under `unknown:<slug>`.** Known-block refusals from earlier in the run no longer carry over (P1 core-5).
4. **New SKILL.md Self-healing lines:** after a hard stop, run R7 in the same turn and end the turn, with no wait. A must-fix that the run shape cannot close is `retries` at that block, never "left open for a person". When #229 lands, its `block_stops` should carry this per block, so R3/R5/R7 still run.
5. **Updated:** the `error-recovery.md` rows, the two tests, and the exclude-list hashes.

**Verified:** `tests/hooks`, `tests/contract` and `tests/install` pass on a scratch worktree [V]. Ruff reports one new UP017; the file already has two of the same. Full `ci_local` was not run.

```diff
diff --git a/SKILL.md b/SKILL.md
index 1d272f0..fe8ab51 100644
--- a/SKILL.md
+++ b/SKILL.md
@@ -58,6 +58,10 @@ Stop only for destructive risk, missing credentials with no fallback, a security
 Record each one with `activate_session.py --hard-stop {destructive,credentials,security,retries,not-needed,context} --reason "..."`.
 `not-needed` is the no-PR end (see "A Cadence run always ends in a PR"). An ops-only handoff stops at **A3**.
 `--deactivate` refuses an open run that has no hard stop.
+After a hard stop, run R7 (`activate_session.py --deactivate`) in the same turn, write the session summary, and end the turn.
+Do not schedule a wakeup, start a loop, or wait for a reply. A headless run has no user, and nothing runs after a hard stop.
+A must-fix that the run shape gives no way to close (a deferral needs P8's register, which core does not run) is `retries` at that block.
+Record it and run R7. Never leave the run open for a person to decide.
 A peer can set a hard stop by mistake, for example a user-level copy of a peer with an old rule (a peer shadow).
 To clear it: Remove the cause, and run `scripts/preflight.py` until it passes. Start a new host session. Then run `activate_session.py --from-branch --resume`.
 Fix each review finding with `/spec-driven`, or open a ticket under the parent issue. Do not leave a must-fix finding without an owner.
diff --git a/hooks/pipeline_stop_guard.py b/hooks/pipeline_stop_guard.py
index 677cdb6..2c1a543 100755
--- a/hooks/pipeline_stop_guard.py
+++ b/hooks/pipeline_stop_guard.py
@@ -30,6 +30,7 @@ import json
 import os
 import re
 import sys
+from datetime import datetime, timezone
 from pathlib import Path
 
 SKILL_ROOT = Path(
@@ -316,7 +317,7 @@ def _cmd(row: dict) -> str:
 def _with_budget(session: dict, phase: str, cont: str) -> tuple[str, str]:
     refusals = int(session.get("stop_refusals") or 0)
     if refusals >= MAX_REFUSALS:
-        return "escalate", f"stop refused {refusals} times — escalate to user. {cont}"
+        return "escalate", f"stop refused {refusals} times; a retries hard stop is recorded. {cont}"
     return "block", f"BLOCKED early stop in {phase}. {cont}"
 
 
@@ -350,7 +351,11 @@ def _continue_text(row: dict, session: dict, unknown: bool) -> str:
     if row.get("detail"):
         cont = f"{cont}: {row['detail']}."
     if unknown:
-        cont = f"Progress unknown{_run_note(session)}: a gate timed out or could not run. {cont}"
+        # A gate that timed out in the 4 s walk is not an open block. Naming its command sent three
+        # shapes-r2 runs back to a finished E4 (20261024-P2-cadence-haiku-core-4, -P1-...-core-5, -P1-...-full-6).
+        return (f"Progress unknown{_run_note(session)}: the {row.get('block')} ({row.get('slug')}) gate timed out "
+                f"in the stop guard's walk, which does not show that it is open. Run "
+                f"`python3 {SKILL_ROOT / 'scripts' / 'headless.py'} next --json` and continue at the block it names")
     return cont
 
 
@@ -400,7 +405,7 @@ def decide(
     refusals = int(session.get("stop_refusals") or 0)
     cont = _continue_text(nxt, session, unknown)
     if refusals >= MAX_REFUSALS:
-        return "escalate", f"stop refused {refusals} times — escalate to user. {cont}"
+        return "escalate", f"stop refused {refusals} times; a retries hard stop is recorded. {cont}"
     return "block", f"BLOCKED early stop in {phase}. {cont}"
 
 
@@ -431,6 +436,28 @@ def apply_refusal(
     return session
 
 
+def record_guard_stop(
+    context_dir: Path, session: dict, slug: str, message: str, *, data_path: Path | None = None
+) -> None:
+    """The refusal budget is spent: record a hard stop `retries`, so the run ends recorded, not open.
+
+    Front matter: Cadence does not stop or ask; a block that cannot pass is recorded and the run moves on.
+    Before this, the fourth stop was allowed with "escalate to user" and the session stayed active, so R7
+    never ran and the harness read the last block the guard named (three shapes-r2 runs read as E4).
+    """
+    if session.get("hard_stop"):
+        return
+    session = {**session, "hard_stop": {
+        "class": "retries",
+        "reason": f"stop guard: {message}"[:300],
+        "block": slug,
+        "by": "pipeline_stop_guard",
+        "at": datetime.now(timezone.utc).isoformat(),
+    }}
+    target = data_path or session_data_path(context_dir)
+    target.write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
+
+
 SUBAGENT_EVENTS = frozenset({"SubagentStop", "subagentStop"})
 
 
@@ -1009,6 +1036,8 @@ def _judge_one(session: dict | None, context_dir: Path, workspace: Path, *, corr
     # agent made progress, so the count starts again (cd-12-F3). Without a recorded block
     # (older sessions) the count applies as before.
     here = str((open_block or {}).get("slug") or (session or {}).get("resume_slug") or "")
+    if unknown:
+        here = f"unknown:{here}"  # refusals on a known block do not carry over to a walk that timed out
     if session and session.get("stop_refusal_slug") not in (None, here):
         session = {**session, "stop_refusals": 0}
     # cd-76 R2-D5c: every evidence read uses the judged run.
@@ -1071,6 +1100,8 @@ def _guard(host: str, *, subagent: bool, repeat: bool, payload: dict | None = No
     if decision == "allow":
         stop_allow(host)
     elif decision == "escalate":
+        if judged and not corrupt and not subagent:
+            record_guard_stop(judged_ctx, judged, here, message, data_path=judged_path)
         stop_allow(host, notice=f"Cadence: {message}")
     else:
         # Subagent stops are pushed back once but never spend the run's budget (ADR-0002).
diff --git a/references/error-recovery.md b/references/error-recovery.md
index 751d93d..4cb9409 100644
--- a/references/error-recovery.md
+++ b/references/error-recovery.md
@@ -202,8 +202,8 @@ A slash command goes to the block's peer through the Agent tool, as the lean pro
 | Evidence | `BLOCKED: this command sets the time of a commit` | `git commit --date`, `-C`, `-c`, `GIT_AUTHOR_DATE`, `GIT_COMMITTER_DATE` or faketime during a run (ADR-0023) | `git commit -m 'phase N: <subject>'` with no date option |
 | Evidence | `BLOCKED: this command writes two or more commits in one shell call` | A list, a loop, xargs or `rebase -x` of `git commit` during a run (ADR-0023) | Do one phase, then `git add <files> && git commit -m 'phase N: <subject>'` in its own shell call |
 | Stop | `BLOCKED early stop in <phase>. Continue paceline: next <block> (<slug>) via <command>` | The run has an open block | Run `<command>` |
-| Stop | `Progress unknown: a gate timed out or could not run` | A gate did not end in time | `python3 "$C/headless.py" next --json` |
-| Stop | `stop refused N times — escalate to user` | Three held stops at one block | Tell the user what blocks the run. Do not stop in silence |
+| Stop | `stop refused N times; a retries hard stop is recorded` | Three held stops at one block | The guard recorded the stop. Run R7 (`activate_session.py --deactivate`) and end the turn. Do not ask or wait: a headless run has no user |
+| Stop | `Progress unknown: the <block> (<slug>) gate timed out in the stop guard's walk` | A gate ran past 4 s in the read-only walk | Not an open block. Run `python3 "$C/headless.py" next --json` and continue at the block it names. Do not run the named block again |
 | Stop | `FAIL-CLOSED: corrupt session during execution/review` | The session file is not readable | `python3 "$C/activate_session.py" --from-branch --resume` |
 | Stop | `BLOCKED: lean peer return: <reason>` | The peer's last message is not one line | End with `ARTIFACT: <path> VERDICT: <verdict>` (`references/peer-contract.md`) |
 | Stop | `BLOCKED: peer return: the artifact <path> is not the artifact of <block>` | The peer wrote its file at another path | Write the file at the path on the `Writes:` line of the packet. Return that path |
diff --git a/tests/hooks/test_hooks_speak_each_host_protocol.py b/tests/hooks/test_hooks_speak_each_host_protocol.py
index 4392db3..e91459e 100644
--- a/tests/hooks/test_hooks_speak_each_host_protocol.py
+++ b/tests/hooks/test_hooks_speak_each_host_protocol.py
@@ -82,7 +82,7 @@ def test_stop_guard_escalation_lets_the_stop_through(tmp_path, host, run_hook):
     data = json.loads(out) if out else {}
     assert "followup_message" not in data and data.get("decision") != "block"
     if host == "claude":
-        assert "escalate to user" in data["systemMessage"]
+        assert "a retries hard stop is recorded" in data["systemMessage"]
 
 
 def test_stop_guard_counts_refusals(tmp_path, run_hook):
diff --git a/tests/hooks/test_stop_guard.py b/tests/hooks/test_stop_guard.py
index 5d27fd1..1f8b343 100644
--- a/tests/hooks/test_stop_guard.py
+++ b/tests/hooks/test_stop_guard.py
@@ -155,6 +155,24 @@ def test_main_budget_still_escalates_after_three(tmp_path, run_hook, layout):
     assert decisions == ["block", "block", "block", "allow"]
 
 
+def test_a_spent_budget_records_a_hard_stop(tmp_path, run_hook):
+    """The fourth stop ends the run recorded: no ask, no open session (shapes-r2: three runs read as E4)."""
+    repo = git_repo(tmp_path)
+    hook_session(repo, "single", resume_slug="implement", stop_refusals=3)
+    _, out, _ = run_hook(GUARD, repo, MAIN["claude"], "claude")
+    assert stop_decision("claude", out) == "allow"
+    stop = read_session(repo)["hard_stop"]
+    assert stop["class"] == "retries" and stop["by"] == "pipeline_stop_guard"
+    assert "escalate to user" not in json.loads(out)["systemMessage"]
+
+
+def test_a_timed_out_gate_is_not_named_as_the_next_command():
+    """A gate that ran past 4 s in the walk sends the agent to headless, not back to that block's command."""
+    row = {"block": "E4", "slug": "draft-pr", "phase": "execution", "command": "/commit-push-pr --draft"}
+    text = guard._continue_text(row, {"pipeline_run_id": "r1"}, True)
+    assert "/commit-push-pr" not in text and "headless.py" in text and "E4 (draft-pr) gate timed out" in text
+
+
 @pytest.mark.parametrize("corruption", ["dangling_ref", "truncated"])
 def test_corrupt_session_blocks_once_then_escalates_on_claude(tmp_path, run_hook, corruption):
     repo = git_repo(tmp_path)
diff --git a/tests/install/test_phase6_exclude_list_hashes_unchanged.py b/tests/install/test_phase6_exclude_list_hashes_unchanged.py
index 1413d51..c2e297b 100644
--- a/tests/install/test_phase6_exclude_list_hashes_unchanged.py
+++ b/tests/install/test_phase6_exclude_list_hashes_unchanged.py
@@ -133,7 +133,8 @@ EXCLUDE_SHA256 = {
     # ADR-0028: one plan review, one code review; the run's own blocks; no cwd fallback in load_stages; A5 core
     # A5 never stops the run: the third A5 artifact hold goes through, no retries stop
     # owner-rules audit: no stop or ask, one plan review, the third hold closes a block whose gate passes
-    "hooks/pipeline_stop_guard.py": "71065054f5d87cb834f24764101bb20df6337dc061076c12e394cd63ebabe93c",
+    # shapes-r2 stop-guard review: a spent refusal budget records a hard stop; a timed-out gate is not named open
+    "hooks/pipeline_stop_guard.py": "86f1f1d3d48e73a6033c88c3095512ed63297dec6f4152451588bea51eb93f6b",
     # Lean Task prompt owns the Cursor Task matcher. Handoff does not register a second one.
     # harness-benchmark S09: guard_secret_read.py on preToolUse Read, beforeReadFile and beforeShellExecution
     "hooks/hooks-cursor.json": "60c449f48447ff0ffad4c0eabc341a547b1c95002a66df1d74b8906d6be253c0",
@@ -185,7 +186,8 @@ EXCLUDE_SHA256 = {
     # A5 never rejects the spec (the owner's sentence)
     # owner-rules audit: no stop or ask, one plan review, the third hold closes a block whose gate passes
     # gh-96 enforced: the /spec-driven peer runs E1; the orchestrator only dispatches
-    "SKILL.md": "68495a8ce66030bebd9037ce34a511620be1d04f13456d54983d005d9453afaa",
+    # shapes-r2 stop-guard review: after a hard stop, R7 in the same turn; no wait for a reply
+    "SKILL.md": "e996dd563d6b3af4c412dc5b03ebede2764bdeeb1dac08f1ebfd78428ca08bfd",
     # #16: protected_writer and the shell backstop also protect .context/handoff
     # gh-35: peer verdicts attested by the subagent write hook (Claude Code)
     # gh-35 R1: hash attestation by target repo; bounded loop and score contract
```

### B. Harness (`harness-benchmark`, scripts/host_trial.py @25dd565)

1. **`rebind_sessions(copy)`:** writes the copy's own by-worktree session before the probe runs. A1 then passes in the copy, and the reason is the real failing gate. Verified: `--check` gives OK in the copy after the rebind [V].
2. **`choose_stop`:** a closed session (no hard stop) wins over a refusal that has a timestamp earlier than `completed_at`. P1 full-6 then reads R7, not E4. Refusal lines without timestamps behave as before, so the existing tests keep passing.
3. **Re-derive the stop points:** run `run_one --finish` / `--stop-only` on the 11 shapes-r2 runs after the fix.

**Verified:** `tests/test_host_trial.py` gives 33 passed. The same 3 tests fail before and after the change, because they need the checkout's own path [V].

```diff
--- a/scripts/host_trial.py	2026-10-25 03:42:22.197524741 +0000
+++ b/scripts/host_trial.py	2026-10-25 03:42:22.247107099 +0000
@@ -248,6 +248,7 @@
 
 
 _OPEN_BLOCK = re.compile(r"Continue paceline: next ([AEPR]\d+) \(([\w-]+)\)")
+_STAMP = re.compile(r'"timestamp": ?"([^"]+)"')
 _REFUSED = re.compile(r"stop refused (\d+) times")
 
 
@@ -258,7 +259,8 @@
     found = None
     for line in lines:
         for block, slug in _OPEN_BLOCK.findall(line):
-            found = {"block": block, "slug": slug, "refused": None}
+            stamp = _STAMP.search(line)
+            found = {"block": block, "slug": slug, "refused": None, "at": stamp.group(1) if stamp else None}
         refused = _REFUSED.findall(line)
         if refused and found is not None:
             found["refused"] = int(refused[-1])
@@ -289,7 +291,9 @@
         return {"block": None, "reason": None}
     if hard:
         return {"block": stop_block(headless_block, hard), "reason": why[:300] or None}
-    if closed is not None and opened is None:
+    if closed is not None and (opened is None or _before(opened.get("at"), closed)):
+        # --deactivate closes a run only after R6 passed (no hard stop here), so a refusal before the close is
+        # history, not the stop: 20261024-P1-cadence-haiku-full-6 closed at 21:22 after refusals at a stale E4.
         return {"block": "R7", "reason": f"done: the session closed at R7 (session-close) at {closed}, with no "
                                           f"Stop-hook refusal ({why})"[:300]}
     if opened is not None:
@@ -299,12 +303,43 @@
     return {"block": headless_block, "reason": why[:300] or None}
 
 
+def _before(at: str | None, closed: str) -> bool:
+    """True when the refusal time `at` is known and earlier than the close time."""
+    from datetime import datetime
+    try:
+        return at is not None and datetime.fromisoformat(at.replace("Z", "+00:00")) < \
+            datetime.fromisoformat(closed.replace("Z", "+00:00"))
+    except ValueError:
+        return False
+
+
+def rebind_sessions(copy: Path) -> None:
+    """Give the copy its own worktree session. Cadence keys a session by sha256 of the git toplevel, so in a copy
+    activate_session.py --check found none: A1 failed and every stop reason of shapes-r2 ended in
+    "(FAIL  no active cadence session)", whatever the real open gate was."""
+    import hashlib
+    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=copy, capture_output=True, text=True)
+    root = Path(top.stdout.strip() if top.returncode == 0 and top.stdout.strip() else copy).resolve()
+    key = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:16]
+    folder = copy / ".context" / "sessions" / "by-worktree"
+    for path in sorted(folder.glob("*.json")):
+        try:
+            data = json.loads(path.read_text(encoding="utf-8"))
+        except (OSError, ValueError):
+            continue
+        if isinstance(data, dict) and "ref" not in data and data.get("status") != "completed":
+            (folder / f"{key}.json").write_text(json.dumps({**data, "workspace": str(root)}, indent=2) + "\n",
+                                                encoding="utf-8")
+            return
+
+
 def stop_point(repo: Path, plugin: Path, env: dict[str, str], transcript: list[str] = ()) -> dict:
     """The block the run stopped at, and why: from Cadence's headless runner in a copy of the repository, the
     session's hard stop and the transcript's last open block (choose_stop)."""
     with tempfile.TemporaryDirectory() as tmp:
         copy = Path(tmp) / "repo"
         shutil.copytree(repo, copy, symlinks=True)
+        rebind_sessions(copy)
         proc = subprocess.run([sys.executable, str(plugin / "scripts" / "headless.py"), "next", "--json"], cwd=copy,
                               env=env, capture_output=True, text=True, timeout=900)
         hard = None
--- a/tests/test_host_trial.py	2026-10-25 03:42:22.199961667 +0000
+++ b/tests/test_host_trial.py	2026-10-25 03:42:59.301368114 +0000
@@ -159,8 +159,8 @@
 
 
 def test_the_open_block_is_the_last_one_the_stop_hook_named():
-    assert host_trial.open_block(CORE_1_TAIL) == {"block": "R5", "slug": "closure", "refused": 3}
-    assert host_trial.open_block(CORE_1_TAIL[:1]) == {"block": "R2", "slug": "test-benchmark-pr", "refused": None}
+    assert host_trial.open_block(CORE_1_TAIL) == {"block": "R5", "slug": "closure", "refused": 3, "at": None}
+    assert host_trial.open_block(CORE_1_TAIL[:1]) == {"block": "R2", "slug": "test-benchmark-pr", "refused": None, "at": None}
     assert host_trial.open_block(['{"type": "result"}']) is None
 
 
@@ -330,3 +330,25 @@
     report = json.loads((out / "jail-check.json").read_text())
     assert report["visible"] == [] and report["agent_exit"] == 0 and report["agent_reply"] == "OK"
     assert str(spec) in report["kept"] and str(plugin) in report["kept"]
+
+
+def test_a_close_after_the_last_refusal_is_done():
+    """20261024-P1-cadence-haiku-full-6: refusals at a stale E4 at 20:40, then R7 closed the session at 21:22."""
+    tail = ['{"type": "user", "timestamp": "2026-10-24T20:40:15.000Z", "message": {"content": [{"type": "text", '
+            '"text": "Stop hook feedback: BLOCKED early stop in execution. Continue paceline: next E4 (draft-pr) via x"}]}}']
+    stop = host_trial.choose_stop("A1", None, host_trial.open_block(tail), "", closed="2026-10-24T21:22:48+00:00")
+    assert stop["block"] == "R7"
+    stop = host_trial.choose_stop("A1", None, host_trial.open_block(tail), "", closed="2026-10-24T20:00:00+00:00")
+    assert stop["block"] == "E4"
+
+
+def test_the_copy_gets_its_own_worktree_session(tmp_path):
+    repo = tmp_path / "copy"
+    repo.mkdir()
+    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
+    _session(repo, active_skill="cadence", status="active", workspace="/elsewhere/repo")
+    host_trial.rebind_sessions(repo)
+    import hashlib
+    key = hashlib.sha256(str(repo.resolve()).encode("utf-8")).hexdigest()[:16]
+    data = json.loads((repo / ".context" / "sessions" / "by-worktree" / f"{key}.json").read_text())
+    assert data["active_skill"] == "cadence" and data["workspace"] == str(repo.resolve())
```

## Still open [I]

- **The walk could read gate verdicts from the run state.** The guard re-runs gates inside a 15 s hook. The front matter says "gates run once on a block's output; their verdict goes into the run state". A guard that reads those verdicts would remove the timeout class completely. That is larger than this diff.
- **Recording a stop is not moving on.** Change A1 ends the run recorded, and the front matter wants the run to move on. That needs #229's `block_stops` merged with this change; the stack merge should combine them.
