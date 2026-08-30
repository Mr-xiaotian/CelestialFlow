.PHONY: format build test

format:
	uv run ruff format .
	uv run ruff check --fix .

build:
	uv build --clear

test:
	uv run pytest tests
