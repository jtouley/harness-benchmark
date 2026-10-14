"""scripts/clean_room_check.py: a run is graded only when it saw and used only its own skills."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("clean_room_check", ROOT / "scripts" / "clean_room_check.py")
crc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(crc)

BUILTIN = sorted(crc.builtin_skills())


def _write(path: Path, *records: dict) -> Path:
    path.write_text("\n".join(json.dumps(r) for r in records) + ("\n" if records else ""), encoding="utf-8")
    return path


def _transcript(tmp_path: Path, *records: dict) -> Path:
    return _write(tmp_path / "t.jsonl", *records)


def _listing(*names: str) -> dict:
    return {"type": "attachment", "attachment": {"type": "skill_listing", "names": list(names)}}


def _call(name: str, **tool_input) -> dict:
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "name": name, "input": tool_input}]}}


def _user(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}]}}


def _verdict(paths, allow=(), allow_paths=()):
    return crc.verdict(crc.scan(list(paths)), set(allow), list(allow_paths))


def test_only_built_in_skills_listed_and_no_contact_is_clean(tmp_path):
    t = _transcript(tmp_path, _listing(*BUILTIN), _user("Add budgets"), _call("Bash", command="pytest -q"))
    assert crc.main([str(t)]) == 0


def test_an_empty_transcript_is_unassessable(tmp_path):
    """R1 on PR #8: an empty transcript was graded clean."""
    t = _transcript(tmp_path)
    assert crc.main([str(t)]) == 3


def test_a_transcript_with_no_skill_listing_is_unassessable(tmp_path):
    t = _transcript(tmp_path, _call("Bash", command="pytest -q"))
    assert _verdict([t])["verdict"] == "unassessable"


def test_a_listing_of_other_skills_is_exposure(tmp_path):
    t = _transcript(tmp_path, _listing("spec-driven", "test-benchmark", *BUILTIN), _call("Bash", command="pytest -q"))
    result = _verdict([t])
    assert result["verdict"] == "exposed"
    assert result["unexpected_listed"] == ["spec-driven", "test-benchmark"]
    assert crc.main([str(t)]) == 1


def test_the_plain_text_listing_is_read_with_multi_line_descriptions(tmp_path):
    text = ("<system-reminder>\nThe following skills are available for use with the Skill tool:\n\n"
            "- spec-driven: Execute with strict TDD.\n  More text on a second line.\n"
            "- cadence: Gated pipeline.\n</system-reminder>")
    t = _transcript(tmp_path, _user(text))
    assert crc.scan([t])["listed"] == ["cadence", "spec-driven"]


def test_a_skill_call_outside_the_allowlist_is_contamination(tmp_path):
    t = _transcript(tmp_path, _listing("spec-driven"), _call("Skill", skill="spec-driven"))
    assert crc.main([str(t)]) == 2


@pytest.mark.parametrize("tool, tool_input", [
    ("Read", {"file_path": "/Users/x/.claude/skills/spec-driven/SKILL.md"}),
    ("Bash", {"command": "cat ~/.cursor/rules/001-core-tdd-protocol.mdc"}),
    ("Bash", {"command": "sed -n 1,40p /Users/x/.cursor/skills/ship-feature/SKILL.md"}),
    ("Read", {"file_path": "/repo/CLAUDE.md"}),
    ("Read", {"file_path": "/Users/x/.claude/plugins/cache/every/ce/skills/tdd/references/steps.md"}),
    ("Read", {"file_path": "/Users/x/.claude/projects/-Users-x-repo/memory/MEMORY.md"}),
    ("Grep", {"pattern": "TDD", "path": "/Users/x/.claude/skills"}),
])
def test_touching_a_skill_rule_plugin_or_memory_location_is_contamination(tmp_path, tool, tool_input):
    t = _transcript(tmp_path, _listing(*BUILTIN), _call(tool, **tool_input))
    assert _verdict([t])["verdict"] == "contaminated"


def test_text_that_a_tool_writes_is_not_a_contact(tmp_path):
    """R1 on PR #8: a Write whose content mentions .cursor/rules/ was counted as contamination."""
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Write", file_path="/repo/README.md",
                                                       content="Never read ~/.cursor/rules/ in this repo"))
    assert _verdict([t])["verdict"] == "clean"


