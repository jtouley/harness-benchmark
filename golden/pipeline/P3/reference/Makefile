.PHONY: build stream test

DURATION ?= 60
PYTHON ?= python3
SBT ?= sbt -batch
VENV = .venv
DBT = $(VENV)/bin/dbt
DBT_ARGS = --project-dir transform --profiles-dir transform

# The dbt environment, from the pinned and hashed requirements; rebuilt only when they change.
$(VENV)/.installed: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes --no-deps -r requirements.txt
	touch $@

# Batch: raw files -> lake (Spark batch job) -> dbt models -> out/marts. Every step replaces its outputs.
build: $(VENV)/.installed
	$(SBT) "runMain pipeline.Batch"
	mkdir -p out/marts
	$(DBT) build $(DBT_ARGS) --exclude tag:stream

# Stream: consume for DURATION seconds into the lake (Structured Streaming), then update the
# incremental stream models. With no checkpoint the query starts over at batch 0, so the models are
# rebuilt in full: their incremental filters compare batch numbers kept from before the reset.
stream: $(VENV)/.installed
	@fresh=$$(test -d lake/_checkpoints/recentchange/query || echo --full-refresh); \
	set -x; \
	$(SBT) "runMain pipeline.Stream $(DURATION)" && \
	mkdir -p out/marts && \
	$(DBT) build $(DBT_ARGS) --select tag:stream $$fresh

# The ingestion's ScalaTest suites (small in-memory DataFrames on a local Spark).
test:
	$(SBT) test
