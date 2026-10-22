"""Recompute each cadence-core run's row from its own records and compare it with the reported table.

Usage (from the repository root):
    uv run --frozen python evidence/scripts/check_runs.py > evidence/outputs/check_runs.txt

Reads, per run:
  docs/evidence/2026-10-21-pipeline-cadence-core-subscription/<run>/   provenance, timing, grade, result,
      commits.txt, driver.log, context/sessions/by-worktree/*.json (Cadence's own hard-stop record)
  evidence/runs/<run>/transcript.jsonl.gz                              the session's stream-json output
Prints, per run: the driver command, the models that served every assistant message (main and peers),
the session ids, the stop point from Cadence's record, the grader's result per check, and each reported
value next to the recomputed one with MATCH or MISMATCH.
"""
from __future__ import annotations

import collections
import gzip
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "docs/evidence/2026-10-21-pipeline-cadence-core-subscription"
RUNS = ROOT / "evidence/runs"
sys.path.insert(0, str(ROOT / "scripts"))
from pipeline_trial import cost_and_tokens  # noqa: E402  the repository's own cost code

PRICING = json.loads((ROOT / "pricing.json").read_text())

# The table reported to the owner on 22 October (write-up "Results" table, counted runs).
REPORTED = {
    "P1-cadence-core-haiku-1": {"ended_at": "P4", "stop": "asked (no hard stop)", "phase_commits": 0, "reward": 0.0, "agent_min": 9.6, "list_usd": "0.11", "cc_usd": "0.12"},
    "P1-cadence-core-haiku-2": {"ended_at": "P4", "stop": "retries", "phase_commits": 0, "reward": 0.0, "agent_min": 20.6, "list_usd": "0.24", "cc_usd": "0.25"},
    "P1-cadence-core-haiku-3": {"ended_at": "E4", "stop": "credentials", "phase_commits": 7, "reward": 0.0, "agent_min": 51.6, "list_usd": "0.55", "cc_usd": "1.71"},
    "P2-cadence-core-haiku-1": {"ended_at": "P7", "stop": "retries", "phase_commits": 0, "reward": 0.0, "agent_min": 42.7, "list_usd": "0.57", "cc_usd": "0.59"},
    "P2-cadence-core-haiku-2": {"ended_at": "E4", "stop": "credentials", "phase_commits": 11, "reward": 0.0, "agent_min": 64.4, "list_usd": "0.68", "cc_usd": "2.48"},
    "P2-cadence-core-haiku-3": {"ended_at": "P7", "stop": "retries", "phase_commits": 1, "reward": 0.0, "agent_min": 81.3, "list_usd": "1.09", "cc_usd": "1.54"},
}
BLOCK = re.compile(r"\b([APER][1-9])\b")


def transcript(run: str):
    with gzip.open(RUNS / run / "transcript.jsonl.gz", "rt", encoding="utf-8") as fh:
        for line in fh:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def served(run: str) -> tuple[dict, list[str], str]:
    models, sessions, last_refusal = {}, [], ""
    seen = set()
    for e in transcript(run):
        if e.get("session_id") and e["session_id"] not in sessions:
            sessions.append(e["session_id"])
        if e.get("type") == "assistant":
            m = e["message"]
            if m.get("id") not in seen:
                seen.add(m.get("id"))
                models[m.get("model")] = models.get(m.get("model"), 0) + 1
        if e.get("type") == "user" and isinstance(e.get("message", {}).get("content"), list):
            for c in e["message"]["content"]:
                text = c.get("content") if isinstance(c.get("content"), str) else json.dumps(c.get("content"))
                hit = re.search(r"BLOCKED: unsafe peer handoff\. (P\d) needs", text or "")
                if hit:
                    last_refusal = hit.group(1)
    return models, sessions, last_refusal


def stop_record(run: str) -> dict:
    for f in sorted((DATA / run / "context/sessions/by-worktree").glob("*.json")):
        d = json.loads(f.read_text())
        hs = d.get("hard_stop")
        if hs:
            return {"class": hs.get("class"), "reason": hs.get("reason"), "at": hs.get("at"), "file": str(f.relative_to(ROOT))}
        if d.get("stop_refusals"):
            return {"class": None, "stop_refusals": d["stop_refusals"], "stop_refusal_slug": d.get("stop_refusal_slug"),
                    "file": str(f.relative_to(ROOT))}
    return {}


def main() -> int:
    mismatches = 0
    for run in sorted(p.name for p in DATA.iterdir() if p.is_dir()):
        d = DATA / run
        prov = json.loads((d / "provenance.json").read_text())
        trial = json.loads((d / "trial.json").read_text())
        print(f"## {run}")
        print(f"driver: PIPE_ROOT=<dir> bash evidence/scripts/host_trial.sh {prov['task']} {run.replace('-0-killed', '-1').replace('-2a-killed', '-2')}"
              f"  (cadence-core {prov['cadence_sha']}, {prov['claude_version']}, requested model {prov['model']})")
        models, sessions, refusal = served(run)
        print(f"models that served assistant messages (distinct message ids): {models}")
        print(f"session ids in the transcript: {sessions}")
        if trial.get("infra_error"):
            print(f"NOT SCORED (infra_error): {trial['infra_error']}\n")
            continue
        timing = json.loads((d / "timing.json").read_text())
        grade = json.loads((d / "grade.json").read_text())
        result = json.loads((d / "result.json").read_text())
        stop = stop_record(run)
        ended = (BLOCK.findall(stop.get("reason") or "") or [refusal or "?"])[0]
        commits = (d / "commits.txt").read_text().splitlines() if (d / "commits.txt").exists() else []
        phase = [c for c in commits if re.search(r"\bphase\b", c, re.I)]
        cost, _ = cost_and_tokens(result, PRICING, prov["model"])
        print(f"stop record: {json.dumps(stop)}")
        if not stop.get("class"):
            print(f"last refused peer handoff in the transcript: {refusal}")
        print(f"grader: reward {grade.get('reward')}, passed {grade.get('passed')}/{grade.get('total')}, "
              f"idempotent {grade.get('idempotent')}, stream_ok {grade.get('stream_ok')}, "
              f"builds {[b['exit'] for b in grade.get('build', [])]}, streams {[s['exit'] for s in grade.get('stream', [])]}")
        for k, v in sorted((grade.get("checks") or {}).items()):
            print(f"  check {k}: pass={v.get('pass')} {str(v.get('error') or v.get('trap') or '')[:120]}")
        found = {"ended_at": ended, "stop": stop.get("class") or "asked (no hard stop)", "phase_commits": len(phase),
                 "reward": grade.get("reward"), "agent_min": round(timing["agent_seconds"] / 60, 1),
                 "list_usd": f"{cost:.2f}", "cc_usd": f"{result.get('total_cost_usd', 0):.2f}"}
        print(f"commits after the trial's base ({len(commits)}): " + "; ".join(c.split(" ", 2)[-1] for c in commits))
        for key, want in REPORTED[run].items():
            ok = found[key] == want
            mismatches += not ok
            print(f"  {key:14} reported {want!s:22} recomputed {found[key]!s:22} {'MATCH' if ok else 'MISMATCH'}")
        print()
    print(f"mismatches: {mismatches}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