def test_an_arm_may_list_call_and_read_its_own_harness(tmp_path):
    t = _transcript(tmp_path, _listing("cadence", *BUILTIN), _call("Skill", skill="cadence"),
                    _call("Read", file_path="/Users/x/Projects/cadence-wt/main-eval/SKILL.md"))
    assert _verdict([t], {"cadence"}, ["/Users/x/Projects/cadence-wt/main-eval"])["verdict"] == "clean"


def test_an_allowed_path_matches_whole_components_only(tmp_path):
    """R1 on PR #8: cadence-wt/main-eval also allowed cadence-wt/main-eval-old/."""
    t = _transcript(tmp_path, _listing("cadence", *BUILTIN),
                    _call("Read", file_path="/Users/x/Projects/cadence-wt/main-eval-old/skills/x/SKILL.md"))
    assert _verdict([t], {"cadence"}, ["/Users/x/Projects/cadence-wt/main-eval"])["verdict"] == "contaminated"


def test_a_plugin_prefixed_name_needs_its_own_allowlist_entry(tmp_path):
    """R1 on PR #8: any <plugin>:cadence passed an allowlist of cadence."""
    t = _transcript(tmp_path, _listing("other-plugin:cadence", *BUILTIN))
    assert _verdict([t], {"cadence"})["verdict"] == "exposed"
    assert _verdict([t], {"other-plugin:cadence"})["verdict"] == "clean"


def test_nested_agents_of_the_run_are_read(tmp_path):
    """cadence#53 happened in a nested peer: its transcript must be part of the run."""
    agents = tmp_path / "subagents"
    agents.mkdir()
    _write(agents / "agent-run.jsonl", _listing("cadence", *BUILTIN), _call("Agent", prompt="/test-benchmark 1"))
    (agents / "agent-run.meta.json").write_text(json.dumps({"spawnDepth": 1}))
    _write(agents / "agent-peer.jsonl", _listing("cadence", "test-benchmark", *BUILTIN),
           _call("Skill", skill="test-benchmark"))
    (agents / "agent-peer.meta.json").write_text(json.dumps({"parentAgentId": "run", "spawnDepth": 2}))
    _write(agents / "agent-other.jsonl", _call("Skill", skill="spec-driven"))
    (agents / "agent-other.meta.json").write_text(json.dumps({"spawnDepth": 1}))
    paths = crc.run_transcripts(agents, "run")
    assert sorted(p.name for p in paths) == ["agent-peer.jsonl", "agent-run.jsonl"]
    result = _verdict(paths, {"cadence"})
    assert result["verdict"] == "contaminated" and result["unexpected_calls"] == ["test-benchmark"]
    assert crc.main(["--agents-dir", str(agents), "--agent", "run", "--allow", "cadence"]) == 2


def test_direct_peers_of_a_top_level_session_are_read(tmp_path):
    """R1 re-review on PR #8: depth-1 agents have no parentAgentId; they live in <session>/subagents/."""
    session = _write(tmp_path / "S.jsonl", _listing(*BUILTIN), _call("Agent", prompt="/test-benchmark 1"))
    (tmp_path / "S" / "subagents").mkdir(parents=True)
    _write(tmp_path / "S" / "subagents" / "agent-p.jsonl", _listing("test-benchmark", *BUILTIN),
           _call("Skill", skill="test-benchmark"))
    assert crc.main([str(session)]) == 2


def test_calling_a_built_in_skill_needs_the_allowlist(tmp_path):
    """R1 re-review on PR #8: built-ins may be listed, but a call is use."""
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Skill", skill="code-review"))
    assert _verdict([t])["verdict"] == "contaminated"
    assert _verdict([t], {"code-review"})["verdict"] == "clean"


def test_a_listing_entry_without_a_description_and_a_three_part_name_are_read(tmp_path):
    text = ("<system-reminder>\nThe following skills are available for use with the Skill tool:\n\n"
            "- bare-skill\n- org:pack:tool: A three-part name.\n</system-reminder>")
    t = _transcript(tmp_path, _user(text))
    assert crc.scan([t])["listed"] == ["bare-skill", "org:pack:tool"]


