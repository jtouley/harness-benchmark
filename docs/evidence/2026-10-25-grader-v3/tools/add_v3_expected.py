"""Write grader v3's result per check into each fixture's expected.json (run from the harness-benchmark root).
    python -I add_v3_expected.py golden/pipeline/fixtures/grader-v3"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path("golden/pipeline").resolve()))
from pipetask import grade  # noqa: E402

key = json.loads(Path("golden/pipeline/key/answer_key.json").read_text())
root = Path(sys.argv[1]).resolve()
for fx in sorted(p for p in root.iterdir() if p.is_dir()):
    here = os.getcwd(); os.chdir(fx)
    try:
        r = grade.grade(Path("."), key)
    finally:
        os.chdir(here)
    exp = json.loads((fx / "expected.json").read_text())
    exp["v3"] = {"passed": r["passed"],
                 "checks": {n: {"pass": bool(c["pass"]), "resolution": c.get("source") or c.get("error")}
                            for n, c in sorted(r["checks"].items())}}
    (fx / "expected.json").write_text(json.dumps(exp, indent=1, sort_keys=True) + "\n")
    print(fx.name, "pinned", "".join("P" if v else "." for _, v in sorted(exp["pinned"]["checks"].items())),
          "v3", "".join("P" if c["pass"] else "." for _, c in sorted(exp["v3"]["checks"].items())))
