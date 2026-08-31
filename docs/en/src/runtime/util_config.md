# RuntimeConfig

> 📅 Last Updated: 2026/08/12

`runtime/util_config.py` provides runtime configuration loading functionality, currently used to read the log level from the project-level configuration file.

## Main Functions

### load_log_level_from_pyproject

```python
def load_log_level_from_pyproject() -> str: ...
```

Reads `log_level` from the `[tool.celestialflow]` section of the project-level ``pyproject.toml``.

- Searches upward for ``pyproject.toml`` starting from the current working directory
- Returns ``"INFO"`` when not found
- Raises ``InvalidOptionError`` if found but the value is not a valid level
- If parsing fails (invalid TOML format), continues searching upward

### Return Value

Returns an uppercase string (e.g., `"INFO"`, `"DEBUG"`), validated using `util_constant.LEVEL_DICT`.

## Usage Examples

```python
from celestialflow.runtime.util_config import load_log_level_from_pyproject

# Read log level from configuration
level = load_log_level_from_pyproject()
print(f"Current log level: {level}")
```

## Notes

- Only TOML-format configuration files are supported
- Valid log level values are defined by `util_constant.LEVEL_DICT`, including `TRACE`/`DEBUG`/`SUCCESS`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`
