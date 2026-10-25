"""Golden-sample fixtures for grader v3, from the regraded stored trees.

    python -I build_fixtures.py W3DIR OUT RUNS_TSV

For each run: the delivered oracle_map.yml (verbatim) and every published mart it names (the Parquet files the
pinned grader's trial left under out/marts/, byte for byte), plus expected.json: the pinned trial's result per
check (passed, reward, stream_ok, idempotent) and the tree and blob it came from. The v3 result per check is
added by the test suite's own regeneration (tests/test_pipeline_grader_v3.py --regen is not used: expected v3
answers are written here from grader v3 at build time and the test checks them).
"""
import hashlib, json, os, re, shutil, sys, subprocess
from pathlib import Path

W, OUT, TSV = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
blobs = {l.split("\t")[0]: l.rstrip("\n").split("\t") for l in TSV.read_text().splitlines()}
for run_dir in sorted(W.glob("*/g")):
    run = run_dir.parent.name
    repo = run_dir / "repo"
    src = repo / "oracle_map.yml"
    if not src.exists():
        continue
    dest = OUT / run
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "out" / "marts").mkdir(parents=True)
    text = src.read_text(encoding="utf-8")
    shutil.copy2(src, dest / "oracle_map.yml")
    marts = sorted(p.name for p in (repo / "out" / "marts").iterdir())
    used = [m for m in marts if re.search(r"(?<![\w])" + re.escape(m) + r"(?![\w])", text)]
    for m in used:
        p = repo / "out" / "marts" / m
        shutil.copytree(p, dest / "out" / "marts" / m) if p.is_dir() else shutil.copy2(p, dest / "out" / "marts" / m)
    pinned = json.loads((run_dir / "pinned.json").read_text())
    _, task, tree_path, tree_sha, tx_path, tx_sha = blobs[run]
    src_tree = repo  # the graded copy
    expected = {
        "run_id": run, "task": task,
        "tree_blob": {"sha256": tree_sha, "path": tree_path, "store": "runs-store"},
        "transcript_blob": {"sha256": tx_sha, "path": tx_path, "store": "runs-store"},
        "graded_snapshot": (pinned.get("snapshot") or {}).get("commit"),
        "marts": used,
        "pinned": {"grader_commit": "c344bea44951cfc5a3a3a99aaa598fdaaedabba8",
                   "grader_tree": "8a0977e42fa02981802090d1f9517efe537994c4",
                   "passed": pinned.get("passed"), "reward": pinned.get("reward"),
                   "stream_ok": pinned.get("stream_ok"), "idempotent": pinned.get("idempotent"),
                   "checks": {n: bool(c.get("pass")) for n, c in sorted(pinned.get("checks", {}).items())}},
    }
    (dest / "expected.json").write_text(json.dumps(expected, indent=1, sort_keys=True) + "\n")
    print(run, len(used), "marts")
