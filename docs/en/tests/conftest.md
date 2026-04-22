# conftest.py Test Configuration Documentation

## Test Purpose

`conftest.py` is a pytest local plugin file responsible for loading project-level environment variable configuration before the test session begins, ensuring all test cases share consistent external service connection parameters (such as Redis, CelestialTree, Reporter, etc.).

## Test Scope

- **Environment initialization**: Automatically executed before pytest collects tests.
- **Configuration loading**: Loads the `.env` file from the project root directory via `python-dotenv`.
- **Zero-intrusion design**: Contains no fixture definitions or hook functions, maintaining minimal responsibility.

## Dependencies

| Dependency | Purpose |
|------------|---------|
| `python-dotenv` | Loads environment variables from `.env` file |

## Potential Issues and Notes

### 1. Missing `.env` File
If the project root directory lacks a `.env` file, `load_dotenv()` will silently skip without raising an error. This means tests that depend on environment variables (such as Redis tests in `demo_stages.py`) may fail or be skipped due to empty configuration.

**Recommendation**: In CI/CD environments, inject environment variables directly rather than relying on `.env` files.

### 2. Environment Variable Pollution
`load_dotenv()` does not overwrite existing environment variables by default (`override=False`). If the host machine already defines a variable with the same name (e.g., `REDIS_HOST`), the actual value used may differ from what's in the `.env` file.

**Troubleshooting**:
```bash
pytest tests/ --collect-only -v
# Check actual environment variable values
python -c "import os; print(os.getenv('REDIS_HOST'))"
```

### 3. Compatibility with uv Virtual Environments
When using `uv run` on Windows, a corrupted virtual environment may cause `dotenv` loading to fail. In such cases, check the integrity of `.venv`, or run directly with `python -m pytest`.

## How to Run

This file does not need to be run manually; pytest loads it automatically:
```bash
pytest tests/
```

## Related Files

- `.env`: Environment variable definition file
- `tests/demo_stages.py`: The demo test with the most environment variable dependencies
