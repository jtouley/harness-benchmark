#!/usr/bin/env python3
"""Review value: do review cycles raise new findings that turn out to be real defects?

Two inputs, either or both (stdlib only):

- a Cadence findings ledger (JSONL; one row per finding event, with id, stage, severity,
  class, status, evidence): metrics per stage;
- a folder of /pr-review reports, PR_REVIEW_#<n>.md: the first review is round 0, and
  each appended "## Update [...]" section is one more round: metrics per round.

Per stage or round it reports: findings raised; blocking findings; confirmed defects
(blocking findings later closed as fixed: ledger status "verified", or a later review
round marks the item resolved); new versus repeat; "fix-induced" findings (the text says
the item comes from an earlier fix); and, with a tokens CSV (stage,round,tokens), the
tokens spent per confirmed defect.

The output holds counts, stage names, PR numbers and normalized verdicts only. It never
copies finding text. Definitions and limits: docs/review-value.md.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

BLOCKING = "blocking"
SHOULD_FIX = "should_fix"
MINOR = "minor"

LEDGER_SEVERITY = {"must-fix": BLOCKING, "should-fix": SHOULD_FIX, "nit": MINOR}
REVIEW_SEVERITY = {"critical": BLOCKING, "required": BLOCKING, "must-fix": BLOCKING,
                   "should-fix": SHOULD_FIX, "optional": SHOULD_FIX, "nit": MINOR, "fyi": MINOR}

# A finding whose text says it comes from an earlier fix. A heuristic: see the docs.
FIX_INDUCED = re.compile(
    r"\bthe fix\b|\bfix commit\b|\bintroduced by\b|from my own earlier recommendation", re.IGNORECASE)

REQUIRED_KEYS = ("id", "stage", "severity", "status")


# --- Ledger -------------------------------------------------------------------------------


def read_ledger(path, with_skipped=False):
    """Rows of the JSONL ledger, in file order. Blank lines are ignored; rows that do not
    parse or miss a required key are skipped and counted."""
    rows, skipped = [], 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        if not isinstance(row, dict) or any(not row.get(k) for k in REQUIRED_KEYS):
            skipped += 1
            continue
        rows.append(row)
    return (rows, skipped) if with_skipped else rows


def _evidence_key(text):
    """Evidence with task ids (cd-47, gh-28) and finding ids taken out, to spot one
    boilerplate finding filed again for each task."""
    text = re.sub(r"\b[a-z]+-\d+(?:-f\d+)?\b", "<id>", (text or "").lower())
    return " ".join(text.split())


def _fix_induced(*texts):
    return any(FIX_INDUCED.search(t or "") for t in texts)


def read_tokens(path):
    """{(stage, round): tokens} from a CSV with the columns stage, round and tokens."""
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = {"stage", "round", "tokens"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"tokens CSV misses column(s): {', '.join(sorted(missing))}")
        out = {}
        for rec in reader:
            key = ((rec["stage"] or "").strip(), (rec["round"] or "").strip())
            try:
                value = int(float(rec["tokens"]))
            except (TypeError, ValueError):
                raise ValueError(f"tokens CSV line {reader.line_num}: tokens is not a number") from None
            out[key] = out.get(key, 0) + value
        return out


def _add_cost(row, tokens):
    """tokens None means the CSV has no row for it: the cost is unknown, never zero."""
    row["tokens"] = tokens
    row["tokens_per_confirmed_defect"] = (tokens / row["confirmed_defects"]
                                          if tokens is not None and row["confirmed_defects"] else None)


def _stage_tokens(tokens, stage):
    values = [v for (st, _), v in tokens.items() if st == stage]
    return sum(values) if values else None


def ledger_metrics(rows, tokens=None):
    final_status = {r["id"]: r["status"] for r in rows}
    pairs = {}  # (stage, id) -> last row of that pair, in first-seen order
    for r in rows:
        pairs[(r["stage"], r["id"])] = r
    stages, seen_ids, seen_text = {}, set(), set()
    for (stage, fid), r in pairs.items():
        s = stages.setdefault(stage, {"stage": stage, "raised": 0, "blocking": 0, "should_fix": 0,
                                      "confirmed_defects": 0, "new": 0, "repeat_id": 0, "repeat_text": 0,
                                      "fix_induced": 0, "status": Counter()})
        sev = LEDGER_SEVERITY.get(str(r["severity"]).lower(), MINOR)
        status = final_status[fid]
        s["raised"] += 1
        s["blocking"] += sev == BLOCKING
        s["should_fix"] += sev == SHOULD_FIX
        s["confirmed_defects"] += sev == BLOCKING and status == "verified"
        s["status"][status] += 1
        s["fix_induced"] += _fix_induced(r.get("evidence"), r.get("note"))
        key = _evidence_key(r.get("evidence"))
        if fid in seen_ids:
            s["repeat_id"] += 1
        elif key and key in seen_text:
            s["repeat_text"] += 1
        else:
            s["new"] += 1
        seen_ids.add(fid)
        seen_text.add(key)
    out = []
    for s in stages.values():
        s["status"] = dict(s["status"])
        if tokens is not None:
            _add_cost(s, _stage_tokens(tokens, s["stage"]))
        out.append(s)
    finals = {}
    for r in rows:
        finals[r["id"]] = r
    totals = {"raised": len(finals),
              "blocking": sum(LEDGER_SEVERITY.get(str(r["severity"]).lower()) == BLOCKING for r in finals.values()),
              "confirmed_defects": sum(LEDGER_SEVERITY.get(str(r["severity"]).lower()) == BLOCKING
                                       and r["status"] == "verified" for r in finals.values())}
    return {"stages": out, "totals": totals}


# --- PR review reports --------------------------------------------------------------------

REPORT_NAME = re.compile(r"^PR_REVIEW_#(\d+)\.md$")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
FINDING = re.compile(
    r"^\s*(?:#{2,4}\s+)?(?:[-*]\s+)?(?:(?P<num>\d+)\.\s+)?(?:\*\*)?\s*"
    r"(?:(?P<label>§?\d+\.\d+|[A-Z]{1,3}-?\d+|[A-Z](?=\.))\.?\s*)?(?:\*\*)?\s*(?:[—–-]+\s*)?"
    r"(?:`?\[(?P<tag>[VLIU])\]`?\s*)?(?:\*\*)?\s*(?:[—–-]+\s*)?"
    r"(?P<sev>(?i:critical|required|must-fix|should-fix|optional|nit|fyi))\b(?P<rest>.*)$")
# A status item's id is read only from the start of its header, so "nit (see F1)" is not F1.
STATUS_LABEL = re.compile(r"^(?:original\s+(?:issue\s+|required\s+)?)?"
                          r"(#\d+|§?\d+\.\d+|[A-Z]{1,3}-?\d+\b|[A-Z](?=[\s.:]|$))", re.IGNORECASE)
STATUS_MARK = re.compile(r"✅|⚠️|⚠|❌")
LEVEL_WORDS = re.compile(r"\b(?:guardrail|patch|architecture)-level\b", re.IGNORECASE)

# Sections whose numbered or bold lines are not findings raised in this round.
EXCLUDED = ("dropped", "inline comments", "recommendation", "verification checklist", "spec-driven proof",
            "summary", "proof the review", "witnesses", "files in the worktree", "three fixes", "spike files",
            "new commits", "github feedback", "verdict")
STATUS = ("previous issues", "status of", "status update")


def _norm_label(label):
    return label.replace("§", "").replace("-", "") if label else None


def status_label(header):
    """The id at the start of a status item's header, normalized; None when it has none."""
    m = STATUS_LABEL.match(header.strip())
    return _norm_label(m.group(1)) if m else None


