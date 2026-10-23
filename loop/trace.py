"""The trace: per run, the findings that cite it, and the cadence commits and pull requests that cite it.

    python -m loop.trace [--run ID ...]                        # the table, from the committed snapshot
    python -m loop.trace snapshot --cadence ../cadence         # refresh citations.json from a cadence checkout

A finding cites a run in `run_ids` of findings.jsonl. A cadence commit cites a run with the trailer
`Evidence: <run id>` and names its finding with `Finding: F-n`. The snapshot (citations.json, at the
root) holds, per cited run, each citing commit: its sha, its findings, and its status. A commit on
main is `merged`, with the pull request and the merge commit that brought it (the first commit on
main's first-parent line that contains it; a squash merge is its own merge commit). A commit not on
main is `unmerged`, with the remote branches that hold it and its pull request number; whether that pull
request is open or closed is not in a checkout. The snapshot keeps shas, ids, numbers and branch
names, and no commit text.

What the snapshot walks is fixed, so two checkouts with the same refs give the same file: the main
ref and every ref under refs/remotes/origin/ (the branches and the pull-request heads), never a local
branch or a tag. The snapshot lists those refs (`refs`: name and sha) so the file states what it saw.
Fetch them with exactly:

    git fetch origin '+refs/heads/*:refs/remotes/origin/*' '+refs/pull/*/head:refs/remotes/origin/pr/*'

(`refs/pull/*/head` alone, without the destination, gives no origin/pr/<n> ref, and an unmerged
commit then has no pull request number.) A finding id a trailer names that has no row in findings.jsonl
is kept, and the table marks it `unfiled`.

The table covers every counted run, every run a finding cites, and every run a commit cites. A run
that none of these names is not in it. `--run` restricts the table to the runs given, and refuses a
run with no record.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from loop import findings, record

ROOT = Path(__file__).resolve().parents[1]
CITATIONS = ROOT / "citations.json"
SOURCE = "jtouley/cadence"
_EVIDENCE = re.compile(r"^Evidence:\s*(.+?)\s*$", re.M)
_FINDING = re.compile(r"^Finding:\s*(F-[1-9][0-9]*)\s*$", re.M)
_PR = re.compile(r"Merge pull request #(\d+)\b|\(#(\d+)\)\s*$")


class TraceError(Exception):
    pass


# --- trailers ------------------------------------------------------------------------------------------


def evidence_trailers(body: str) -> list[str]:
    """The run ids in a commit message's `Evidence:` trailers, in order; other evidence lines are left out."""
    return [v for v in _EVIDENCE.findall(body) if record.RUN_ID.fullmatch(v)]


def finding_trailers(body: str) -> list[str]:
    return _FINDING.findall(body)


def pr_number(subject: str) -> int | None:
    """The pull request a merge subject names: a merge commit's, or a squash merge's `(#n)`."""
    found = _PR.search(subject)
    return int(found.group(1) or found.group(2)) if found else None


# --- the cadence checkout ------------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    return proc.stdout if proc.returncode == 0 else ""


def walked_refs(cadence: Path, main: str) -> list[dict]:
    """The refs the snapshot walks: `main`, then every ref under refs/remotes/origin/, each with its sha."""
    refs = [{"name": main, "sha": _git(cadence, "rev-parse", main).strip()}]
    for line in _git(cadence, "for-each-ref", "--format=%(refname) %(objectname)", "refs/remotes/origin/").splitlines():
        full, _, sha = line.rpartition(" ")
        name = full.removeprefix("refs/remotes/")
        if name and name != main and full != "refs/remotes/origin/HEAD":
            refs.append({"name": name, "sha": sha})
    return refs


def citing_commits(cadence: Path, main: str = "origin/main") -> list[dict]:
    """Every commit reachable from the walked refs whose message cites a run: {sha, findings, run_ids}."""
    out = []
    names = [r["name"] for r in walked_refs(cadence, main)]
    for entry in _git(cadence, "log", "--format=%H%x00%B%x01", *names, "--").split("\x01"):
        sha, _, body = entry.strip().partition("\x00")
        run_ids = evidence_trailers(body) if sha else []
        if run_ids:
            out.append({"sha": sha, "findings": sorted(set(finding_trailers(body))), "run_ids": run_ids})
    return out


def first_parent(cadence: Path, main: str) -> list[tuple[str, str]]:
    """(sha, subject) of main's first-parent line, oldest first."""
    lines = _git(cadence, "log", "--first-parent", "--format=%H%x00%s", main).splitlines()
    return [tuple(line.split("\x00", 1)) for line in reversed(lines) if "\x00" in line]


def status_of(cadence: Path, sha: str, main: str, line: list[tuple[str, str]] | None = None) -> dict:
    """merged (pr, merge_sha) when `sha` is on main, else unmerged (pr from a fetched pull ref, branches)."""
    line = first_parent(cadence, main) if line is None else line
    if subprocess.run(["git", "merge-base", "--is-ancestor", sha, main], cwd=cadence, capture_output=True).returncode == 0:
        for merge_sha, subject in line:
            if subprocess.run(["git", "merge-base", "--is-ancestor", sha, merge_sha], cwd=cadence,
                              capture_output=True).returncode == 0:
                return {"status": "merged", "pr": pr_number(subject), "merge_sha": merge_sha}
        return {"status": "merged", "pr": None, "merge_sha": None}
    branches = sorted(b.strip() for b in _git(cadence, "branch", "-r", "--contains", sha, "--format=%(refname:short)")
                      .splitlines() if b.strip() and not b.strip().endswith("/HEAD") and b.strip() != "origin")
    prs = [int(b.rsplit("/pr/", 1)[1]) for b in branches if "/pr/" in b and b.rsplit("/pr/", 1)[1].isdigit()]
    return {"status": "unmerged", "pr": min(prs) if prs else None, "branches": branches}


