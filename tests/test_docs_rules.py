"""docs/rules.md: every rule links to code or a test that exists, so the page stays auditable."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "rules.md"
TEXT = PAGE.read_text(encoding="utf-8")
# A numbered rule: from "N. **" to the next numbered rule or heading.
RULES = re.findall(r"^\d+\. \*\*.*?(?=^\d+\. \*\*|^## )", TEXT, re.M | re.S)
TEST_NAMES = {m for p in (ROOT / "tests").glob("test_*.py") for m in re.findall(r"^def (test_\w+)", p.read_text(encoding="utf-8"), re.M)}


def test_every_link_on_the_page_resolves():
    links = re.findall(r"\]\(([^)]+)\)", TEXT)
    assert links
    for link in links:
        assert (PAGE.parent / link).exists(), link


def _enclosing_parenthesis(text: str, at: int) -> str | None:
    """The innermost balanced (...) span around position `at`, or None."""
    depth, start = 0, None
    for i in range(at, -1, -1):
        if text[i] == ")":
            depth += 1
        elif text[i] == "(":
            if depth == 0:
                start = i
                break
            depth -= 1
    if start is None:
        return None
    depth = 0
    for j in range(start, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return text[start:j + 1]
    return None


def test_every_test_a_rule_names_exists_unless_its_own_parenthesis_names_a_pull_request():
    """The exemption is per test name: a name that is not in tests/ must sit in a parenthesis that names
    the pull request it is in, so one unmerged test cannot excuse a wrong name elsewhere in the rule."""
    assert len(RULES) >= 15
    for rule in RULES:
        for m in re.finditer(r"`(test_\w+)`", rule):
            name = m.group(1)
            if name in TEST_NAMES:
                continue
            span = _enclosing_parenthesis(rule, m.start())
            assert span is not None and re.search(r"#\d+", span), (name, rule[:60])


def test_the_table_lists_every_rule_once():
    rows = re.findall(r"^\| (\d+) ", TEXT, re.M)
    assert rows == [str(i) for i in range(1, len(RULES) + 1)]
