.PHONY: build

UV ?= uv

# Batch: raw files -> lake -> DuckDB models -> out/marts. Every step replaces its outputs.
build:
	$(UV) run --frozen python -m pipeline.build
