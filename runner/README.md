# Isolated runner

One trial, one disposable container ([issue #10](https://github.com/jtouley/harness-benchmark/issues/10),
[runner and isolation](../docs/plans/tasks/pipeline-family.md#runner-and-isolation)). Everything a trial needs
runs inside it: Claude Code (headless, `claude -p`), the arm's plugin (`--plugin-dir`), the task
repository, a Docker daemon of its own (Docker-in-Docker, privileged) for any database or broker the task
starts, the task's virtual environments and caches, and the grader. The host keeps only the collected
outputs. The container and its volume are deleted when the trial ends, also when it is interrupted.

## Use

```sh
docker build -t harness-benchmark/runner:local runner/     # once; native architecture of the host
ANTHROPIC_API_KEY=... runner/run_trial.sh \
  --repo path/to/task-repo --prompt path/to/prompt.txt --grader path/to/grader.sh \
  --model claude-opus-5-5 [--plugin-dir harnesses/reviewloop] [--suffix "text"] \
  --out results/runs/<trial>
```

Run one trial at a time on the laptop. `--help` lists every option (timeouts, permission mode, image).

| Input | Inside the container |
|---|---|
| `--repo` (copied; the host copy is not changed) | `/trial/repo`, the agent's working directory, owned by user `agent` |
| `--prompt`, plus ` ` and `--suffix` | `/trial/prompt.txt` |
| `--plugin-dir` | `/trial/plugin`, passed as `claude --plugin-dir` |
| `--grader`, `--grader-arg` (repeatable) | `/opt/hb-grader/grader` (root-only directory), copied in after the agent has finished; run as root as `grader /trial/repo [ARG...]` |
| `--replay`, `--replay-seed` | `/opt/hb-replay/replay.pyz` (root-only directory): a dev service started as root on `localhost:8099` before the agent and stopped before the grader |
| `ANTHROPIC_API_KEY` | standard input of the container; given to the agent process only |

The agent can write extra outputs to `$HB_OUTPUTS` (`/trial/out/agent`); a prompt that asks for a
summary file should name that path.

| Output (in `--out`) | What |
|---|---|
| `transcript.jsonl` | Claude Code's `stream-json` output |
| `result.json` | the transcript's last `result` line (cost, usage, `duration_ms`) |
| `grade.json`, `grade.stderr` | the grader's stdout and stderr |
| `timing.json` | `agent_seconds` (start to agent exit), `postprocess_seconds` (kill step, result extraction, wait for the grader), `grader_seconds`; agent and grader exit codes; agent processes killed and left after the kill; both caps; `agent_network_during_grading` (`blocked` or `open`); `dev_replay` |
| `replay-dev.log` | the dev service's log (with `--replay`) |
| `host.json` | container name, exit code, wall seconds, `api_key_redacted_files` |
| `agent/`, `claude-projects/` | files the agent wrote to `$HB_OUTPUTS`; Claude Code's session logs |
| `repo/` | the working tree the agent left, as plain files: no `.git`, `.venv`, `out/`, `lake/` or `target/` |
| `runner.log`, `agent.stderr`, `dockerd.log` | logs |

The container exits 0 once the grader has run, also when the agent timed out (`agent_exit` 124) or the
grader failed. Read the result from `timing.json` and `grade.json`, not from the exit code of
`run_trial.sh`. Its own exit codes: 2 (bad arguments), 3 (an output file could not be scanned for the
API key), 90 (the inner daemon did not start), 91 (the grader was not delivered), 130 (interrupted).
`results/runs/` is in `.gitignore`.

## What happens in a trial

1. `run_trial.sh` creates the container (no bind mount, no published port), copies the inputs in, and
   starts it with the API key on standard input.
2. `entrypoint.sh` starts the inner `dockerd`; its storage is the container's anonymous volume.
3. The agent runs as user `agent` (in the `docker` group), with the key in its environment only. A
   one-shot runs under its guard cap (`--agent-timeout`); a harness arm (`--plugin-dir`) has no time limit
   (criteria v2 §5.3).
   With `--replay`, a dev service (`replay.pyz`) runs as root on `localhost:8099` during the agent's
   session; the agent can use it but not read its files.
4. Every process of user `agent` in the trial's own PID namespace is killed (repeated until none is
   left), so no worker the agent left can serve the grader. Containers the agent started in the inner
   daemon stay up for the grader, also when they run as uid 1000 (the uid of `agent`).
5. `run_trial.sh` copies the grader in only now (the agent never sees it), into a root-only directory; it
   runs as root, without the key. While it runs, processes of user `agent` (a task's `make`, when the
   grader runs it as that user) have no network beyond loopback. A grader killed at `--grader-timeout`
   leaves `{"error": ..., "reward": 0.0}` as `grade.json`.
6. `run_trial.sh` copies `/trial/out` to `--out`, replaces each copy of the API key in those files with
   `[REDACTED:ANTHROPIC_API_KEY]`, then `docker rm -f -v`: the container, its volume, the inner daemon
   and everything in it go.

The API key is never a process argument (shell builtins write it to the container's standard input and
`export` it for the agent), and the runner does not put it in the image, the container configuration
(`docker inspect`), a file or a log. The agent itself can read it from its own environment, as on the
host, and can print it; the scan in step 6 redacts what it printed before the outputs are used. The scan
reads the key from the environment and never prints it.

## Image

A task image can add `/opt/hb/toolchain.env` (NAME=VALUE lines): the entrypoint gives those variables to
the agent and to the grader. The pipeline family's images are built by `pipeline/build.sh` on top of
this one (`pipeline/Dockerfile`: the toolchains with warm caches; `pipeline/caps.json`: the caps).

`Dockerfile`: Debian bookworm-slim (glibc, so task virtualenvs get manylinux wheels), the static Docker
29.9.0 binaries and `dind` wrapper from `docker:29.9.0-dind` (daemon, CLI, compose, buildx), uv 0.13.1,
Claude Code 2.1.287 (native installer), git, Python 3.11, jq. 814 MB on arm64. Build it on the machine
that runs the trials: arm64 on the Apple Silicon laptop, x86-64 on a cloud host.

## Tests

`tests/test_runner.py`. Without Docker: argument checks; that both scripts give the key to builtins
only; that the output scan redacts the key (a fake `docker` writes outputs that hold a fake key) and does
not follow links; that `results/runs/` is ignored by git. With `HB_RUNNER_DOCKER_TESTS=1`: builds the image, then runs stub trials (no API call)
whose agent starts a uid-1000 service in the inner daemon, leaves a background process, prints its
(fake) key and a non-JSON line, commits and holds; the
tests check the container while it runs and after it ends, and interrupt one trial. One more trial runs
the real Claude Code agent with a plugin and no key: it loads the plugin and model, stops at login, and
makes no API request.

## Not yet done

- Real Claude Code trials have run in the container on the pipeline tasks only
  ([2026-10-15](../docs/evidence/2026-10-15-pipeline-trials.md)); B01 has not.
- The inner daemon starts empty each trial, so every trial pulls the task's images (no cache or mirror).
- Parallel trials on a remote x86-64 host (the account is an owner decision); the image has not been
  built on x86-64.
- Harbor does not use this runner yet.
- The isolation protects the host and other trials, not the grader from a hostile agent: the agent is in
  the inner daemon's `docker` group (root inside the container), and containers it leaves running in the
  inner daemon are still up while the grader runs.
