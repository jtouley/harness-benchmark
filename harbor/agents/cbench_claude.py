"""Claude Code under Harbor, with the framework's install left in place.

Harbor's built-in ``claude-code`` agent points ``CLAUDE_CONFIG_DIR`` at a fresh
directory under the trial's logs and copies only ``~/.claude/skills`` into it.
That drops user-level hooks (``settings.json``) and plugins, which is exactly what
Cadence and Superpowers install. This subclass seeds the same directory from the
image's ``~/.claude`` right after Harbor creates it, so every arm runs with what
its own documented installer wrote. Nothing else changes: same command line,
same trajectory and token/cost capture.

Pinned to Harbor 0.24.0: it matches the setup command Harbor builds in
``ClaudeCode.run``. If a Harbor upgrade changes that command, the test in
``tests/test_harbor.py`` (``test_agent_hook_matches_harbor``) fails loudly.
"""

from __future__ import annotations

from harbor.agents.installed.claude_code import ClaudeCode

# The first command of ClaudeCode.run: creates the config dir layout.
SETUP_MARKER = "mkdir -p $CLAUDE_CONFIG_DIR/debug"
SEED = (
    ' && { [ -d ~/.claude ] && cp -a ~/.claude/. "$CLAUDE_CONFIG_DIR"/ 2>/dev/null; true; }'
    ' && rm -rf "$CLAUDE_CONFIG_DIR"/projects/* "$CLAUDE_CONFIG_DIR"/backups'
)


class CbenchClaudeCode(ClaudeCode):
    @staticmethod
    def name() -> str:
        return "cbench-claude-code"

    async def exec_as_agent(self, environment, command, env=None, cwd=None, timeout_sec=None):
        if SETUP_MARKER in command and SEED not in command:
            command += SEED
        return await super().exec_as_agent(environment, command, env=env, cwd=cwd, timeout_sec=timeout_sec)
