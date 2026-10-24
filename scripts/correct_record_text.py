"""Correct the score text of a record that scripts/run_one.sh published before loop/run_summary.py: its commit
message, its pull request body and its pr.md printed "<passed>/<total>" as the score, and the score is
round(reward x total)/total (run 20261024-P1-cadence-haiku-core-4, PR #115: "2/7" for a 0/7 run). The batch
postmortem that loop.driver wrote in the same commit (postmortems/<batch>.md) printed the passed count in its
Score column too, before loop/postmortem.py used the same score.

    uv run --frozen python scripts/correct_record_text.py <run-id> [--branch rec/<run-id>] [--pr N]
        [--pr-md $WORK/pr.md] [--push]

It never rewrites history and never force-pushes, so it works on a record branch another session created: the
corrected text goes in a new commit on top of the branch (a fast-forward push), whose message is the
record commit's subject with the corrected summary, made from the branch's own runs/<run-id>/record.json and
scores.jsonl. The commit also holds every postmortem on the branch that covers the run's batch, written again by
this checkout's loop.postmortem from the branch's runs/, findings.jsonl and citations.json (the run's row then
reads its score, passed, reward and stream_ok); it is empty when those postmortems are already current. With --pr it replaces the "**Score:**" line of that pull request's body (gh api, REST); with
--pr-md the same line of a local pr.md. Without --push it changes nothing: it prints the commit message and
the new body, and says what --push would do.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from loop import postmortem, run_summary, trace  # noqa: E402

REPO = "jtouley/harness-benchmark"
SCORE_LINE = re.compile(r"^\*\*Score:\*\* .*$", re.M)
TRAILERS = ("Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
            "Claude-Session: https://claude.ai/code/session_01QAzPEbn3jrqAw3J58oC4VA")


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def commit_message(batch: str, rid: str, summary: str, postmortems: list[str] | None = None) -> str:
    pms = (f" {', '.join(postmortems)} written again by loop.postmortem: its Score column printed the passed "
           "count too.") if postmortems else ""
    return (f"{batch}: {rid}: score text corrected\n\n{summary}\n\n"
            "The record commit's message printed the passed count as the score; the score is round(reward x "
            f"total)/total, the scoreboard's (loop/run_summary.py).{pms} Nothing in the record changes.\n\n"
            + TRAILERS)


def refresh_postmortems(wt: Path, batch: str) -> list[str]:
    """Every postmortem in checkout `wt` that covers `batch`, written again from wt's runs/, findings.jsonl and
    citations.json by this checkout's generator; the paths (relative to wt) whose text changed."""
    pms = wt / "postmortems"
    before = {p: p.read_text(encoding="utf-8") for p in pms.glob("*.md")} if pms.is_dir() else {}
    written = postmortem.refresh(batch, wt / "runs", pms, wt / "findings.jsonl",
                                 trace.load_citations(wt / "citations.json"))
    return [str(p.relative_to(wt)) for p in written if before.get(p) != p.read_text(encoding="utf-8")]


def corrected_body(body: str, summary: str) -> str:
    """The body with its **Score:** line replaced (one is added at the top when it has none)."""
    line = f"**Score:** {summary}"
    if SCORE_LINE.search(body):
        return SCORE_LINE.sub(lambda _: line, body, count=1)
    return f"{line}\n\n{body}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run_id")
    ap.add_argument("--branch", help="the record branch (default rec/<run-id>)")
    ap.add_argument("--pr", type=int, help="the record's pull request number: its body's **Score:** line")
    ap.add_argument("--pr-md", type=Path, help="a local pr.md whose **Score:** line to correct")
    ap.add_argument("--push", action="store_true", help="commit, push and edit; without it, print only")
    args = ap.parse_args(argv)
    branch = args.branch or f"rec/{args.run_id}"
    git("fetch", "-q", "origin", f"+refs/heads/{branch}:refs/remotes/origin/{branch}")
    with tempfile.TemporaryDirectory() as tmp:
        wt = Path(tmp) / "rec"
        git("worktree", "add", "-q", "--detach", str(wt), f"origin/{branch}")
        try:
            run = wt / "runs" / args.run_id
            rec = json.loads((run / "record.json").read_text(encoding="utf-8"))
            summary = run_summary.summary(run)
            changed = refresh_postmortems(wt, rec["batch"])
            message = commit_message(rec["batch"], args.run_id, summary, changed)
            print(f"== {branch} at {git('rev-parse', 'HEAD', cwd=wt)}\n== commit message\n{message}")
            if changed:
                print(f"== postmortem diff\n{git('diff', '--', *changed, cwd=wt)}")
            if args.push:
                if changed:
                    git("add", "--", *changed, cwd=wt)
                subprocess.run(["git", "commit", "-q", "--allow-empty", "-F", "-"], cwd=wt, input=message,
                               text=True, check=True)
                git("push", "-q", "origin", f"HEAD:refs/heads/{branch}", cwd=wt)  # a fast-forward: never forced
                print(f"pushed {git('rev-parse', 'HEAD', cwd=wt)} to {branch}")
        finally:
            git("worktree", "remove", "--force", str(wt))
    if args.pr_md:
        body = corrected_body(args.pr_md.read_text(encoding="utf-8"), summary)
        if args.push:
            args.pr_md.write_text(body, encoding="utf-8")
            print(f"rewrote the **Score:** line of {args.pr_md}")
        else:
            print(f"== {args.pr_md} would read\n{body}")
    if args.pr:
        api = f"repos/{REPO}/pulls/{args.pr}"
        old = json.loads(subprocess.run(["gh", "api", api], check=True, capture_output=True, text=True).stdout)
        if old.get("head", {}).get("ref") != branch:
            print(f"PR #{args.pr} is on {old.get('head', {}).get('ref')}, not {branch}: not edited", file=sys.stderr)
            return 1
        body = corrected_body(old.get("body") or "", summary)
        if args.push:
            subprocess.run(["gh", "api", "-X", "PATCH", api, "--input", "-"], input=json.dumps({"body": body}),
                           text=True, check=True, capture_output=True)
            print(f"edited the body of PR #{args.pr}")
        else:
            print(f"== PR #{args.pr} body would read\n{body}")
    if not args.push:
        print("dry run: nothing committed, pushed or edited (add --push)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