def _resolved(text):
    """The first status marker in the item decides: ✅ resolved, ⚠️ partial, ❌ open."""
    m = STATUS_MARK.search(text)
    return bool(m) and m.group(0) == "✅"


def parse_finding_line(line):
    """{label, severity, title} when the line opens a finding, else None. A finding line
    carries an evidence tag ([V], [L], [I] or [U]) and then a severity word."""
    m = FINDING.match(line)
    if not m or not m["tag"]:
        return None
    label = f"#{m['num']}" if m["num"] else _norm_label(m["label"])
    title = LEVEL_WORDS.sub("", m["rest"].split("**")[0])
    title = " ".join(re.sub(r"[^a-z0-9 ]", " ", title.lower()).split())[:60]
    return {"label": label, "severity": REVIEW_SEVERITY[m["sev"].lower()], "title": title}


_VERDICT_LINE = re.compile(r"^\s*(?:\*\*)?(?:re-review\s+)?verdict\s*(?:\*\*)?\s*:\s*(?:\*\*)?\s*(.*)$",
                           re.IGNORECASE)
_VERDICT_HEADING = re.compile(r"^#{2,4}\s+verdict\b", re.IGNORECASE)


def _normalize_verdict(text):
    t = text.replace("*", "").strip().upper()
    if "REQUEST CHANGES" in t:
        return "REQUEST CHANGES"
    if t.startswith("APPROVE WITH NITS"):
        return "APPROVE WITH NITS"
    if t.startswith("APPROVE WITH"):
        return "APPROVE WITH CONDITIONS"
    if t.startswith("APPROVE") or "MERGE-READY" in t or "READY TO MERGE" in t:
        return "APPROVE"
    return "OTHER"


