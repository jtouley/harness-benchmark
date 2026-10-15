.PHONY: build stream validate

DURATION ?= 60
UV ?= uv
ENGINE = $(UV) run --frozen python -m engine
DBT = $(UV) run --frozen dbt
DBT_ARGS = --project-dir transform --profiles-dir transform

# Batch: raw files -> lake (pipelines/batch.yml) -> dbt models -> out/marts. Every step replaces its outputs.
build: validate
	$(ENGINE) run pipelines/batch.yml
	mkdir -p out/marts
	$(DBT) build $(DBT_ARGS) --exclude tag:stream

# Stream: consume for DURATION seconds into the lake (pipelines/stream.yml), then update the
# incremental stream models.
stream: validate
	$(ENGINE) run pipelines/stream.yml --duration $(DURATION)
	mkdir -p out/marts
	$(DBT) build $(DBT_ARGS) --select tag:stream

# Check every pipeline file against the schema; a problem is reported as file:line: problem.
validate:
	$(ENGINE) validate pipelines/*.yml
