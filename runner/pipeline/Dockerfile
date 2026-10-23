# The pipeline family's trial images: the runner image plus each task's toolchain, with every package
# the skeleton pins already in a cache, so no trial reads a package index (golden/pipeline/README.md,
# "A trial on the isolated runner"). Built by runner/pipeline/build.sh, whose context holds only the
# four skeletons: no reference, key, capture or grader is ever in this image.
#
#   target py  (P1, P2, P4): make, Python 3.12 (uv-managed), the P1, P2 and P4 locks in the uv cache, the
#                        grader's own environment in /opt/grader (duckdb, pyyaml).
#   target p3  (P3):     py, plus JDK 17, sbt, the Spark/Scala/ScalaTest closure in the coursier and ivy
#                        caches, and the dbt-spark closure (with pyspark) in a wheelhouse.
ARG BASE=harness-benchmark/runner:local
FROM eclipse-temurin:17.0.20.1_1-jdk-noble@sha256:fb79620c3f6ee8f1c7530a8dc4fd49e3b410bcef037694ad4858a1553bac4170 AS jdk

FROM ${BASE} AS py
ARG PYTHON_VERSION=3.12
RUN apt-get update && apt-get install -y --no-install-recommends make && rm -rf /var/lib/apt/lists/*
ENV UV_CACHE_DIR=/opt/hb/cache/uv UV_PYTHON_INSTALL_DIR=/opt/hb/python UV_PYTHON_BIN_DIR=/opt/hb/bin \
    UV_LINK_MODE=copy
# Python 3.12 for the tasks (python3 on the toolchain PATH), and the grader's own environment.
RUN uv python install "${PYTHON_VERSION}" \
 && ln -sf "$(uv python find "${PYTHON_VERSION}")" /opt/hb/bin/python3 \
 && ln -sf "$(uv python find "${PYTHON_VERSION}")" /opt/hb/bin/python \
 && UV_CACHE_DIR=/tmp/grader-cache uv venv -q --python "${PYTHON_VERSION}" /opt/grader \
 && UV_CACHE_DIR=/tmp/grader-cache uv pip install -q --python /opt/grader/bin/python duckdb==1.5.6 pyyaml==6.0.3 \
 && rm -rf /tmp/grader-cache
# Warm the uv cache from the P1, P2 and P4 locks, then drop the environments: only the cache stays.
COPY P1/skeleton /tmp/warm/P1
COPY P2/skeleton /tmp/warm/P2
COPY P4/skeleton /tmp/warm/P4
RUN cd /tmp/warm/P1 && uv sync -q --frozen && cd /tmp/warm/P2 && uv sync -q --frozen && cd /tmp/warm/P4 && uv sync -q --frozen \
 && rm -rf /tmp/warm && chown -R agent:agent /opt/hb/cache
COPY toolchain-py.env /opt/hb/toolchain.env

FROM py AS p3
ARG SBT_VERSION=1.12.15
ARG SBT_SHA256=d8c215f47b879002a030f930410d83e9d138015362411f62e294c145b9f8a931
COPY --from=jdk /opt/java/openjdk /opt/java/openjdk
ENV JAVA_HOME=/opt/java/openjdk PATH=/opt/hb/bin:/opt/java/openjdk/bin:/opt/sbt/bin:$PATH \
    COURSIER_CACHE=/opt/hb/cache/coursier PIP_CACHE_DIR=/opt/hb/cache/pip \
    SBT_OPTS="-Dsbt.ivy.home=/opt/hb/cache/ivy -Dsbt.boot.directory=/opt/hb/cache/sbt-boot -Dsbt.global.base=/opt/hb/cache/sbt-global -Dsbt.server.forcestart=false -Xss4m"
RUN curl -fsSL -o /tmp/sbt.tgz "https://github.com/sbt/sbt/releases/download/v${SBT_VERSION}/sbt-${SBT_VERSION}.tgz" \
 && echo "${SBT_SHA256}  /tmp/sbt.tgz" | sha256sum -c - \
 && tar -xzf /tmp/sbt.tgz -C /opt && rm /tmp/sbt.tgz
# Warm sbt: the launcher, Scala, Spark and ScalaTest, and the compiler bridge (a throwaway source and
# test make sbt compile both configurations and run a forked JVM once).
COPY P3/skeleton /tmp/warm/P3
RUN cd /tmp/warm/P3 && mkdir -p src/main/scala src/test/scala \
 && printf 'object Warm { def main(a: Array[String]): Unit = println(org.apache.spark.SPARK_VERSION) }\n' \
      > src/main/scala/Warm.scala \
 && printf 'class WarmSpec extends org.scalatest.funsuite.AnyFunSuite { test("w") { assert(true) } }\n' \
      > src/test/scala/WarmSpec.scala \
 && sbt -batch "runMain Warm" test
# The dbt-spark closure as the files PyPI serves (their hashes are the ones requirements.txt pins),
# plus the build backend pyspark's source archive needs, so `pip install --require-hashes` works with
# no index; one install builds pyspark's wheel into the pip cache.
RUN cd /tmp/warm/P3 && python3 -m venv /tmp/v \
 && /tmp/v/bin/pip download -q --no-deps --require-hashes -r requirements.txt -d /opt/hb/wheelhouse \
 && /tmp/v/bin/pip download -q setuptools wheel -d /opt/hb/wheelhouse \
 && PIP_NO_INDEX=1 PIP_FIND_LINKS=/opt/hb/wheelhouse /tmp/v/bin/pip install -q --require-hashes --no-deps \
      -r requirements.txt \
 && rm -rf /tmp/v /tmp/warm && chown -R agent:agent /opt/hb/cache
COPY toolchain-p3.env /opt/hb/toolchain.env
