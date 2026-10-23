"""The task prompt, taken word for word from the specs.

    python -m pipetask.prompt P1 > golden/pipeline/P1/prompt.md
    python -m pipetask.prompt P4 > golden/pipeline/P4/prompt.md

The prompt is the shared request (the quoted block under "The request" in docs/plans/tasks/pipeline-spec.md)
followed by the task's stack section (the quoted block under "Stack section" in the task's page), with
the quote markers removed and nothing added. A test checks that the committed prompt files still equal
this, so a prompt cannot drift from the spec or gain a hint. P4, the hold-out, has its own request: the
quoted block under "The request" in its page, and nothing else.
"""

from __future__ import annotations

import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[3] / "docs" / "plans" / "tasks"
TASK_PAGES = {"P1": "P1-duckdb-dlt-dbt.md", "P2": "P2-config-arrow-polars-datafusion.md", "P3": "P3-scala-spark.md"}
OWN_REQUEST = {"P4": "P4-holdout-library-loans.md"}  # the hold-out: its own request, no stack section


def quoted_block(markdown: str, heading_prefix: str) -> str:
    """The first block of `>` lines after the heading that starts with heading_prefix."""
    lines = markdown.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(heading_prefix))
    block, inside = [], False
    for line in lines[start + 1:]:
        if line.startswith(">"):
            inside = True
            block.append(line[2:] if line.startswith("> ") else line[1:])
        elif inside:
            break
    return "\n".join(block).strip() + "\n"


def prompt(task: str) -> str:
    if task in OWN_REQUEST:
        return quoted_block((DOCS / OWN_REQUEST[task]).read_text(encoding="utf-8"), "## The request")
    request = quoted_block((DOCS / "pipeline-spec.md").read_text(encoding="utf-8"), "## The request")
    stack = quoted_block((DOCS / TASK_PAGES[task]).read_text(encoding="utf-8"), "## Stack section")
    return request + "\n" + stack


if __name__ == "__main__":
    sys.stdout.write(prompt(sys.argv[1]))
