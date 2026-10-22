#!/usr/bin/env bash
# What .github/workflows/verify.yml runs, on this machine. GitHub-hosted CI is off (billing blocks every
# hosted runner), so run this before each push and paste its last lines into the pull request.
#
# Each `== <name>` section is one `run:` step of verify.yml (tests/test_ci_local.py keeps them in step).
# A step that cannot run here prints "skipped: <why>" and the command to run it by hand.
#
# Time budget: tests/time_budget.py sizes its budgets for GitHub's ubuntu-latest runner. A local machine
# can be slower, and a false red pasted into a PR is worse than none, so this script sets
# HB_TEST_WALL_BUDGET and HB_TEST_TOTAL_BUDGET to CI_LOCAL_BUDGET_FACTOR (default 2) times the CI budgets,
# unless they are already set. The budget it used is printed.
set -euo pipefail
cd "$(dirname "$0")/.."

FACTOR=${CI_LOCAL_BUDGET_FACTOR:-2}
read -r CI_WALL CI_TOTAL < <(python3 -c '
import re, pathlib
text = pathlib.Path("tests/time_budget.py").read_text()
b = dict(re.findall(r"\"(wall|total)\": ([0-9.]+)", re.search(r"BUDGETS = \{[^}]*\}", text).group(0)))
print(int(float(b["wall"])), int(float(b["total"])))')
if [ -n "${HB_TEST_WALL_BUDGET:-}" ] || [ -n "${HB_TEST_TOTAL_BUDGET:-}" ]; then
  export HB_TEST_WALL_BUDGET=${HB_TEST_WALL_BUDGET:-$CI_WALL} HB_TEST_TOTAL_BUDGET=${HB_TEST_TOTAL_BUDGET:-$CI_TOTAL}
  echo "budget: wall $HB_TEST_WALL_BUDGET s, total $HB_TEST_TOTAL_BUDGET s (set in the environment)"
else
  export HB_TEST_WALL_BUDGET=$((CI_WALL * FACTOR)) HB_TEST_TOTAL_BUDGET=$((CI_TOTAL * FACTOR))
  echo "budget: wall $HB_TEST_WALL_BUDGET s, total $HB_TEST_TOTAL_BUDGET s ($FACTOR x the CI budget of wall $CI_WALL s, total $CI_TOTAL s)"
fi
[ "${CI_LOCAL_ONLY_BUDGET:-}" = 1 ] && exit 0

HAND="Run by hand where it can run:"
CLAUDE_PIN=2.1.294

echo "== npm install -g @anthropic-ai/claude-code@2.1.294"
if claude --version 2>/dev/null | grep -q "^$CLAUDE_PIN"; then
  CLAUDE_OK=1; echo "Claude Code $CLAUDE_PIN is installed"
else
  CLAUDE_OK=0
  echo "skipped: Claude Code $CLAUDE_PIN is not installed here (found: $(claude --version 2>/dev/null || echo none));" \
       "this script does not install global tools. $HAND npm install -g @anthropic-ai/claude-code@$CLAUDE_PIN"
fi

echo "== Split pinned frameworks into fetchable and private"
PRIVATE_REPOS="https://github.com/jtouley/cadence"
read -r -d '' SPLIT <<'PY' || true
import json, sys
private_repos = sys.argv[1].split()
public, private = [], []
for name, fw in json.load(open("frameworks.lock.json"))["frameworks"].items():
    (private if fw.get("repo", "") in private_repos else public).append(name)
print(" ".join(public)); print(" ".join(private))
PY
{ read -r PUBLIC; read -r PRIVATE; } < <(python3 -c "$SPLIT" "$PRIVATE_REPOS")
echo "public: $PUBLIC"; echo "private: ${PRIVATE:-none}"

echo "== Fetch pinned frameworks (checks each pinned sha)"
FETCHED=0
if timeout 20 git ls-remote --exit-code https://github.com/obra/superpowers HEAD >/dev/null 2>&1; then
  # shellcheck disable=SC2086  # one argument per framework, as in verify.yml
  uv run --frozen --with tokenizers python -m cbench fetch $PUBLIC
  FETCHED=1
else
  echo "skipped: github.com is not reachable from here. $HAND uv run --frozen --with tokenizers python -m cbench fetch $PUBLIC"
fi

echo "== Install every fetchable framework twice and compare the trees"
if [ "$FETCHED" = 1 ] && [ "$CLAUDE_OK" = 1 ]; then
  # shellcheck disable=SC2086
  uv run --frozen --with tokenizers python -m cbench install-check $PUBLIC
else
  WHY=$([ "$FETCHED" = 1 ] || echo "the fetch above did not run; ")$([ "$CLAUDE_OK" = 1 ] || echo "Claude Code $CLAUDE_PIN is not installed; ")
  echo "skipped: ${WHY%; }. $HAND uv run --frozen --with tokenizers python -m cbench install-check $PUBLIC"
fi

echo "== Verify every committed result byte for byte"
if [ -z "$PRIVATE" ] && [ "$FETCHED" = 1 ] && [ "$CLAUDE_OK" = 1 ]; then
  uv run --frozen --with tokenizers python -m cbench verify
else
  echo "skipped: needs every framework, and ${PRIVATE:-a step above} is not available here. $HAND" \
       "uv run --frozen --with tokenizers python -m cbench fetch && uv run --frozen --with tokenizers python -m cbench verify"
fi

echo "== Unit and pipeline tests"
HB_TEST_BUDGET=1 uv run --frozen --with tokenizers python -m pytest -q

echo "== Regenerate the report"
uv run --frozen --with tokenizers python -m cbench report
git diff --exit-code results/
echo "ci_local: OK at $(git rev-parse --short HEAD)"
