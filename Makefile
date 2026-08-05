.PHONY: format build

format:
	uv run ruff format .

build:
	rm -rf dist
	uv build
