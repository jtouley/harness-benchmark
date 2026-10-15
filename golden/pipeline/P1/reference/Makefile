.PHONY: build stream

DURATION ?= 60
UV ?= uv
DBT = $(UV) run --frozen dbt
DBT_ARGS = --project-dir transform --profiles-dir transform

# Batch: raw files -> lake -> dbt models -> out/marts. Every step replaces its outputs.
build:
	$(UV) run --frozen python -m pipeline.batch
	mkdir -p out/marts
	$(DBT) build $(DBT_ARGS) --exclude tag:stream

# Stream: consume for DURATION seconds into the lake, then update the incremental stream models.
stream:
	$(UV) run --frozen python -m pipeline.stream --duration $(DURATION)
	mkdir -p out/marts
	$(DBT) build $(DBT_ARGS) --select tag:stream

