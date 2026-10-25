"""Tag each dispatched prompt by the signals this audit counts. Heuristic: regexes, not judgment.

usage: python3 -I bin/tag_prompts.py dispatched-prompts-2026-10-25.md [first_prompt_number]
Prints one line per prompt with any tag, then counts. Every count in README.md that says "regex" comes from here;
each finding in README.md was then read by hand, and the regex false positives it names are excluded there.
"""
import re
import sys

TAGS = {
    "TRAP": r"\bF5\b|\btrap F5|frame at 5896|5895 of 11774|\bbad 1\b|malformed frame|truncated frame",
    "ANSWER": r"where the answer was|where it was 60|answer was 1122",
    "ORACLE": r"oracle_map",
    "EXPECT": r"must FAIL|must PASS|must match the recorded|should come out|true score|7/7 on the same|strongest run|must now catch",
    "VERIFIED": r"\(verified|verified by a|all verified earlier|Bug \(verified\)",
    "MERGE_OWN": r"merge (it|that) with the GitHub merge tool|merge it with the GitHub merge tool|You may now merge|merge it once|merge that once|If it's mergeable \(clean\), merge",
    "DOC_UNPINNED": r"WbaPy7W4Qc2EZL9R68B1oA|eface3ec-ac42",
    "SHA256_PIN": r"sha256",
    "SLASH_FIRST": None,
}


def prompts(text):
    parts = re.split(r"(?m)^## (\d+)\. (\S+) (\S+) ?(.*)$", text)
    for i in range(1, len(parts), 5):
        body = parts[i + 4]
        m = re.search(r"```\n(.*?)```", body, re.S)
        yield int(parts[i]), parts[i + 2], parts[i + 3].strip(), (m.group(1) if m else body)


def main():
    text = open(sys.argv[1], encoding="utf-8").read()
    first = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    counts = {k: 0 for k in TAGS}
    total = 0
    for n, tool, title, body in prompts(text):
        if n < first:
            continue
        total += 1
        hit = [k for k, rx in TAGS.items() if (body.lstrip().startswith("/") if rx is None else re.search(rx, body))]
        for k in hit:
            counts[k] += 1
        if hit:
            print(n, tool, title[:60], ",".join(hit))
    print("prompts:", total)
    for k, v in counts.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