def parse_verdict(text):
    """The last verdict in the text, normalized; None when there is none."""
    found, lines = None, text.splitlines()
    for i, line in enumerate(lines):
        cand = None
        if _VERDICT_HEADING.match(line):
            cand = ""
        else:
            m = _VERDICT_LINE.match(line)
            if m:
                cand = m.group(1)
        if cand is None:
            continue
        if not cand.strip():
            cand = next((ln for ln in lines[i + 1:] if ln.strip()), "")
        found = _normalize_verdict(cand)
    return found


def _split_rounds(text):
    parts = re.split(r"(?m)^(?=## Update\b)", text)
    return parts


def read_reviews(folder):
    """Reports named PR_REVIEW_#<n>.md, sorted by PR number; other files are ignored."""
    out = []
    for p in Path(folder).iterdir():
        m = REPORT_NAME.match(p.name)
        if m and p.is_file():
            out.append({"pr": int(m.group(1)), "rounds": _split_rounds(p.read_text(encoding="utf-8"))})
    return sorted(out, key=lambda r: r["pr"])


def _parse_round(text):
    """Findings raised and status items in one round."""
    findings, status_items, stack = [], [], []
    current, section = None, None
    for line in text.splitlines():
        h = HEADING.match(line)
        if h:
            level = len(h.group(1))
            stack = [(lv, t) for lv, t in stack if lv < level] + [(level, h.group(2).lower())]
            current = None
            if level == 2:
                sec = re.match(r"(\d+)\.\s", h.group(2))
                section = sec.group(1) if sec else None
        titles = [t for lv, t in stack if lv >= 2]  # the H1 is the report title, not a section
        in_status = any(k in t for t in titles for k in STATUS)
        excluded = in_status or any(k in t for t in titles for k in EXCLUDED)
        if in_status:
            if re.match(r"\s*(?:[-*]\s+)?\*\*", line):
                header = re.sub(r"^\s*[-*]\s+", "", line).replace("*", "").strip()
                status_items.append({"label": status_label(header), "header": header, "text": line})
            elif status_items and not h:
                status_items[-1]["text"] += "\n" + line
            continue
        if excluded:
            continue
        f = parse_finding_line(line)
        if f:
            f["body"] = line
            f["labels"] = {f["label"]}
            if section and f["label"] and f["label"].startswith("#"):
                f["labels"].add(f"{section}.{f['label'][1:]}")
            findings.append(f)
            current = f
        elif current is not None and not h:
            current["body"] += "\n" + line
    return findings, status_items


def _blank_round(pr, idx):
    return {"pr": pr, "round": idx, "kind": None, "verdict": None, "raised": 0, "blocking": 0,
            "should_fix": 0, "new": 0, "repeat": 0, "fix_induced": 0, "resolved_confirmed": 0,
            "confirmed_defects": 0}


def review_metrics(reports, tokens=None):
    rounds = []
    for rep in reports:
        pr, parsed, seen_titles, credited = rep["pr"], [], set(), set()
        pr_rounds = []
        for idx, text in enumerate(rep["rounds"]):
            findings, items = _parse_round(text)
            r = _blank_round(pr, idx)
            r["verdict"] = parse_verdict(text)
            for f in findings:
                r["raised"] += 1
                r["blocking"] += f["severity"] == BLOCKING
                r["should_fix"] += f["severity"] == SHOULD_FIX
                r["fix_induced"] += _fix_induced(f["body"])
                if f["title"] and f["title"] in seen_titles:
                    r["repeat"] += 1
                else:
                    r["new"] += 1
            seen_titles.update(f["title"] for f in findings if f["title"])
            for it in items:
                if not _resolved(it["text"]):
                    continue
                r["resolved_confirmed"] += 1
                # Credit the round that raised this label most recently, if it was blocking there.
                origin = next((j for j in range(idx - 1, -1, -1)
                               if any(it["label"] in f["labels"] for f in parsed[j])), None) if it["label"] else None
                if origin is not None:
                    blocking = any(it["label"] in f["labels"] and f["severity"] == BLOCKING for f in parsed[origin])
                else:
                    origin = idx - 1 if idx > 0 else None
                    blocking = bool(re.search(r"\b(?:required|critical|must-fix)\b", it["header"], re.IGNORECASE))
                key = (origin, it["label"] or it["header"].strip())
                if origin is not None and blocking and key not in credited:
                    credited.add(key)
                    pr_rounds[origin]["confirmed_defects"] += 1
            parsed.append(findings)
            pr_rounds.append(r)
        for r in pr_rounds:
            r["kind"] = "new" if r["new"] else ("confirm-only" if r["resolved_confirmed"] or r["repeat"] else "empty")
            if tokens is not None:
                _add_cost(r, tokens.get((f"PR#{pr}", str(r["round"]))))
        rounds.extend(pr_rounds)
    return {"rounds": rounds, "by_round": _by_round(rounds)}


