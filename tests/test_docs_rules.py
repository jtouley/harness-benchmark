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


def test_every_test_a_rule_names_exists_unless_the_rule_says_it_is_in_a_pull_request():
    assert len(RULES) >= 15
    for rule in RULES:
        in_pr = re.search(r"#\d+", rule) is not None
        for name in re.findall(r"`(test_\w+)`", rule):
            assert name in TEST_NAMES or in_pr, (name, rule[:60])


def test_the_table_lists_every_rule_once():
    rows = re.findall(r"^\| (\d+) ", TEXT, re.M)
    assert rows == [str(i) for i in range(1, len(RULES) + 1)]
