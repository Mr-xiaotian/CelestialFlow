.PHONY: format build

format:
	uv run ruff format .
	uv run ruff check --fix .

build:
	rm -rf dist
	uv build
