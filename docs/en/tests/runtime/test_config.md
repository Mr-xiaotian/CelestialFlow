# tests/runtime/test_config.py

> 📅 Last Updated: 2026/10/09

## Purpose
Validates the `load_report_url_from_pyproject` and `load_if_report_from_pyproject` functions in `celestialflow.runtime.util_config`, ensuring that they can correctly read the reporting URL and reporting switch from the `[tool.celestialflow]` section of the project-level `pyproject.toml`, and fall back to defaults / raise `ConfigurationError` when the configuration is missing or invalid.

## Core Test Objects
- `load_report_url_from_pyproject()`: Reads `report_url`; returns `DEFAULT_REPORT_URL` (`http://127.0.0.1:5005`) when not configured or when there is no `pyproject.toml`.
- `load_if_report_from_pyproject()`: Reads `if_report`; returns `False` when not configured or when there is no `pyproject.toml`; raises `ConfigurationError` when the configuration is non-boolean.
- `DEFAULT_REPORT_URL`: The default constant for the reporting address, used as the fallback when there is no configuration.

## Test Helpers
- `tmp_path` + `monkeypatch.chdir`: writes a `pyproject.toml` in the temporary directory before calling the functions under test, isolating them from dependence on the real working directory.

## Key Test Scenarios

### `load_report_url_from_pyproject`
1. **Reading a configured address** (`test_load_report_url_reads_report_url`): when `pyproject.toml` configures `report_url = "http://127.0.0.1:9000"`, it returns that address.
2. **Default value when not configured** (`test_load_report_url_defaults_when_absent`): returns `DEFAULT_REPORT_URL` when only `log_level` is present without `report_url`.
3. **No `pyproject.toml`** (`test_load_report_url_defaults_without_pyproject`): returns `DEFAULT_REPORT_URL` in an empty directory.

### `load_if_report_from_pyproject`
1. **Reading a configured switch** (`test_load_if_report_reads_true`): returns `True` when `if_report = true`.
2. **Default off when not configured** (`test_load_if_report_defaults_to_false`): returns `False` when only `report_url` is configured without `if_report` (the switch is decoupled from the address).
3. **No `pyproject.toml`** (`test_load_if_report_returns_false_without_pyproject`): returns `False` in an empty directory.
4. **Non-boolean configuration throws** (`test_load_if_report_rejects_non_boolean`): raises `ConfigurationError` when `if_report = "yes"`.

## Test Focus
- **Default fallback**: both the reporting address and the switch have explicit defaults when configuration is missing.
- **Switch decoupling**: the presence of `report_url` does not implicitly enable reporting; `if_report` must be explicitly `true`.
- **Invalid input**: a non-boolean `if_report` is rejected via `ConfigurationError` rather than silently ignored.

## How to Run

```bash
# Run all
pytest tests/runtime/test_config.py -v

# Run report URL related tests only
pytest tests/runtime/test_config.py -k "report_url" -v

# Run report switch related tests only
pytest tests/runtime/test_config.py -k "if_report" -v
```

## Notes
- The related implementation is in `src/celestialflow/runtime/util_config.py`.
- All cases switch the working directory via `monkeypatch.chdir`, so the tests are fast and have no real network/file side effects.