def snapshot(cadence: Path, main: str = "origin/main") -> dict:
    """citations.json: per cited run, its citing commits with their status, from the checkout."""
    line = first_parent(cadence, main)
    citations: dict[str, list[dict]] = {}
    for commit in citing_commits(cadence, main):
        status = status_of(cadence, commit["sha"], main, line)
        for run_id in commit["run_ids"]:
            citations.setdefault(run_id, []).append({"sha": commit["sha"], "findings": commit["findings"], **status})
    for commits in citations.values():
        commits.sort(key=lambda c: (c["status"] != "merged", c["pr"] or 0, c["sha"]))
    return {"schema": 1, "source": SOURCE, "main": _git(cadence, "rev-parse", main).strip(),
            "refs": walked_refs(cadence, main), "citations": dict(sorted(citations.items()))}


def load_citations(path: Path = CITATIONS) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"citations": {}}


# --- the rows and the table ----------------------------------------------------------------------------


def rows(runs: Path, findings_path: Path, citations: dict, run_ids: list[str] | None = None) -> list[dict]:
    """One row per run: every counted run, every run a finding cites, every run a commit cites; or the
    runs given. {run_id, counts, findings: [F-n], commits: [snapshot entries]}."""
    by_finding: dict[str, list[str]] = {}
    known: set[str] = set()
    for row in findings.load(findings_path):
        known.add(row["id"])
        for rid in row["run_ids"]:
            by_finding.setdefault(rid, []).append(row["id"])
    cited = citations.get("citations", {})
    if run_ids is None:
        wanted = set(by_finding) | set(cited)
        wanted |= {p.name for p in runs.iterdir() if (p / "record.json").exists() and record.load(p)["counts"]["counts"]}
    else:
        wanted = set(run_ids)
    out = []
    for rid in sorted(wanted):
        if not (runs / rid / "record.json").exists():
            raise TraceError(f"no record for run {rid} in {runs}")
        commits = [{**c, "unfiled": sorted(f for f in c["findings"] if f not in known)} for c in cited.get(rid, [])]
        out.append({"run_id": rid, "counts": record.load(runs / rid)["counts"]["counts"],
                    "findings": sorted(by_finding.get(rid, []), key=lambda f: int(f[2:])), "commits": commits})
    return out


def _commit_text(c: dict) -> str:
    """One citing commit: sha, findings (an id with no findings.jsonl row says unfiled), pull request, status."""
    unfiled = set(c.get("unfiled", []))
    names = [f"{f} (unfiled)" if f in unfiled else f for f in c["findings"]]
    who = f"`{c['sha'][:7]}` ({', '.join(names) or 'no finding'})"
    pr = f"#{c['pr']}" if c.get("pr") else "no pull request named"
    if c["status"] == "merged":
        at = f" at `{c['merge_sha'][:7]}`" if c.get("merge_sha") else ""
        return f"{who} merged in {pr}{at}"
    on = ", ".join(b for b in c.get("branches", []) if "/pr/" not in b) or ", ".join(c.get("branches", [])) or "no branch"
    return f"{who} unmerged, {pr}{' open or closed' if c.get('pr') else ''}, on {on}"


def table(rows: list[dict]) -> str:
    lines = ["| Run | Counts | Findings | Cadence commits (finding, pull request, status) |", "|---|---|---|---|"]
    for r in rows:
        lines.append(f"| `{r['run_id']}` | {'yes' if r['counts'] else 'no'} | {', '.join(r['findings']) or '—'} | "
                     f"{'; '.join(_commit_text(c) for c in r['commits']) or '—'} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.trace", description=__doc__.split("\n\n")[0])
    ap.add_argument("action", nargs="?", choices=["table", "snapshot"], default="table")
    ap.add_argument("--run", action="append", help="restrict the table to this run (repeatable)")
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    ap.add_argument("--findings", type=Path, default=findings.FINDINGS)
    ap.add_argument("--citations", type=Path, default=CITATIONS)
    ap.add_argument("--cadence", type=Path, help="snapshot: a checkout of jtouley/cadence with main and the pull refs fetched")
    ap.add_argument("--main", default="origin/main", help="snapshot: the ref of cadence main (default origin/main)")
    args = ap.parse_args(argv)
    if args.action == "snapshot":
        if not args.cadence:
            ap.error("snapshot needs --cadence")
        data = snapshot(args.cadence, args.main)
        args.citations.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"{sum(len(v) for v in data['citations'].values())} citation(s) of {len(data['citations'])} run(s) "
              f"at {data['main'][:7]} -> {args.citations}")
        return 0
    try:
        print(table(rows(args.runs, args.findings, load_citations(args.citations), args.run)))
    except TraceError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