def test_a_relative_path_resolves_against_the_run_cwd(tmp_path):
    """Pilot 2026-10-13: `cat README* CLAUDE.md` in the task repo is the repo's own file, not a user-level one."""
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Bash", command="cat README* CLAUDE.md"))
    assert _verdict([t])["verdict"] == "contaminated"
    found = crc.scan([t], cwd="/runs/a/repo")
    assert found["contacts"] == ["/runs/a/repo/CLAUDE.md"]
    assert crc.verdict(found, set(), ["/runs/a/repo"])["verdict"] == "clean"
    assert crc.main([str(t), "--cwd", "/runs/a/repo", "--allow-path", "/runs/a/repo"]) == 0


def test_a_home_path_does_not_resolve_against_the_cwd(tmp_path):
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Bash", command="cat ~/.claude/skills/x/SKILL.md"))
    found = crc.scan([t], cwd="/runs/a/repo")
    assert crc.verdict(found, set(), ["/runs/a/repo"])["verdict"] == "contaminated"


def test_a_grep_pattern_is_not_a_path(tmp_path):
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Grep", pattern="SKILL.md", path="/repo/src"))
    assert _verdict([t])["verdict"] == "clean"


# Negative fixtures, one per known leak channel (review of PR #8 at 20257f2). Each must be non-clean.
REPO = "/runs/a/repo"


def _repo_verdict(t, cwd=REPO, allow_paths=(REPO,)):
    return crc.verdict(crc.scan([t], cwd=cwd), set(), list(allow_paths))["verdict"]


@pytest.mark.parametrize("file_path", [
    "../../../home/u/.claude/skills/tdd/SKILL.md",
    f"{REPO}/../../../home/u/.claude/skills/tdd/SKILL.md",
])
def test_a_dotdot_path_does_not_escape_the_allowed_cwd(tmp_path, file_path):
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Read", file_path=file_path))
    assert _repo_verdict(t) == "contaminated"


def test_a_relative_path_after_cd_is_not_read_as_under_the_cwd(tmp_path):
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Bash", command="cd ~ && cat .claude/skills/tdd/SKILL.md"))
    assert _repo_verdict(t) == "contaminated"


def test_an_allow_path_must_be_absolute_and_matches_as_a_prefix(tmp_path):
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Read", file_path="/home/u/repo/.claude/skills/x/SKILL.md"))
    with pytest.raises(ValueError):
        crc.verdict(crc.scan([t]), set(), ["repo"])
    assert crc.verdict(crc.scan([t]), set(), ["/runs/a/repo"])["verdict"] == "contaminated"
    with pytest.raises(SystemExit) as exit_:
        crc.main([str(t), "--allow-path", "repo"])
    assert exit_.value.code == 2  # argparse usage error


@pytest.mark.parametrize("tool, tool_input", [
    ("Bash", {"command": "grep -rn TDD ~/.claude"}),
    ("Grep", {"pattern": "TDD", "path": "/home/u/.claude"}),
    ("Bash", {"command": "find ~/.claude -name '*.md' -exec cat {} +"}),
    ("Glob", {"pattern": ".claude/skills/**/*.md", "path": "/home/u"}),
    ("Read", {"file_path": "/home/u/.codex/skills/tdd/SKILL.txt"}),
    ("Read", {"file_path": "/home/u/.agents/skills/tdd/notes.txt"}),
    ("Read", {"file_path": "/home/u/.claude/settings.json"}),
    ("Read", {"file_path": "/home/u/.claude/hooks/pre.sh"}),
    ("Read", {"file_path": "/home/u/.claude/output-styles/tdd.md"}),
])
def test_any_contact_with_a_host_config_directory_is_contamination(tmp_path, tool, tool_input):
    t = _transcript(tmp_path, _listing(*BUILTIN), _call(tool, **tool_input))
    assert _verdict([t])["verdict"] == "contaminated"


