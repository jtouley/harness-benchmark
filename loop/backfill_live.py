"""Records of the live Cadence runs of 21 and 22 October 2026, from the evidence branches of jtouley/cadence.

    python -m loop.backfill_live --cadence ../cadence [--runs runs]    # writes the records that are not there yet

The sessions that made these runs also graded them: with a probe script of their own, or from the
run's own gate records. No outside grader scored any of them, and the driver did not exist yet. So
every record here has `counts.counts` false, with `counts.why` set to WHY, and no run has a
scores.jsonl. The scoreboard does not show them. They are kept so that the runs exist as records,
with the harness commit, the model, the task, the time, the session's own claim and a pointer to the
evidence.

Every field comes from a file at a pinned commit of jtouley/cadence (EVIDENCE), read from the
`--cadence` checkout. Nothing is copied from those branches: no transcript, plan or code. A record
points at the evidence by commit and path, and the transcript and tree blobs name the files there
by sha256.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from loop import record, store
from loop.driver import transcript_facts

ROOT = Path(__file__).resolve().parents[1]
CADENCE_REPO = "jtouley/cadence"
# Evidence commits: branch evidence/7058c2b0 (51 e2e runs of one session) and evidence/08495c94 (the
# three Haiku arms of another). The two other evidence branches of that day (evidence/c467ba5e at
# 13a639a, evidence/17c78ed4 at d24f709) hold test-suite runs and hook cases, not live Cadence runs.
E2E = "9008b0e2389021aa499aa39798a852d9f444af11"
ARMS = "9954da6405804dc7eabd9e5433c2bb3ac8779265"
WHY = "self-graded, no outside grader, pre-driver"
BATCH_E2E = "2026-10-21-cadence-e2e-budgetcli"
BATCH_ARMS = "2026-10-21-cadence-arms-budgetcli"
# requests.md numbers its request texts. A request is a task's golden input (golden/cadence/<task>.md),
# or a resume of an earlier request, or the recurring-expenses ticket LOCAL-3, which has no golden input.
TASK_OF_REQUEST = {1: "LOCAL-3", 3: "d1", 4: "d2"}
RESUME_OF_REQUEST = {2: 1, 5: 1, 6: 1, 7: 3, 8: 4, 9: 3}
TICKET = {"LOCAL-3": "LOCAL-3", "d1": "LOCAL-4", "d2": "LOCAL-4", "d3": "LOCAL-4", "d4": "LOCAL-4"}
# The arms of evidence/08495c94: stop point and the session's own classification (its README, claim 4).
ARM_RUNS = {
    "arm-a": ("P3", "retries hard stop at P3: round 2 said REQUEST CHANGES and the gate did not read it; no code",
              "stopped at P3 with no code (the session's own reading of the gate records and the final message)"),
    "arm-b-try1": (None, "stopped before code: the orchestrator ran the next step before P3 and wrote the P9 marker "
                   "out of order", "not one of the compared arms; stopped before code (the session's own reading)"),
    "arm-b": ("R5", "stopped at R5: three findings stayed fixed, not verified", "code and a draft PR; 13 of 17 probes "
              "pass by the session's own probe (claim3/probes-arm-b.txt); did not reach R7"),
    "arm-c": ("R4", "hard stop at R4: a scorecard finding stayed open", "code and a draft PR; the same 13 of 17 probes "
              "pass by the session's own probe (claim3/probes-arm-c.txt); did not reach R6 or R7"),
}
ARM_PROMPT = {"arm-a": "prompt.txt", "arm-b-try1": "prompt.txt", "arm-b": "prompt-b.txt", "arm-c": "prompt.txt"}
MODEL_ALIAS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}


# --- reading the evidence ------------------------------------------------------------------------------


def _git(cadence: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cadence), *args], capture_output=True)


def available(cadence: Path) -> bool:
    return cadence.is_dir() and all(_git(cadence, "cat-file", "-e", f"{c}^{{commit}}").returncode == 0 for c in (E2E, ARMS))


def _show(cadence: Path, commit: str, path: str) -> bytes | None:
    proc = _git(cadence, "show", f"{commit}:{path}")
    return proc.stdout if proc.returncode == 0 else None


def _text(cadence: Path, commit: str, path: str) -> str | None:
    data = _show(cadence, commit, path)
    return data.decode("utf-8", "replace") if data is not None else None


def _ls(cadence: Path, commit: str, path: str) -> list[str]:
    proc = _git(cadence, "ls-tree", "--name-only", f"{commit}:{path}")
    return proc.stdout.decode().split() if proc.returncode == 0 else []


def _full_sha(cadence: Path, short: str) -> str:
    proc = _git(cadence, "rev-parse", "--verify", f"{short}^{{commit}}")
    return proc.stdout.decode().strip() if proc.returncode == 0 else short


def _blob(cadence: Path, commit: str, path: str, gzipped: bool) -> dict:
    """A blob entry for a file kept in the evidence commit: the sha256 of the original bytes."""
    data = _show(cadence, commit, path)
    if data is None:
        return store.missing(f"not in {CADENCE_REPO}@{commit[:7]}:{path}")
    if gzipped:
        data = gzip.decompress(data)
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "store": f"git:{CADENCE_REPO}@{commit}",
            "path": path}


# --- parsing (pure) ------------------------------------------------------------------------------------


def parse_requests(md: str) -> dict[str, int]:
    """driver script name -> request number, from the 'Used by:' lines of requests.md."""
    out = {}
    for number, used in re.findall(r"^## Request (\d+)\n\nUsed by: ([^\n]*)", md, re.M):
        for name in used.split(","):
            out[name.strip()] = int(number)
    return out


def parse_records_table(md: str) -> dict[str, dict]:
    """'d1-run1' -> the columns of its row in live-run-records.md (the session's own claims)."""
    out = {}
    for line in md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 10 or "/run" not in cells[0]:
            continue
        run = cells[0].replace("/", "-")
        out[run] = {"model": cells[1], "cost_usd": cells[2], "exit": cells[3], "r7": cells[4] == "True",
                    "request": cells[5], "edge": cells[6], "scope": cells[7], "deferral": cells[8]}
    return out


def parse_driver(sh: str) -> dict:
    """What a driver script asked for: the model flag, the plugin copy and the claude flags, no prompt."""
    line = next(l for l in sh.splitlines() if l.startswith("claude "))
    copy = re.search(r'--plugin-dir "\$E/([^"]+)"', line).group(1)
    model = re.search(r"--model (\S+)", line)
    flags = [f for f in ("--dangerously-skip-permissions", "--output-format stream-json", "--verbose") if f in line]
    return {"copy": copy, "model_flag": model.group(1) if model else None, "flags": " ".join(flags).split()}


def named_commit(diff_header: str) -> str | None:
    """The short commit a plugin-diff header names, or None ('driver scripts name no commit')."""
    found = re.search(r"name \['([0-9a-f]{7,40})'\]", diff_header)
    return found.group(1) if found else None


def transcript_times(lines: list[str]) -> tuple[str | None, str | None]:
    """First and last event timestamp of a stream-json transcript, as the records write them."""
    stamps = []
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and isinstance(event.get("timestamp"), str):
            stamps.append(event["timestamp"])
    if not stamps:
        return None, None
    return _iso(stamps[0]), _iso(stamps[-1])


def _iso(stamp: str) -> str:
    return _parse(stamp).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(timezone.utc)


def wall_seconds(start: str | None, end: str | None) -> float | None:
    return round((_parse(end) - _parse(start)).total_seconds(), 3) if start and end else None


def exit_code(stderr: str | None) -> int | None:
    found = re.search(r"^claude exit (\d+)$|^exit (\d+)$", stderr or "", re.M)
    return int(found.group(1) or found.group(2)) if found else None


# --- the records ---------------------------------------------------------------------------------------


def _base(run_id, batch, evidence, task, request_id, arm, model, cadence, **over) -> dict:
    rec = {
        "schema": 1, "run_id": run_id, "kind": "live", "batch": batch,
        "provenance": {"source": "backfill", "evidence": evidence}, "task": task, "request_id": request_id,
        "arm": arm, "cadence": cadence, "model_requested": model, "models_served": None, "session_id": None,
        "claude_version": None, "command": None, "started_at": None, "ended_at": None, "exit_code": None,
        "cost": {"list_usd": None, "reported_usd": None}, "stop_point": {"block": None, "reason": None},
        "transcript": store.missing("not kept"), "tree": store.missing("not kept"),
        "counts": {"counts": False, "why": WHY},
        "timing": {"agent_wall_seconds": None, "run_wall_seconds": None, "agent_active_seconds": None, "blocks": None},
        "isolation": None,
    }
    rec.update(over)
    return rec


def _facts(lines: list[str]) -> dict:
    facts = transcript_facts(lines)
    return {k: v for k, v in facts.items() if v is not None}


def _claim(row: dict | None) -> str:
    if not row:
        return "no row in live-run-records.md"
    probes = (f"probe request {row['request']}, edge {row['edge']}, scope {row['scope']}, deferral {row['deferral']}"
              if row["request"] != "-" else "no probe")
    return f"{'reached R7' if row['r7'] else 'did not reach R7'}; {probes}"


def e2e(cadence: Path) -> list[dict]:
    """One record per driver script of evidence/7058c2b0."""
    commit, folder = E2E, "evidence/live-runs"
    at = f"{CADENCE_REPO}@{commit[:7]}"
    requests = parse_requests(_text(cadence, commit, f"{folder}/requests.md") or "")
    rows = parse_records_table(_text(cadence, commit, f"{folder}/live-run-records.md") or "")
    drivers = _ls(cadence, commit, f"{folder}/drivers")
    last_run = {}
    for name in drivers:
        rid, n = name[:-3].split("-run")
        last_run[rid] = max(last_run.get(rid, 0), int(n))
    out = []
    for name in drivers:
        run = name[:-3]
        rid, n = run.split("-run")
        driver = parse_driver(_text(cadence, commit, f"{folder}/drivers/{name}") or "")
        number = requests.get(name)
        base_number = RESUME_OF_REQUEST.get(number, number)
        task = TASK_OF_REQUEST[base_number]
        if rid in ("d3", "d4") and base_number == 4:
            task = rid  # the scenario's own golden input; d2, d3 and d4 hold one text
        arm = "cadence-core" if driver["copy"].startswith("core-plugin") else "cadence"
        diff_head = (_text(cadence, commit, f"{folder}/plugin-diffs/{driver['copy']}.diff") or "").splitlines()
        short = named_commit(diff_head[0] if diff_head else "")
        repo_url = f"https://github.com/{CADENCE_REPO}" if arm == "cadence" else "https://github.com/jtouley/cadence-core"
        cad = {"repo": repo_url, "sha": _full_sha(cadence, short), "tree_clean": False} if short else None
        transcript_path = f"{folder}/transcripts/{run}.jsonl.gz"
        raw = _show(cadence, commit, transcript_path)
        lines = gzip.decompress(raw).decode("utf-8", "replace").splitlines() if raw else []
        facts = _facts(lines)
        started, ended = transcript_times(lines)
        row = rows.get(run)
        raw_err = _show(cadence, commit, f"{folder}/transcripts/{run}.stderr.gz")
        code = exit_code(gzip.decompress(raw_err).decode("utf-8", "replace")) if raw_err else None
        if driver["model_flag"]:
            model = MODEL_ALIAS.get(driver["model_flag"], driver["model_flag"])
        else:  # no --model: the model is the one the transcript's init event names
            model = (facts.get("models_served") or [None])[0]
        prompt = (f"<golden/cadence/{task}.md>" if task in ("d1", "d2", "d3", "d4") else f"<requests.md Request {base_number}>")
        if number != base_number:
            prompt = f"<requests.md Request {number}: a resume of Request {base_number}>"
        command = ["claude", "-p", f"/cadence:cadence {prompt}"]
        if driver["model_flag"]:
            command += ["--model", driver["model_flag"]]
        command += ["--plugin-dir", driver["copy"], *driver["flags"]]
        if row and row["r7"]:
            stop = {"block": "R7", "reason": "the session's own record says the run wrote its session summary"}
        elif code is None:
            stop = {"block": None, "reason": "the driver's stderr has no exit line: the run was cut off before claude "
                                             "exited; the stop block is not in the evidence"}
        else:
            stop = {"block": None, "reason": "did not reach R7 (the session's own record); the stop block is not in "
                                             "the evidence"}
        note = (f"claimed by the session that ran it: {_claim(row)} (its own probe script, "
                f"{folder}/probe-results-20261022T1558.txt). Plugin copy {driver['copy']}: ")
        note += (f"commit {short} plus the e2e config, and for some copies code copied in by hand "
                 f"({folder}/plugin-diffs/{driver['copy']}.diff), so not a clean commit"
                 if short else f"the driver names no commit ({folder}/plugin-diffs/{driver['copy']}.diff)")
        if task == "d2" and rid not in ("d2",):
            note += ". The request text equals golden/cadence/d2.md (d2, d3 and d4 hold one text)"
        if number != base_number:
            note += f". Request {number} resumes the run of request {base_number} on the same repository"
        if driver["model_flag"] is None:
            note += ". The driver passed no --model; the model is the transcript's"
        evidence = [f"{at}:{folder}/drivers/{name}", f"{at}:{transcript_path}", f"{at}:{folder}/live-run-records.md",
                    f"{at}:{folder}/requests.md#request-{number}", f"{at}:evidence/README.md"]
        if int(n) == last_run[rid]:
            tree = _blob(cadence, commit, f"{folder}/runs/{rid}/repo.bundle", gzipped=False)
            evidence.append(f"{at}:{folder}/runs/{rid}")
        else:
            tree = store.missing(f"the repository was kept only as left after run {last_run[rid]} "
                                 f"({at}:{folder}/runs/{rid}/repo.bundle)")
        rec = _base(f"{(started or '20261021')[:10].replace('-', '')}-{run}-{arm}-{(model or 'model').split('-')[1]}",
                    BATCH_E2E, evidence, task, TICKET[task], arm, model, cad, command=command, started_at=started,
                    ended_at=ended, exit_code=code, stop_point=stop,
                    transcript=_blob(cadence, commit, transcript_path, gzipped=True), tree=tree,
                    timing={"agent_wall_seconds": wall_seconds(started, ended), "run_wall_seconds": None,
                            "agent_active_seconds": facts.get("agent_active_seconds"), "blocks": None})
        rec.update({k: v for k, v in facts.items() if k in ("models_served", "session_id", "claude_version", "cost")})
        rec["provenance"]["note"] = note
        out.append(rec)
    return out


def arms(cadence: Path) -> list[dict]:
    """One record per arm folder of evidence/08495c94."""
    commit, folder = ARMS, "evidence/runs"
    at = f"{CADENCE_REPO}@{commit[:7]}"
    out = []
    for arm, (block, reason, claim) in ARM_RUNS.items():
        d = f"{folder}/{arm}"
        started = (_text(cadence, commit, f"{d}/started") or "").strip() or None
        ended_lines = (_text(cadence, commit, f"{d}/ended") or "").splitlines()
        ended = ended_lines[-1].strip() if len(ended_lines) > 1 else None
        code = exit_code("\n".join(ended_lines))
        commit_txt = _text(cadence, commit, f"{d}/cadence-commit.txt") or ""
        sha = re.search(r"cadence commit: ([0-9a-f]{7,40})", commit_txt)
        patch = re.search(r"plus (evidence/runs/\S+\.patch)", commit_txt)
        raw = _show(cadence, commit, f"{d}/stream.jsonl.gz")
        lines = gzip.decompress(raw).decode("utf-8", "replace").splitlines() if raw else []
        facts = _facts(lines)
        prompt = ARM_PROMPT[arm]
        note = (f"claimed by the session that ran it: {claim}. Cadence {sha.group(1)[:7] if sha else '?'} plus "
                f"{patch.group(1) if patch else 'an arm patch'}, so not a clean commit. The request "
                f"({folder}/request.txt) is the d1 scenario with one phrase changed ('one row per expense'); it is "
                f"not byte for byte golden/cadence/d1.md")
        if prompt == "prompt-b.txt":
            note += ". The prompt resumes the run that arm-b-try1 left on the same repository"
        rec = _base(f"{(started or '20261021')[:10].replace('-', '')}-{arm}-cadence-haiku", BATCH_ARMS,
                    [f"{at}:{d}", f"{at}:{folder}/{prompt}", f"{at}:{folder}/run.sh", f"{at}:evidence/README.md"],
                    "d1", "LOCAL-4", "cadence", "claude-haiku-5-5",
                    {"repo": f"https://github.com/{CADENCE_REPO}", "sha": sha.group(1), "tree_clean": False} if sha else None,
                    command=["claude", "-p", f"<{folder}/{prompt}>", "--model", "haiku", "--plugin-dir", "<cadence copy>",
                             "--dangerously-skip-permissions", "--output-format", "stream-json", "--verbose"],
                    started_at=started, ended_at=ended, exit_code=code, stop_point={"block": block, "reason": reason},
                    transcript=_blob(cadence, commit, f"{d}/stream.jsonl.gz", gzipped=True),
                    tree=_blob(cadence, commit, f"{d}/repo.bundle", gzipped=False),
                    timing={"agent_wall_seconds": wall_seconds(started, ended), "run_wall_seconds": None,
                            "agent_active_seconds": facts.get("agent_active_seconds"), "blocks": None})
        rec.update({k: v for k, v in facts.items() if k in ("models_served", "session_id", "claude_version", "cost")})
        rec["provenance"]["note"] = note
        out.append(rec)
    return out


def build(cadence: Path) -> list[dict]:
    return e2e(cadence) + arms(cadence)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.backfill_live", description=__doc__.split("\n\n")[0])
    ap.add_argument("--cadence", type=Path, required=True, help="a checkout of jtouley/cadence that has the evidence commits")
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    args = ap.parse_args(argv)
    if not available(args.cadence):
        print(f"the evidence commits are not in {args.cadence}: git fetch origin evidence/7058c2b0 evidence/08495c94",
              file=sys.stderr)
        return 2
    written = 0
    for rec in build(args.cadence):
        if (args.runs / rec["run_id"] / "record.json").exists():
            continue
        record.write_record(args.runs, rec)
        written += 1
    print(f"{written} record(s) written to {args.runs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
