"""Score a review skill revision against the current version on the review eval set (skill-creator layout).

Two commands, with the agent work between them done by Agent-tool subagents of a Claude Code session (never a
CLI agent process: owner limit, 2026-10-25):

    python -m revieweval.compare layout --work WORK --iteration NAME --cadence CADENCE_CHECKOUT \\
        --config old_skill=pr-review-local@2100c6e --config builtin=code-review \\
        --config new_skill=antagonistic-review@<sha>#full --baseline old_skill --baseline builtin [--runs 3]
    # the session dispatches each run's steps.json, then its grader.md, as subagents (see revieweval/README.md)
    python -m revieweval.compare collect --work WORK --iteration NAME --skill-creator SKILL_CREATOR_DIR

`layout` writes WORK/<NAME>/ in skill-creator's workspace layout: <case>/eval_metadata.json and
<case>/{old_skill,new_skill}/run-<k>/ with its own clone of the case's tree (repo/), the subagent prompts
(steps.json) and the grader prompt (grader.md). The prompts of a configuration come from the skill's own text
at the pinned commit, so a revision is scored as written.

`collect` runs skill-creator's scripts/aggregate_benchmark.py on WORK/<NAME> (benchmark.json, benchmark.md),
then writes comparison.json: per configuration the recall against the known answers, the false findings,
wall time and tokens, each as mean and stddev over runs, and the verdict of the owner's rule:
the new version is measurably better only if its recall beats the old one by more than the run-to-run
variance (the larger stddev), it has no more false findings beyond that variance, and its wall time and tokens
are at most SPEED_SLO times the old one's (the postmortem's speed SLO, 120 to 125%; 1.25 is used).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEED_SLO = 1.25
LETTERS = ("A", "B", "C")
NO_CLI = ("Run as an Agent-tool subagent of this session. Do not start `claude` or any other agent CLI, do not "
          "change permission modes, and do not create triggers or scheduled tasks.")


def cases() -> list[dict]:
    return json.loads((HERE / "cases.json").read_text())["cases"]


def assertions(case: dict) -> list[str]:
    out = []
    for a in case["answers"]:
        if a["kind"] == "defect" and a["severity"] == "must-fix" and not a.get("reproduced_locally_only"):
            out.append(f"[recall:{a['id']}] The final review reports as must-fix: {a['statement']}")
        elif a["kind"] == "defect" and a.get("reproduced_locally_only"):
            out.append(f"[recall:{a['id']}] The final review reports as must-fix, shown from the code or a local stub "
                       f"(an outside request is not required): {a['statement']}")
        elif a["kind"] == "defect":
            out.append(f"[recall:{a['id']}] The final review reports, at any severity: {a['statement']}")
        else:
            out.append(f"[control:{a['id']}] {a['statement']} The final review makes no such must-fix claim.")
    return out


def skill_text(cadence: Path, sha: str, path: str) -> str:
    return subprocess.run(["git", "show", f"{sha}:{path}"], cwd=cadence, check=True, capture_output=True,
                          text=True).stdout


def export_cadence(cadence: Path, sha: str, dest: Path) -> Path:
    home = dest / f"cadence-{sha[:7]}"
    if not home.exists():
        home.mkdir(parents=True)
        archive = subprocess.run(["git", "archive", sha], cwd=cadence, check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", str(home)], input=archive, check=True)
    return home


def fenced(text: str) -> list[str]:
    return [b.strip() for b in re.findall(r"```\n(.*?)```", text, flags=re.S)]


def steps_for(spec: str, cadence: Path, work: Path, run: Path, pr: str) -> tuple[list[dict], list[str]]:
    """The subagent steps of one run of configuration `spec`, and the output files the grader reads as the review.

    `spec` is `pr-review-local@<sha>`, `code-review` (Claude Code's built-in skill, as it ships), or
    `antagonistic-review@<sha>[#full|#three|#single]`: #full is the whole procedure; #three is the three reviewers
    with no consolidation (the grader reads their union); #single is reviewer A alone.
    """
    skill, _, rest = spec.partition("@")
    sha, _, variant = rest.partition("#")
    repo, out, log = run / "repo", run / "outputs", run.parents[1] / "build.log"
    where = (f"The change under review is branch `review` against `base` in {repo} (your own copy). "
             f"The one build of this tree is done: its log is {log} when it exists. Do not run the full build again. "
             f"Write your files to {out}. Read nothing outside your copy, the build log and {out}: other paths on "
             f"this machine hold grading material. {NO_CLI}")
    final = f"{out}/final-review-{pr}.md"
    if skill == "code-review":
        return [{"id": "review", "after": [], "save_report_to": final,
                 "prompt": f"/code-review {repo}"}], [final]
    if skill == "pr-review-local":
        home = export_cadence(cadence, sha, work / "skills")
        return [{"id": "R1", "after": [], "save_report_to": None, "prompt":
                 f"CADENCE_HOME is {home}. Follow {home}/commands/pr-review-local.md with the argument `local`. "
                 f"There is no active Cadence run: skip the ledger append and the gates, and write the review to "
                 f"{final}. {where}"}], [final]
    if skill == "antagonistic-review":
        variant = variant or "full"
        prompts = fenced(skill_text(cadence, sha, "skills/antagonistic-review/SKILL.md"))
        review, consolidate, explain = prompts[0], prompts[1], prompts[2]
        review = review.replace("<pr-number>", pr)
        letters = LETTERS[:1] if variant == "single" else LETTERS
        steps = [{"id": x, "after": [], "save_report_to": None,
                  "prompt": f"{review.replace('<letter>', x)}\n\nYou are reviewer {x}. {where}"} for x in letters]
        files = [f"{out}/findings-{pr}-{x}.txt" for x in letters]
        if variant in ("single", "three"):
            return steps, files
        home = export_cadence(cadence, sha, work / "skills")
        skill_md = home / "skills" / "antagonistic-review" / "SKILL.md"
        steps.append({"id": "consolidate", "after": list(letters), "save_report_to": None, "prompt":
                      f"{consolidate}\n\nThe findings files: {', '.join(files)}. Apply the sections \"The standard of "
                      f"the consolidation\" and \"The final review\" of {skill_md}, and save the final review to {final}. "
                      f"{where}"})
        steps.append({"id": "explain", "after": ["consolidate"], "save_report_to": None, "prompt":
                      f"{explain}\n\nSave it to {out}/explain-{pr}.md. {where}"})
        return steps, [final]
    raise SystemExit(f"unknown configuration {spec}")


def grader_prompt(case: dict, run: Path, review_files: list[str]) -> str:
    lines = "\n".join(f"- {a}" for a in assertions(case))
    files = ", ".join(review_files)
    return (f"Grade one review run. Follow the grader instructions of the skill-creator skill (agents/grader.md). "
            f"outputs_dir: {run / 'outputs'}. The review to grade is the text of: {files} (taken together, as one "
            f"review). The reviewed tree is {run / 'repo'} (branch `review` against `base`): read it, and run single "
            f"commands in it to check a claim.\n\nExpectations (use these texts exactly):\n{lines}\n\nAlso list "
            f"every must-fix finding of the review under `claims`, with `verified` true when the tree shows it holds, "
            f"false when the tree shows it does not, and null when it cannot be told. Write {run / 'grading.json'}. "
            f"{NO_CLI}")


def layout(args) -> None:
    root = args.work / args.iteration
    configs = dict(c.split("=", 1) for c in args.config)
    picked = [c for c in cases() if not args.cases or c["name"] in args.cases]
    unknown = sorted(set(args.cases) - {c["name"] for c in cases()})
    if unknown:
        raise SystemExit(f"unknown cases: {', '.join(unknown)}")
    if args.cases and (root / "dispatch.jsonl").exists():  # it would replace the full run list with the subset's
        raise SystemExit(f"{root / 'dispatch.jsonl'} exists: lay out a subset under a new --iteration")
    meta = {"configs": configs, "baselines": args.baseline, "runs": args.runs}
    dispatch = []
    for case in picked:
        cdir = root / case["name"]
        cdir.mkdir(parents=True, exist_ok=True)
        tree = args.work / "trees" / case["name"] / "repo"
        built = args.work / "built" / case["name"]
        if (built / "build.log").exists():
            shutil.copy(built / "build.log", cdir / "build.log")
        pr = case["name"]
        (cdir / "eval_metadata.json").write_text(json.dumps(
            {"eval_name": case["name"], "prompt": "Review the change `review` against `base` (a stored run tree, blinded).",
             "assertions": assertions(case)}, indent=1) + "\n")
        for config, spec in configs.items():
            for k in range(1, args.runs + 1):
                run = cdir / config / f"run-{k}"
                (run / "outputs").mkdir(parents=True, exist_ok=True)
                (run / "source").write_text(f"{tree}\n")  # the prepared tree has `base`; built/repo does not
                steps, review_files = steps_for(spec, args.cadence, args.work, run, pr)
                (run / "steps.json").write_text(json.dumps({"config": spec, "steps": steps,
                                                            "review_files": review_files}, indent=1) + "\n")
                (run / "grader.md").write_text(grader_prompt(case, run, review_files) + "\n")
                for st in steps:
                    dispatch.append({"run": str(run), "case": case["name"], "config": config, "spec": spec,
                                     "step": st["id"], "after": st["after"], "diff": f"{run / 'repo'} (review vs base)",
                                     "prompt": st["prompt"], "output": st["save_report_to"] or str(run / "outputs"),
                                     "timing": str(run / "timing.json")})
                dispatch.append({"run": str(run), "case": case["name"], "config": config, "spec": "grader",
                                 "step": "grade", "after": [st["id"] for st in steps], "diff": str(run / "repo"),
                                 "prompt": (run / "grader.md").read_text().strip(), "output": str(run / "grading.json"),
                                 "timing": None})
    (root / "configs.json").write_text(json.dumps(meta, indent=1) + "\n")
    with open(root / "dispatch.jsonl", "w") as f:
        for d in dispatch:
            f.write(json.dumps(d) + "\n")
    print(f"{len(picked)} cases x {len(configs)} configurations x {args.runs} runs: {len(dispatch)} dispatches in "
          f"{root / 'dispatch.jsonl'}")


def setup(run: Path) -> None:
    """The run's own clone of its case's tree (operator step, before the run's first dispatch)."""
    repo = run / "repo"
    if repo.exists() and subprocess.run(["git", "-C", str(repo), "rev-parse", "-q", "--verify", "refs/heads/base"],
                                        capture_output=True).returncode != 0:
        shutil.rmtree(repo)  # a clone without `base` (one made from built/repo) cannot be reviewed or graded
    if not repo.exists():
        src = (run / "source").read_text().strip()
        subprocess.run(["git", "clone", "-q", "-b", "review", src, str(run / "repo")], check=True)
        subprocess.run(["git", "-C", str(run / "repo"), "branch", "-q", "base", "origin/base"], check=True)


def cleanup(run: Path) -> None:
    """Remove the run's clone once grading.json exists (operator step: the disk holds few clones at a time)."""
    if (run / "grading.json").exists() and (run / "repo").exists():
        shutil.rmtree(run / "repo")


def stats(xs: list[float]) -> dict:
    if not xs:
        return {"mean": None, "stddev": None, "n": 0}
    m = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0
    return {"mean": round(m, 4), "stddev": round(sd, 4), "n": len(xs)}


def run_metrics(run: Path) -> dict | None:
    try:
        g = json.loads((run / "grading.json").read_text())
    except (OSError, ValueError):
        return None
    exp = g.get("expectations", [])
    rec = [e["passed"] for e in exp if e["text"].startswith("[recall:")]
    ctl = [e["passed"] for e in exp if e["text"].startswith("[control:")]
    refuted = sum(1 for c in g.get("claims", []) if c.get("verified") is False)
    try:
        t = json.loads((run / "timing.json").read_text())
    except (OSError, ValueError):
        t = {}
    if "steps" in t and "total_duration_seconds" not in t:
        t = {**t, **critical_path(run, t["steps"])}
    return {"recall_hits": sum(rec), "recall_total": len(rec), "false": ctl.count(False) + refuted,
            "seconds": t.get("total_duration_seconds"), "tokens": t.get("total_tokens")}


def critical_path(run: Path, steps: dict) -> dict:
    """Wall time and tokens of a run from its steps' Agent-tool notifications ({step: {duration_ms, total_tokens}}):
    parallel steps overlap, so the wall time is the longest path through steps.json's `after` lists."""
    order = json.loads((run / "steps.json").read_text())["steps"]
    done: dict[str, float] = {}
    for st in order:
        start = max((done[a] for a in st["after"]), default=0.0)
        done[st["id"]] = start + steps[st["id"]]["duration_ms"] / 1000
    return {"total_duration_seconds": round(max(done.values()), 1),
            "total_tokens": sum(v["total_tokens"] for v in steps.values())}


def summarize(rows: list[dict]) -> dict:
    """Recall and false findings per run number (one value per repeat, over all cases), so the stddev is the
    run-to-run variance; time and tokens per review."""
    by_run: dict[str, list[dict]] = {}
    for r in rows:
        by_run.setdefault(r["run"], []).append(r)
    recall = [sum(r["recall_hits"] for r in rs) / max(1, sum(r["recall_total"] for r in rs)) for rs in by_run.values()]
    false = [sum(r["false"] for r in rs) for rs in by_run.values()]
    return {"recall": stats(recall), "false_findings": stats(false),
            "seconds_per_review": stats([r["seconds"] for r in rows if r["seconds"] is not None]),
            "tokens_per_review": stats([r["tokens"] for r in rows if r["tokens"] is not None]),
            "graded_runs": len(rows)}


def verdict(new: dict, old: dict) -> dict:
    """The owner's rule for `new` against one baseline `old`."""
    if not new["recall"]["n"] or not old["recall"]["n"]:
        return {"measurably_better": None, "why": "no graded runs for one configuration"}
    var = max(new["recall"]["stddev"], old["recall"]["stddev"])
    gain = new["recall"]["mean"] - old["recall"]["mean"]
    fvar = max(new["false_findings"]["stddev"], old["false_findings"]["stddev"])
    fgain = new["false_findings"]["mean"] - old["false_findings"]["mean"]
    ratios = {}
    for k in ("seconds_per_review", "tokens_per_review"):
        a, b = new[k]["mean"], old[k]["mean"]
        ratios[k] = round(a / b, 3) if a is not None and b else None
    checks = {"recall_gain_exceeds_variance": gain > var,
              "false_findings_not_worse_beyond_variance": fgain <= fvar,
              "time_within_speed_slo": ratios["seconds_per_review"] is not None
              and ratios["seconds_per_review"] <= SPEED_SLO,
              "tokens_within_speed_slo": ratios["tokens_per_review"] is not None
              and ratios["tokens_per_review"] <= SPEED_SLO}
    return {"measurably_better": all(checks.values()), "does_not_regress": gain >= -var and fgain <= fvar,
            "recall_gain": round(gain, 4), "recall_variance": var, "false_gain": round(fgain, 4),
            "ratios": ratios, "speed_slo": SPEED_SLO, "checks": checks}


def compare(root: Path) -> dict:
    meta = json.loads((root / "configs.json").read_text())
    rows: dict[str, list[dict]] = {c: [] for c in meta["configs"]}
    for cdir in sorted(p for p in root.iterdir() if (p / "eval_metadata.json").exists()):
        for config in rows:
            for run in sorted((cdir / config).glob("run-*")):
                m = run_metrics(run)
                if m:
                    rows[config].append({"case": cdir.name, "run": run.name, **m})
    summary = {c: summarize(r) for c, r in rows.items()}
    baselines = meta["baselines"]
    verdicts = {c: {b: verdict(summary[c], summary[b]) for b in baselines}
                for c in summary if c not in baselines}
    beats_all = {c: (all(v["measurably_better"] for v in vs.values()) if all(
        v["measurably_better"] is not None for v in vs.values()) else None) for c, vs in verdicts.items()}
    return {"configs": meta["configs"], "summary": summary, "verdicts": verdicts,
            "beats_every_baseline": beats_all, "runs": rows}


def collect(args) -> None:
    root = args.work / args.iteration
    agg = Path(args.skill_creator) / "scripts" / "aggregate_benchmark.py" if args.skill_creator else None
    if agg and agg.exists():
        subprocess.run([sys.executable, str(agg), str(root), "--skill-name", args.iteration], check=False)
    result = compare(root)
    (root / "comparison.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({k: result[k] for k in ("summary", "verdicts", "beats_every_baseline")}, indent=1))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("layout")
    a.add_argument("--work", type=Path, required=True)
    a.add_argument("--iteration", required=True)
    a.add_argument("--cadence", type=Path, required=True)
    a.add_argument("--config", action="append", required=True, help="NAME=SPEC, repeatable")
    a.add_argument("--baseline", action="append", default=[], help="a NAME that is a baseline, repeatable")
    a.add_argument("--runs", type=int, default=3)
    a.add_argument("cases", nargs="*")
    for name in ("setup", "cleanup"):
        r = sub.add_parser(name)
        r.add_argument("runs", nargs="+", type=Path)
    c = sub.add_parser("collect")
    c.add_argument("--work", type=Path, required=True)
    c.add_argument("--iteration", required=True)
    c.add_argument("--skill-creator", default="")
    args = ap.parse_args(argv)
    if args.cmd in ("setup", "cleanup"):
        for run in args.runs:
            (setup if args.cmd == "setup" else cleanup)(run)
        return
    layout(args) if args.cmd == "layout" else collect(args)


if __name__ == "__main__":
    main()
