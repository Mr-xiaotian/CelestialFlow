# src/celestialflow/runtime/util_config.py

> 📅 Last Updated: 2026/10/09

`runtime/util_config.py` provides runtime configuration loading functionality, used to read the log level, report URL, and report switch from the `[tool.celestialflow]` section of the project-level `pyproject.toml`.

## Default Constants

### DEFAULT_REPORT_URL

The default report URL `"http://127.0.0.1:5005"` used when `report_url` is not configured.

## Main Functions

### load_log_level_from_pyproject

```python
def load_log_level_from_pyproject() -> str: ...
```

Reads `log_level` from the `[tool.celestialflow]` section of the project-level `pyproject.toml`.

- Searches upward for `pyproject.toml` starting from the current working directory
- Returns `"INFO"` when not found
- Raises `InvalidOptionError` if found but the value is not a valid level
- If parsing fails (invalid TOML format), continues searching upward

Returns an uppercase string (e.g., `"INFO"`, `"DEBUG"`), validated using `util_constant.LEVEL_DICT`.

### load_report_url_from_pyproject

```python
def load_report_url_from_pyproject() -> str: ...
```

Reads `report_url` from the `[tool.celestialflow]` section of the project-level `pyproject.toml`.

- Searches upward for `pyproject.toml` starting from the current working directory
- Returns the default address `DEFAULT_REPORT_URL` when the corresponding configuration is not found
- If parsing fails (invalid TOML format), continues searching upward

### load_if_report_from_pyproject

```python
def load_if_report_from_pyproject() -> bool: ...
```

Reads `if_report` from the `[tool.celestialflow]` section of the project-level `pyproject.toml`.

- Searches upward for `pyproject.toml` starting from the current working directory
- Returns `False` when not configured
- The report switch and the report URL are decoupled: reporting is only enabled when explicitly configured as `true`; the mere presence of `report_url` no longer triggers reporting
- Throws `ConfigurationError` when the configured value is not a boolean
- If parsing fails (invalid TOML format), continues searching upward

## Usage Example

```python
from celestialflow.runtime.util_config import (
    DEFAULT_REPORT_URL,
    load_log_level_from_pyproject,
    load_report_url_from_pyproject,
    load_if_report_from_pyproject,
)

# Read the log level from the configuration
level = load_log_level_from_pyproject()
print(f"Current log level: {level}")

# Report URL and switch
url = load_report_url_from_pyproject()
if_report = load_if_report_from_pyproject()
print(f"Report URL: {url} (default {DEFAULT_REPORT_URL}), enabled: {if_report}")
```

## Notes

- Only TOML-format configuration files are supported
- Valid log level values are defined by `util_constant.LEVEL_DICT`, including `TRACE`/`DEBUG`/`SUCCESS`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`