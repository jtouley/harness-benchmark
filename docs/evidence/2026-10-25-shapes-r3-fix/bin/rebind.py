"""rebind.py <tree>: bind the stored run's session to this checkout, open, as at its P1/P4 gates."""
import hashlib, json, subprocess, sys
from pathlib import Path
tree = Path(sys.argv[1]).resolve()
ctx = tree / ".context"
top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=tree, capture_output=True, text=True).stdout.strip()
old = json.loads((ctx / "cadence-session.json").read_text())
src = ctx / old["ref"] if "ref" in old else None
data = json.loads(src.read_text()) if src else old
data.update({"workspace": str(tree), "active_skill": "cadence", "status": "active"})
for k in ("hard_stop", "completed_at", "block_stops"):
    data.pop(k, None)
key = hashlib.sha256(top.encode()).hexdigest()[:16]
dst = ctx / "sessions" / "by-worktree" / f"{key}.json"
dst.write_text(json.dumps(data, indent=2))
(ctx / "cadence-session.json").write_text(json.dumps({"ref": f"sessions/by-worktree/{key}.json"}))
print(dst)
