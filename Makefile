.PHONY: format build test

format:
	uv run ruff format .
	uv run ruff check --fix .

build:
	rm -rf dist
	uv build

test:
	uv run pytest tests
