# The P3 toolchain: everything `make build` and `make stream` need, pinned, in one container.
# Nothing is installed on the host. Both base images are pinned by digest (multi-arch indexes, so the
# same file builds on x86-64 runners and on Apple Silicon); sbt is checked against its sha256.
#
#   docker build -t hb-pipeline-p3 golden/pipeline/P3/image
#
# JDK 17 (Temurin 17.0.20.1+1), Python 3.12.15, sbt 1.12.15. Scala 2.13.8 and Spark 3.5.9 are pinned
# by the task's build.sbt and fetched by sbt; pyspark 3.5.9, dbt-core and dbt-spark by its
# requirements.txt. The grader's own dependencies (duckdb, pyyaml) sit apart in /opt/grader, outside
# the project's environment.

FROM eclipse-temurin:17.0.20.1_1-jdk-noble@sha256:fb79620c3f6ee8f1c7530a8dc4fd49e3b410bcef037694ad4858a1553bac4170 AS jdk

FROM python:3.12.15-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258

ARG SBT_VERSION=1.12.15
ARG SBT_SHA256=d8c215f47b879002a030f930410d83e9d138015362411f62e294c145b9f8a931

ENV JAVA_HOME=/opt/java/openjdk \
    LANG=C.UTF-8 \
    TZ=UTC
COPY --from=jdk /opt/java/openjdk /opt/java/openjdk

RUN apt-get update \
 && apt-get install -y --no-install-recommends make git curl ca-certificates procps \
 && rm -rf /var/lib/apt/lists/* \
 && curl -fsSL -o /tmp/sbt.tgz "https://github.com/sbt/sbt/releases/download/v${SBT_VERSION}/sbt-${SBT_VERSION}.tgz" \
 && echo "${SBT_SHA256}  /tmp/sbt.tgz" | sha256sum -c - \
 && tar -xzf /tmp/sbt.tgz -C /opt \
 && rm /tmp/sbt.tgz \
 && python3 -m venv /opt/grader \
 && /opt/grader/bin/pip install --no-cache-dir duckdb==1.5.6 pyyaml==6.0.3

# Every download cache under /cache, so one volume keeps them between containers.
ENV PATH=/opt/java/openjdk/bin:/opt/sbt/bin:$PATH \
    COURSIER_CACHE=/cache/coursier \
    SBT_OPTS="-Dsbt.ivy.home=/cache/ivy -Dsbt.boot.directory=/cache/sbt-boot -Dsbt.global.base=/cache/sbt-global -Dsbt.server.forcestart=false -Xss4m" \
    PIP_CACHE_DIR=/cache/pip \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /work
