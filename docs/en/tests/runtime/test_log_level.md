# tests/runtime/test_log_level.py

> 📅 Last Updated: 2026/10/30

## Purpose
Validates the input normalization and error branches of `celestialflow.runtime.util_log_level.normalize_log_level`: level names are case-insensitive with leading/trailing whitespace ignored; unknown levels and non-string inputs raise `InvalidOptionError` and `ConfigurationError` respectively.

## Core Test Objects
- `normalize_log_level(log_level)`: Validates and normalizes the log level, returning the uppercase key in `LEVEL_DICT`; a non-string raises `ConfigurationError`, and a value outside the allowed set raises `InvalidOptionError`.
- `DEFAULT_LOG_LEVEL`: The default value (`"INFO"`) used when the runtime entry point does not explicitly specify a log level; it is defined in the same module and serves as the parameter default for entries such as `run` / `restore_db`.
- `InvalidOptionError`: Inherits from `ConfigurationError`, carries `field` / `value` / `allowed`, where the allowed set comes from the keys of `LEVEL_DICT`: `TRACE`, `DEBUG`, `SUCCESS`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goal |
|--------|--------|---------|
| `TestNormalizeLogLevel` | 3 | Case and whitespace normalization, unknown level rejection, non-string rejection |

## Key Test Scenarios

### `TestNormalizeLogLevel`
1. **Normalization** (`test_uppercases_and_strips`): `normalize_log_level(" error ")` returns `"ERROR"`, showing that `strip().upper()` takes effect.
2. **Rejecting an unknown level** (`test_rejects_unknown_level`): `normalize_log_level("VERBOSE")` raises `InvalidOptionError`.
3. **Rejecting non-strings** (`test_rejects_non_string`): `normalize_log_level(30)` raises `ConfigurationError` (the type check runs before the value check).

## Test Focus
- **Input tolerance**: Letter case and leading/trailing whitespace do not affect resolution of a legal level.
- **Layered errors**: type errors go through `ConfigurationError`, while value errors go through the more specific `InvalidOptionError`, so callers can catch at the granularity they need.
- **Single source for the allowed set**: legal levels are determined by the keys of `LEVEL_DICT`, avoiding the test and the implementation each maintaining their own list.

## Usage Example

```python
from celestialflow.runtime.util_errors import ConfigurationError, InvalidOptionError
from celestialflow.runtime.util_log_level import DEFAULT_LOG_LEVEL, normalize_log_level

print(DEFAULT_LOG_LEVEL)                 # INFO
print(normalize_log_level(" debug "))    # DEBUG

try:
    normalize_log_level("VERBOSE")
except InvalidOptionError as error:
    print(error.field)    # log level
    print(error.allowed)  # tuple of allowed levels

try:
    normalize_log_level(30)  # type: ignore[arg-type]
except ConfigurationError as error:
    print(error)  # log level must be a string, got 30.
```

## How to Run

```bash
# Run all
pytest tests/runtime/test_log_level.py -v

# Run only the normalization case
pytest tests/runtime/test_log_level.py -k "uppercases" -v

# Run only the error branch cases
pytest tests/runtime/test_log_level.py -k "rejects" -v
```

## Important Details
- `normalize_log_level` first uses `isinstance` to strictly check for a string, so inputs such as integers and `None` never reach the level comparison branch.
- The return value is always an uppercase key in `LEVEL_DICT`, which callers can use directly for the level setting of a log filter.
- All cases are pure in-memory computation with no I/O side effects.

## Notes
- The related implementation is located at `src/celestialflow/runtime/util_log_level.py`; `util_*` is an internal utility of the runtime entry point and is not re-exported from the `celestialflow.runtime` package.
- This file does not assert on `DEFAULT_LOG_LEVEL` separately; the default value is reflected in the parameter defaults of the runtime entries that need a log level.
