"""Auditability: what a run left that a reader can check, computed by code from its stored record, bundle and
transcript, for every arm (owner, 2026-10-25: "Commiting not being asked for is exactly the point, the fact
that cadence does abd all of it is auditable is all a huge selling point").

    python -m loop.audit --store ../runs-store [--runs runs] [--run RUN_ID]          # print the table
    python -m loop.audit --store ../runs-store --write                               # write runs/<id>/audit.json
    python -m loop.audit --store ../runs-store --check                               # recompute, compare, exit 1

It is reported beside the grader score (scoreboard.md, the batch postmortems) and never changes it. No model
reads anything: every component is a fixed rule over the stored bytes. Five components, each present, absent,
or unread (its blob is in a store that was not given):

1. committed_history: the tree bundle holds at least one commit the agent made: a commit reachable from the
   bundle's refs, other than refs/graded/*, whose author is not the starting repository's (loop.graded
   SETUP_AUTHORS). Committing is not asked for in any arm (criteria-v2 §2.3).
2. pr_description: the transcript shows a pull request with a description. Either a local PR, the file
   `.context/prs/PR-<id>.md` that Cadence's E4 writes when no tracker is set (a Write, or a shell heredoc,
   that succeeded), with a title line and at least one non-blank line of body; or a `gh pr create` call with
   `--body`/`--body-file` whose result names a `/pull/<n>` URL.
3. decisions: a record of decisions or assumptions. A file named DECISIONS or ASSUMPTIONS (any extension), or
   one under an `adr/` or `decisions/` folder, with a non-blank line beyond its headings, in the agent's
   committed history or written during the run (transcript); or a document written during the run with a
   heading that names assumptions, decisions or trade-offs, followed by a non-blank line. Pipeline tasks P1
   and P2 ask every arm for DECISIONS.md, so on those tasks this component is prompted; the others are not.
4. gate_evidence: a gate's verdict recorded in the transcript: a line `OK|PASS|FAIL|BLOCKED  <name>-gate...`
   (the verdict format of Cadence's stages.json gate scripts) at the start of a line of a Bash call's result.
   A failing verdict is evidence too. An arm with no gates has none.
5. regradable: the bundle is in the store with the bytes the record names, and it holds refs/graded/<run_id>
   at the commit the grader graded (loop.graded.problem is None), so the graded work can be graded again.

A blob the record never kept makes its components absent (nothing to audit). A blob in another store
(the live runs keep theirs in jtouley/cadence) makes them unread unless --extra-store maps that store.
`present` is the count of present components out of five.

runs/<id>/audit.json holds the result, written by this module only (`--write`, and loop.driver for a new
run). loop.check refuses a record with no audit.json, one of another MEASURE, or one whose inputs are not the
record's blobs; `--check` recomputes every file from the store and refuses a difference.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

from loop import graded, record, store

ROOT = Path(__file__).resolve().parents[1]
MEASURE = 1  # bump when a component's rule changes; every audit.json is then written again
COMPONENTS = ("committed_history", "pr_description", "decisions", "gate_evidence", "regradable")
LABELS = {"committed_history": "Commits", "pr_description": "PR", "decisions": "Decisions",
          "gate_evidence": "Gates", "regradable": "Regradable"}

LOCAL_PR = re.compile(r"(?:^|/)\.context/prs/PR-[^/]+\.md$")
DECISION_FILE = re.compile(r"(?i)(?:^|/)(?:(?:decisions|assumptions)(?:\.[a-z0-9]+)?|(?:adr|decisions)/[^/]+\.md)$")
DECISION_HEADING = re.compile(r"(?i)^#{1,6}\s.*\b(?:assumptions?|decisions?|trade-?offs?)\b")
GATE_VERDICT = re.compile(r"(?m)^[ \t]*(OK|PASS|FAIL|BLOCKED)[ \t]+([a-z0-9][a-z0-9-]*-gate[a-z0-9-]*)\b")
PULL_URL = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/pull/\d+")
HEREDOC = re.compile(r"<<-?[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
REDIRECT = re.compile(r"(?<![0-9&<>])(>>?)[ \t]*(['\"]?)([^\s'\"<>|;&()]+)\2")


# --- the stored blobs

def _root(blob: dict, roots: dict[str, Path]) -> tuple[Path | None, str | None, bool]:
    """(the blob's local path, why not, whether it is unread rather than absent)."""
    if not blob or not blob.get("sha256"):
        return None, f"not stored ({(blob or {}).get('missing') or 'no blob'})", False
    root = roots.get(blob.get("store", ""))
    if root is None:
        return None, f"stored in {blob.get('store')}, which was not read", True
    if not store.verify(blob, root):
        return None, f"{blob.get('path')} is not in {blob.get('store')} with the recorded bytes", False
    return root / blob["path"], None, False


def _lines(path: Path):
    with open(path, "rb") as f:
        gz = f.read(2) == b"\x1f\x8b"
    opener = gzip.open if gz else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as f:
        yield from f


# --- the transcript

def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(c.get("text", "") for c in content if isinstance(c, dict) and isinstance(c.get("text"), str))
    return ""


def _events(lines):
    """(tool uses in order, {tool_use_id: (result text, is_error)}, session cwd) of a stream-json transcript."""
    uses, results, cwd = [], {}, None
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "system" and event.get("subtype") == "init" and cwd is None:
            cwd = event.get("cwd")
        message = event.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and isinstance(block.get("input"), dict):
                uses.append(block)
            elif block.get("type") == "tool_result":
                results[block.get("tool_use_id")] = (_text(block.get("content")), bool(block.get("is_error")))
    return uses, results, cwd


def heredoc_writes(command: str) -> list[tuple[str, str, bool]]:
    """(path, body, append) for each `... > path <<EOF` (or `<<EOF > path`) heredoc in a shell command."""
    out, lines, i = [], command.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        doc = HEREDOC.search(line)
        if not doc:
            i += 1
            continue
        delim = doc.group(2)
        end = next((j for j in range(i + 1, len(lines)) if lines[j].strip() == delim), len(lines))
        body = "\n".join(lines[i + 1:end])
        target = REDIRECT.search(HEREDOC.sub(" ", line))
        if target:
            out.append((target.group(3), body, target.group(1) == ">>"))
        i = end + 1
    return out


def _rel(path: str, cwd: str | None) -> str:
    if cwd and path.startswith(cwd.rstrip("/") + "/"):
        return path[len(cwd.rstrip("/")) + 1:]
    return path


def written_files(uses: list[dict], results: dict, cwd: str | None) -> dict[str, str | None]:
    """{path: its last content, or None when an edit hit a file whose content the transcript does not hold} of
    every file the run wrote with a tool call that did not fail: Write, Edit, and shell heredocs."""
    files: dict[str, str | None] = {}
    for use in uses:
        if results.get(use.get("id"), ("", False))[1]:
            continue
        name, args = use.get("name"), use["input"]
        if name == "Write" and isinstance(args.get("file_path"), str):
            files[_rel(args["file_path"], cwd)] = str(args.get("content") or "")
        elif name in ("Edit", "MultiEdit") and isinstance(args.get("file_path"), str):
            path = _rel(args["file_path"], cwd)
            text = files.get(path)
            edits = args.get("edits") if name == "MultiEdit" else [args]
            for edit in edits if isinstance(edits, list) else []:
                if text is not None and isinstance(edit, dict) and isinstance(edit.get("old_string"), str):
                    new = str(edit.get("new_string") or "")
                    text = text.replace(edit["old_string"], new) if edit.get("replace_all") else \
                        text.replace(edit["old_string"], new, 1)
            files[path] = text
        elif name == "Bash" and isinstance(args.get("command"), str):
            for path, body, append in heredoc_writes(args["command"]):
                path = _rel(path, cwd)
                before = files.get(path, "") if append else ""
                files[path] = None if before is None else before + body + "\n"
    return files


def _has_body(text: str | None) -> bool:
    """A non-blank line that is not a heading."""
    return text is not None and any(line.strip() and not line.lstrip().startswith("#") for line in text.splitlines())


def _heading_with_body(text: str) -> str | None:
    """The first heading that names assumptions, decisions or trade-offs and has a non-blank line under it."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if DECISION_HEADING.match(line.strip()):
            for after in lines[i + 1:]:
                if after.lstrip().startswith("#"):
                    break
                if after.strip():
                    return line.strip()
    return None


def _flags(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def pr_from(uses: list[dict], results: dict, files: dict) -> dict:
    local = sorted(p for p, text in files.items() if LOCAL_PR.search(p) and text is not None
                   and (body := [line for line in text.splitlines() if line.strip()]) and len(body) >= 2)
    hosted = []
    for use in uses:
        if use.get("name") != "Bash" or "gh pr create" not in str(use["input"].get("command", "")):
            continue
        out, error = results.get(use.get("id"), ("", True))
        words = _flags(use["input"]["command"])
        described = any(w in ("--body", "-b", "--body-file", "-F") or w.startswith(("--body=", "--body-file="))
                        for w in words)
        url = PULL_URL.search(out)
        if described and url and not error:
            hosted.append(url.group(0))
    if local or hosted:
        return {"present": True, "local": local, "hosted": sorted(set(hosted))}
    return {"present": False, "why": "no PR file with a title and body under .context/prs/, and no gh pr create "
                                     "with a body that returned a pull URL"}


def decisions_written(files: dict) -> list[str]:
    found = []
    for path, text in sorted(files.items()):
        if text is None:
            continue
        if (DECISION_FILE.search(path) and _has_body(text)) or (path.endswith(".md") and _heading_with_body(text)):
            found.append(path)
    return found


def gates_from(uses: list[dict], results: dict) -> dict:
    verdicts: dict[str, dict[str, int]] = {}
    for use in uses:
        if use.get("name") != "Bash":
            continue
        for match in GATE_VERDICT.finditer(results.get(use.get("id"), ("", False))[0]):
            seen = verdicts.setdefault(match.group(2), {})
            seen[match.group(1)] = seen.get(match.group(1), 0) + 1
    if not verdicts:
        return {"present": False, "why": "no gate verdict line in any Bash result"}
    total = sum(n for v in verdicts.values() for n in v.values())
    passed = sum(v.get("OK", 0) + v.get("PASS", 0) for v in verdicts.values())
    return {"present": True, "gates": sorted(verdicts), "verdicts": total, "pass": passed, "fail": total - passed}


# --- the bundle

def _git(cwd: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    proc = subprocess.run([*graded.SAFE_GIT, *args], cwd=cwd, env=env, capture_output=True, text=True,
                          errors="replace", check=False)
    if proc.returncode != 0:
        raise graded.GradedError(f"git {' '.join(args[:2])}: {proc.stderr.strip()[-200:]}")
    return proc.stdout


def bundle_facts(path: Path) -> dict:
    """The agent's commits (not the starting repository's, not refs/graded/*) and the decision files they
    hold, from a tree bundle (plain or gzipped)."""
    with tempfile.TemporaryDirectory() as tmp:
        mirror = Path(tmp) / "m.git"
        _git(Path(tmp), "clone", "-q", "--mirror", str(graded._plain(path, Path(tmp))), str(mirror))
        log = _git(mirror, "log", "--exclude=refs/graded/*", "--all", "--format=%H%x00%an")
        agent = [sha for sha, author in (line.split("\x00", 1) for line in log.splitlines() if "\x00" in line)
                 if author not in graded.SETUP_AUTHORS]
        files: dict[str, str] = {}  # decision file -> the newest agent commit that touches it
        for sha in agent:  # newest first (git log order)
            for name in _git(mirror, "show", "--no-renames", "--name-only", "--format=", sha).splitlines():
                if name and DECISION_FILE.search(name) and name not in files:
                    files[name] = sha
        kept = []
        for name, sha in sorted(files.items()):
            try:
                text = _git(mirror, "show", f"{sha}:{name}")
            except graded.GradedError:
                continue  # deleted by that commit
            if _has_body(text):
                kept.append(name)
    return {"agent_commits": len(agent), "decision_files": kept}


# --- the measure

def _unread(why: str) -> dict:
    return {"present": None, "why": why}


def _absent(why: str) -> dict:
    return {"present": False, "why": why}


def compute(rec: dict, roots: dict[str, Path]) -> dict:
    """The audit of one record, from the blobs under `roots` ({store id: checkout})."""
    tpath, twhy, tunread = _root(rec.get("transcript") or {}, roots)
    bpath, bwhy, bunread = _root(rec.get("tree") or {}, roots)
    comp: dict[str, dict] = {}

    facts = None
    if bpath is not None:
        try:
            facts = bundle_facts(bpath)
        except graded.GradedError as exc:
            bwhy = f"the bundle cannot be read: {exc}"
    if facts is not None:
        n = facts["agent_commits"]
        comp["committed_history"] = {"present": True, "commits": n} if n else _absent("the bundle holds only the "
                                                                                      "starting repository")
    else:
        comp["committed_history"] = _unread(f"bundle {bwhy}") if bunread else _absent(f"bundle {bwhy}")

    if tpath is not None:
        uses, results, cwd = _events(_lines(tpath))
        files = written_files(uses, results, cwd)
        comp["pr_description"] = pr_from(uses, results, files)
        written = decisions_written(files)
        gates = gates_from(uses, results)
    else:
        why = f"transcript {twhy}"
        comp["pr_description"] = _unread(why) if tunread else _absent(why)
        written, gates = None, (_unread(why) if tunread else _absent(why))

    committed = (facts or {}).get("decision_files") or []
    if committed or written:
        comp["decisions"] = {"present": True, "committed": committed, "written": written or []}
    elif (facts is None and bunread) or (written is None and tunread):
        comp["decisions"] = _unread("a blob was not read")
    else:
        comp["decisions"] = _absent("no decisions or assumptions record in the bundle's commits or the transcript")
    comp["gate_evidence"] = gates

    if bpath is None:
        comp["regradable"] = _unread(f"bundle {bwhy}") if bunread else _absent(f"bundle {bwhy}")
    else:
        root = roots[rec["tree"]["store"]]
        why = graded.problem(rec, root)
        comp["regradable"] = _absent(why) if why else {"present": True, "ref": graded.ref(rec["run_id"])}

    return {"measure": MEASURE, "run_id": rec["run_id"],
            "inputs": {"transcript": (rec.get("transcript") or {}).get("sha256"),
                       "tree": (rec.get("tree") or {}).get("sha256")},
            "components": comp,
            "present": sum(1 for c in comp.values() if c["present"] is True),
            "unread": sum(1 for c in comp.values() if c["present"] is None)}


def dump(audit: dict) -> str:
    return json.dumps(audit, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def write(run: Path, audit: dict) -> Path:
    path = run / "audit.json"
    path.write_text(dump(audit), encoding="utf-8")
    return path


def load(run: Path) -> dict | None:
    path = run / "audit.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


# --- reading it

def mark(audit: dict | None, name: str) -> str:
    """yes / no / ? for one component."""
    if audit is None:
        return "—"
    got = audit["components"][name]["present"]
    return "?" if got is None else "yes" if got else "no"


def score_text(audit: dict | None) -> str:
    """`k/5`, with the unread components named when there are any."""
    if audit is None:
        return "—"
    text = f"{audit['present']}/{len(COMPONENTS)}"
    return text + (f" ({audit['unread']} unread)" if audit["unread"] else "")


def cell(audit: dict | None, name: str) -> str:
    """One component for a table: yes with its count where it has one, no, or ?."""
    text = mark(audit, name)
    if text != "yes":
        return text
    got = audit["components"][name]
    if name == "committed_history":
        return f"yes ({got['commits']})"
    if name == "gate_evidence":
        return f"yes ({got['verdicts']}: {got['pass']} pass, {got['fail']} fail)"
    if name == "decisions":
        return "yes (committed)" if got["committed"] else "yes (written, not committed)"
    if name == "pr_description":
        return "yes (hosted)" if got["hosted"] else "yes (local)"
    return text


def problems(runs: Path) -> list[str]:
    """Records with no audit.json, or one that is not this measure's, or not of the record's blobs. Whether
    each file is what the code computes needs the store: python -m loop.audit --store ../runs-store --check."""
    out = []
    if not runs.is_dir():
        return out
    for run in sorted(p for p in runs.iterdir() if (p / "record.json").is_file()):
        rec = record.load(run)
        try:
            got = load(run)
        except ValueError as exc:
            out.append(f"{run.name}/audit.json: {exc}")
            continue
        if got is None:
            out.append(f"{run.name}: no audit.json (python -m loop.audit --store ../runs-store --write --run {run.name})")
            continue
        want = {"transcript": (rec.get("transcript") or {}).get("sha256"), "tree": (rec.get("tree") or {}).get("sha256")}
        if got.get("measure") != MEASURE:
            out.append(f"{run.name}/audit.json: measure {got.get('measure')!r}, not {MEASURE}")
        if got.get("run_id") != run.name:
            out.append(f"{run.name}/audit.json: run_id {got.get('run_id')!r} is not the folder name")
        if got.get("inputs") != want:
            out.append(f"{run.name}/audit.json: its inputs are not the record's transcript and tree")
        comp = got.get("components") or {}
        if sorted(comp) != sorted(COMPONENTS) or any(c.get("present") not in (True, False, None) for c in comp.values()):
            out.append(f"{run.name}/audit.json: components must be {', '.join(COMPONENTS)}, each present true, false or null")
        elif got.get("present") != sum(1 for c in comp.values() if c["present"] is True) or \
                got.get("unread") != sum(1 for c in comp.values() if c["present"] is None):
            out.append(f"{run.name}/audit.json: present or unread does not match its components")
    return out


def _roots(store_root: Path, extra: list[str]) -> dict[str, Path]:
    roots = {store.STORE: store_root}
    for item in extra:
        name, _, path = item.rpartition("=")
        if not name:
            raise SystemExit(f"--extra-store takes STORE=PATH, not {item!r}")
        roots[name] = Path(path)
    return roots


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m loop.audit", description=__doc__.split("\n\n")[0])
    ap.add_argument("--store", type=Path, required=True, help="a checkout of the runs-store branch")
    ap.add_argument("--extra-store", action="append", default=[], metavar="STORE=PATH",
                    help="another store a record names (its `store` value) and a checkout of it")
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    ap.add_argument("--run", help="this run only")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write runs/<id>/audit.json")
    mode.add_argument("--check", action="store_true", help="refuse an audit.json that is not what this computes")
    args = ap.parse_args(argv)
    roots = _roots(args.store, args.extra_store)
    bad = 0
    print("| Run | Arm | Audit | " + " | ".join(LABELS[c] for c in COMPONENTS) + " |")
    for run in sorted(p for p in args.runs.iterdir() if (p / "record.json").is_file()):
        if args.run and run.name != args.run:
            continue
        rec = record.load(run)
        got = compute(rec, roots)
        if args.write:
            write(run, got)
        elif args.check and load(run) != json.loads(dump(got)):
            bad += 1
            print(f"{run.name}/audit.json: not what loop.audit computes from the store", file=sys.stderr)
        print(f"| {run.name} | {rec['arm']} | {score_text(got)} | " + " | ".join(cell(got, c) for c in COMPONENTS) + " |")
    if args.check:
        print(f"{bad} audit file(s) differ", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