def _by_round(rounds):
    """Totals by round index (0 = first review; "3+" holds round 3 and later)."""
    order = ["0", "1", "2", "3+"]
    out = {}
    for r in rounds:
        key = order[min(r["round"], 3)]
        agg = out.setdefault(key, {"round": key, "rounds": 0, "raised": 0, "blocking": 0, "new": 0,
                                   "confirmed_defects": 0, "fix_induced": 0, "confirm_only_rounds": 0})
        agg["rounds"] += 1
        for k in ("raised", "blocking", "new", "confirmed_defects", "fix_induced"):
            agg[k] += r[k]
        agg["confirm_only_rounds"] += r["kind"] == "confirm-only"
    return [out[k] for k in order if k in out]


# --- Report -------------------------------------------------------------------------------


def _table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join("" if v is None else (f"{v:,.0f}" if isinstance(v, float) else str(v))
                                for v in row) + " |" for row in rows]
    return "\n".join(lines)


def _cost_cells(row):
    if row["tokens"] is None:
        return ["unknown", "unknown"]
    return [row["tokens"], row["tokens_per_confirmed_defect"] if row["tokens_per_confirmed_defect"] is not None else "-"]


def render_markdown(result):
    parts = []
    ledger = result.get("ledger")
    if ledger:
        cost = any("tokens" in s for s in ledger["stages"])
        head = ["stage", "raised", "blocking", "should-fix", "confirmed defects", "new", "repeat id",
                "repeat text", "fix-induced"] + (["tokens", "tokens / confirmed"] if cost else [])
        rows = [[s["stage"], s["raised"], s["blocking"], s["should_fix"], s["confirmed_defects"], s["new"],
                 s["repeat_id"], s["repeat_text"], s["fix_induced"]]
                + (_cost_cells(s) if cost else []) for s in ledger["stages"]]
        t = ledger["totals"]
        parts.append("## Findings ledger, per stage\n\n" + _table(head, rows)
                     + f"\n\nUnique ids: {t['raised']}; blocking: {t['blocking']}; "
                       f"confirmed defects: {t['confirmed_defects']}; "
                       f"skipped rows: {ledger.get('skipped_rows', 0)}.")
    reviews = result.get("reviews")
    if reviews:
        cost = any("tokens" in r for r in reviews["rounds"])
        head = ["PR", "round", "verdict", "raised", "blocking", "should-fix", "new", "repeat", "fix-induced",
                "resolved (confirmed here)", "confirmed defects", "kind"] + (
            ["tokens", "tokens / confirmed"] if cost else [])
        rows = [[f"#{r['pr']}", r["round"], r["verdict"] or "-", r["raised"], r["blocking"], r["should_fix"],
                 r["new"], r["repeat"], r["fix_induced"], r["resolved_confirmed"], r["confirmed_defects"],
                 r["kind"]] + (_cost_cells(r) if cost else [])
                for r in reviews["rounds"]]
        parts.append("## PR review rounds\n\n" + _table(head, rows))
        head = ["round", "rounds", "raised", "blocking", "new", "confirmed defects", "fix-induced",
                "confirm-only rounds"]
        rows = [[a["round"], a["rounds"], a["raised"], a["blocking"], a["new"], a["confirmed_defects"],
                 a["fix_induced"], a["confirm_only_rounds"]] for a in reviews["by_round"]]
        parts.append("## PR review rounds, by round index\n\n" + _table(head, rows))
    return "\n\n".join(parts) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--findings", type=Path, help="Cadence findings ledger (JSONL)")
    ap.add_argument("--reviews", type=Path, help="folder of PR_REVIEW_#<n>.md reports")
    ap.add_argument("--tokens", type=Path, help="optional CSV: stage,round,tokens (reviews: stage PR#<n>)")
    ap.add_argument("--json", type=Path, help="write the JSON result here")
    ap.add_argument("--markdown", type=Path, help="write the Markdown tables here (default: stdout)")
    args = ap.parse_args(argv)
    if not args.findings and not args.reviews:
        ap.error("give --findings, --reviews, or both")
    tokens = read_tokens(args.tokens) if args.tokens else None
    result = {}
    if args.findings:
        rows, skipped = read_ledger(args.findings, with_skipped=True)
        result["ledger"] = ledger_metrics(rows, tokens)
        result["ledger"]["skipped_rows"] = skipped
    if args.reviews:
        result["reviews"] = review_metrics(read_reviews(args.reviews), tokens)
    if args.json:
        args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    md = render_markdown(result)
    if args.markdown:
        args.markdown.write_text(md, encoding="utf-8")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
