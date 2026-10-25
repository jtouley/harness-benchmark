"""The regrade table: official score (latest scores.jsonl line), the pinned grader's regrade, grader v3's result
on the same trial's marts, and each check that changed with its v3 resolution.
    python -I table.py W3DIR RUNS_DIR OUT_JSON"""
import json, sys
from pathlib import Path
W, RUNS, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
rows = []
for g in sorted(W.glob("*/g")):
    run = g.parent.name
    score = [json.loads(l) for l in (RUNS / run / "scores.jsonl").read_text().splitlines() if l.strip()][-1]
    p, v = json.loads((g / "pinned.json").read_text()), json.loads((g / "v3-marts.json").read_text())
    gate = bool(p.get("stream_ok")) and bool(p.get("idempotent"))
    v3_reward = round(v["passed"] / v["total"], 4) if gate else 0.0
    changes = []
    for n in map(str, range(1, 8)):
        a, b = p["checks"][n], v["checks"][n]
        if bool(a["pass"]) != bool(b["pass"]):
            changes.append({"check": n, "pinned": bool(a["pass"]), "v3": bool(b["pass"]),
                            "pinned_reason": a.get("error") or ("got " + str(a.get("got"))[:60] if "got" in a else a.get("reading")),
                            "v3_resolution": b.get("source") or b.get("error")})
    rows.append({"run_id": run, "official": {"score": round(score["reward"] * 7), "passed": score["passed"],
                 "reward": score["reward"], "stream_ok": score["stream_ok"], "idempotent": score["idempotent"],
                 "grader_commit": score["grader"]["commit"]},
                 "pinned_regrade": {"score": round(p["reward"] * 7), "passed": p["passed"], "reward": p["reward"],
                                    "stream_ok": p["stream_ok"], "idempotent": p["idempotent"],
                                    "checks": "".join("P" if p["checks"][str(n)]["pass"] else "." for n in range(1, 8))},
                 "reproduced": (p["passed"], p["reward"], p["stream_ok"], p["idempotent"]) ==
                               (score["passed"], score["reward"], score["stream_ok"], score["idempotent"]),
                 "v3": {"score": round(v3_reward * 7), "passed": v["passed"], "reward": v3_reward,
                        "checks": "".join("P" if v["checks"][str(n)]["pass"] else "." for n in range(1, 8))},
                 "changes": changes,
                 "v3_checks": {n: {"pass": bool(c["pass"]), "resolution": c.get("source") or c.get("error")}
                               for n, c in sorted(v["checks"].items())}})
OUT.write_text(json.dumps(rows, indent=1) + "\n")
for r in rows:
    print(f"{r['run_id']:36s} off {r['official']['score']} ({r['official']['passed']}) repro {r['reproduced']} v3 {r['v3']['score']} ({r['v3']['passed']}) {r['pinned_regrade']['checks']} -> {r['v3']['checks']} {[c['check'] for c in r['changes']]}")