def test_auto_loaded_instruction_files_are_contacts(tmp_path):
    text = ("<system-reminder>\nContents of /home/u/.claude/CLAUDE.md (user's private global instructions):\n"
            "Always use strict TDD.\nContents of /home/u/.claude/projects/-x/memory/MEMORY.md:\n- prefer TDD\n"
            "</system-reminder>")
    t = _transcript(tmp_path, _listing(*BUILTIN), _user(text), _call("Bash", command="pytest -q"))
    result = _verdict([t])
    assert result["verdict"] == "contaminated"
    assert result["unexpected_contacts"] == ["/home/u/.claude/CLAUDE.md", "/home/u/.claude/projects/-x/memory/MEMORY.md"]


def test_an_instructions_attachment_is_a_contact_unless_it_is_the_task_repo(tmp_path):
    attachment = {"type": "attachment", "attachment": {"type": "instructions", "files": [
        {"path": f"{REPO}/AGENTS.md", "type": "Project", "content": "Run tests."},
        {"path": "/home/u/.claude/CLAUDE.md", "type": "User", "content": "Always TDD."}]}}
    t = _transcript(tmp_path, _listing(*BUILTIN), attachment)
    result = crc.verdict(crc.scan([t], cwd=REPO), set(), [REPO])
    assert result["verdict"] == "contaminated"
    assert result["unexpected_contacts"] == ["/home/u/.claude/CLAUDE.md"]


def test_spawning_a_user_level_subagent_type_is_use(tmp_path):
    t = _transcript(tmp_path, _listing(*BUILTIN),
                    _call("Task", subagent_type="compound-engineering:review:kieran-python-reviewer", prompt="review"),
                    _call("Agent", subagent_type="Explore", prompt="find x"), _call("Agent", prompt="no type"))
    result = _verdict([t])
    assert result["verdict"] == "contaminated"
    assert result["unexpected_calls"] == ["compound-engineering:review:kieran-python-reviewer"]
    assert _verdict([t], {"compound-engineering:review:kieran-python-reviewer"})["verdict"] == "clean"


def test_a_listing_of_user_level_agent_types_is_exposure(tmp_path):
    listing = {"type": "attachment", "attachment": {"type": "agent_listing_delta",
               "addedTypes": ["Explore", "general-purpose", "kieran-python-reviewer"],
               "builtInTypes": ["Explore", "general-purpose"]}}
    t = _transcript(tmp_path, _listing(*BUILTIN), listing)
    result = _verdict([t])
    assert result["verdict"] == "exposed"
    assert result["unexpected_listed"] == ["kieran-python-reviewer"]


def test_reading_a_saved_tool_output_of_the_session_is_not_a_contact(tmp_path):
    """Claude Code saves large tool outputs under ~/.claude/projects/<slug>/<session>/tool-results/."""
    saved = "/home/u/.claude/projects/-runs-a-repo/0f1e/tool-results/b1.txt"
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Read", file_path=saved),
                    _call("Read", file_path="/home/u/.claude/projects/-runs-a-repo/memory/notes.md"))
    assert _verdict([t])["unexpected_contacts"] == ["/home/u/.claude/projects/-runs-a-repo/memory/notes.md"]


@pytest.mark.parametrize("command", [
    "find ~ -name SKILL.md -exec cat {} +",
    "rg --files -g CLAUDE.md /home/u",
    "grep -rl 'strict TDD' /home/u",
    "grep -rn TDD $HOME",
    "ls /Users/x",
])
def test_a_command_over_the_home_folder_is_a_contact(tmp_path, command):
    """R7 on PR #8: a bare instruction-file name was a search pattern, resolved into the allowed repo."""
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Bash", command=command))
    assert _repo_verdict(t) == "contaminated"


def test_a_cd_to_one_absolute_folder_sets_the_base_for_relative_paths(tmp_path):
    t = _transcript(tmp_path, _listing(*BUILTIN), _call("Bash", command=f"cd {REPO} && cat CLAUDE.md"))
    assert _repo_verdict(t) == "clean"


def test_loaded_file_text_inside_a_tool_result_is_not_a_contact(tmp_path):
    result = {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x",
              "content": "Contents of /home/u/.claude/CLAUDE.md: see the docs"}]}}
    t = _transcript(tmp_path, _listing(*BUILTIN), result)
    assert _repo_verdict(t) == "clean"
