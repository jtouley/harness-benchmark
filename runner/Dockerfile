# One disposable container per trial: Claude Code, the arm's plugin, the task repository, its own
# Docker daemon (Docker-in-Docker, run privileged), the task's virtualenvs and caches, and the grader.
# Built for the host's architecture: arm64 on the Apple Silicon laptop, x86-64 on a cloud host.
# glibc base (Debian), not Alpine: task virtualenvs need manylinux wheels.
ARG DOCKER_VERSION=29.9.0
FROM docker:${DOCKER_VERSION}-dind AS docker

FROM debian:bookworm-slim
ARG CLAUDE_CODE_VERSION=2.1.287
ARG UV_VERSION=0.13.1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      bash ca-certificates curl git python3 python3-venv procps psmisc \
      iptables pigz xz-utils tini jq \
 && rm -rf /var/lib/apt/lists/*

# Static Docker binaries (dockerd, containerd, runc, the CLI, compose and buildx plugins) and the
# `dind` wrapper that prepares cgroups for a nested daemon.
COPY --from=docker /usr/local/bin/ /usr/local/bin/
COPY --from=docker /usr/local/libexec/docker/cli-plugins/ /usr/local/libexec/docker/cli-plugins/

RUN curl -fsSL "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-$(uname -m)-unknown-linux-gnu.tar.gz" \
      | tar -xz --strip-components=1 -C /usr/local/bin \
 && uv --version

# The agent runs as an unprivileged user in the docker group (it can drive the inner daemon, as a
# developer can). The grader runs as root after every agent process is killed.
RUN groupadd -r docker && useradd -m -u 1000 -G docker -s /bin/bash agent
USER agent
RUN curl -fsSL https://claude.ai/install.sh | bash -s "${CLAUDE_CODE_VERSION}" \
 && /home/agent/.local/bin/claude --version
USER root
RUN ln -s /home/agent/.local/bin/claude /usr/local/bin/claude

# The inner daemon's storage must not sit on the outer overlay filesystem. This anonymous volume is
# removed with the container (`docker rm -v`).
VOLUME /var/lib/docker

COPY entrypoint.sh claude-agent.sh /opt/hb/
RUN chmod 0755 /opt/hb/*.sh && mkdir -p /trial/repo /trial/out /trial/plugin
# The repository is owned by `agent`; the grader runs git in it as root ("dubious ownership" otherwise).
RUN git config --system --add safe.directory /trial/repo
ENTRYPOINT ["/usr/bin/tini", "--", "/opt/hb/entrypoint.sh"]
