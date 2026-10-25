"""Rebuild a one-shot's delivered tree by replaying its transcript's writes, in order, onto the stored
starting repository.

    python replay_transcript.py TRANSCRIPT ORIG_REPO_PATH LOG

Runs inside a private mount and network namespace (replay_tree.sh) where ORIG_REPO_PATH (the path the
agent worked in) is the rebuild directory and /tmp is a fresh tmpfs, so every command sees the paths it saw
in the run. Each tool call is applied in transcript order:
- Write: the file is written with the call's content. Edit: old_string -> new_string (replace_all honoured),
  refused when old_string is missing (logged).
- Bash: the command runs in bash from the cwd the session had, with the run's own cwd rule: the cwd persists,
  and is reset to the repository when a command leaves it outside the repository ("Shell cwd was reset").
  Commands that run the pipeline, fetch, wait or kill (make, uv, dbt, curl, sleep, pkill, nohup) are shell
  functions that do nothing and log the call: they write only ignored outputs (lake/, out/, .venv/,
  transform/target), never source, and every logged call is listed so that can be checked. `timeout` runs
  its command through the same functions.
- Read, Monitor, ToolSearch: no effect on the tree.
The log is one JSON line per tool call: index, tool, exit code, the original result's is_error, and the
calls a shim swallowed.
"""
import json, os, subprocess, sys

tx, repo, log = sys.argv[1], sys.argv[2], sys.argv[3]
SHIMS = r'''
__shim() { printf '%s\n' "$*" >> "$SHIMLOG"; return 0; }
make() { __shim make "$@"; }; uv() { __shim uv "$@"; }; dbt() { __shim dbt "$@"; }; curl() { __shim curl "$@"; }
sleep() { __shim sleep "$@"; }; pkill() { __shim pkill "$@"; }; nohup() { __shim nohup "$@"; }
timeout() { while [ $# -gt 0 ]; do case "$1" in -s|-k|--signal|--kill-after) shift 2;; -*) shift;; *) shift; break;; esac; done; "$@"; }
export -f __shim make uv dbt curl sleep pkill nohup timeout
'''
events = [json.loads(l) for l in open(tx) if l.strip()]
results = {}
for e in events:
    if e.get("type") == "user":
        for b in (e.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_result":
                results[b["tool_use_id"]] = bool(b.get("is_error"))
cwd = repo
n = 0
with open(log, "w") as out:
    for e in events:
        if e.get("type") != "assistant":
            continue
        for b in (e.get("message") or {}).get("content") or []:
            if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                continue
            n += 1
            name, inp = b["name"], b["input"]
            rec = {"i": n, "tool": name, "orig_error": results.get(b["id"])}
            if name == "Write":
                p = inp["file_path"]; os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, "w").write(inp["content"]); rec["path"] = p
            elif name == "Edit":
                p = inp["file_path"]; s = open(p).read(); rec["path"] = p
                if inp["old_string"] not in s:
                    rec["edit"] = "old_string missing"
                else:
                    s = s.replace(inp["old_string"], inp["new_string"]) if inp.get("replace_all") else s.replace(inp["old_string"], inp["new_string"], 1)
                    open(p, "w").write(s); rec["edit"] = "applied"
            elif name == "Bash":
                shimlog = "/tmp/.shim.log"
                open(shimlog, "w").close()
                pwdfile = "/tmp/.pwd"
                script = SHIMS + f"trap 'pwd > {pwdfile}' EXIT\ncd {json.dumps(cwd)}\n" + inp["command"] + "\n"
                try:
                    p = subprocess.run(["bash", "-c", script], stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                       timeout=300, env={**os.environ, "SHIMLOG": shimlog})
                    rec["exit"] = p.returncode; rec["stderr"] = p.stderr[-300:]
                except subprocess.TimeoutExpired:
                    rec["exit"] = "timeout"
                try:
                    new = open(pwdfile).read().strip()
                    cwd = new if (new == repo or new.startswith(repo + "/")) else repo
                except OSError:
                    pass
                rec["shimmed"] = [l for l in open(shimlog).read().splitlines() if l]
                rec["cmd"] = inp["command"][:200]
                if inp.get("run_in_background"):
                    rec["background"] = True
            out.write(json.dumps(rec) + "\n")
print("replayed", n, "tool calls")
