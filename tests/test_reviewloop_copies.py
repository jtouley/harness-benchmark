"""The two reviewloop arms are copies that must differ only in the reviewer's model."""
import json
from pathlib import Path

H = Path(__file__).resolve().parents[1] / "harnesses"
BASE, SONNET = H / "reviewloop", H / "reviewloop-sonnet-reviewer"


def files(root):
    return sorted(p.relative_to(root) for p in root.rglob("*") if p.is_file())


def test_reviewloop_copies_differ_only_in_the_reviewer_model():
    assert files(BASE) == files(SONNET)
    for rel in files(BASE):
        if rel.name == "plugin.json":
            continue
        a, b = (BASE / rel).read_text(), (SONNET / rel).read_text()
        if rel == Path("agents/reviewer.md"):
            a, b = a.replace("model: opus", "model: X"), b.replace("model: sonnet", "model: X")
        assert a == b, f"{rel} drifted between the two reviewloop copies"


def test_plugin_descriptions_name_the_pinned_reviewer_model():
    for root, model in [(BASE, "opus"), (SONNET, "sonnet")]:
        assert f"model: {model}\n" in (root / "agents/reviewer.md").read_text()
        desc = json.loads((root / ".claude-plugin/plugin.json").read_text())["description"]
        assert model in desc.lower() and "stronger model" not in desc
