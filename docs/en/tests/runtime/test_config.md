# tests/runtime/test_config.py

> 📅 Last Updated: 2026/10/30

## Purpose
Validates the construction checks and address normalization of `celestialflow.runtime.ReportConfig`: the default address fallback, stripping of leading/trailing whitespace and trailing slashes, and whether invalid inputs such as non-strings, empty strings, and illegal schemes are rejected via `ConfigurationError`. It also verifies that the configuration object is immutable.

## Core Test Objects
- `ReportConfig`: A frozen dataclass (`frozen=True, slots=True`) whose only field is `url`; validation and normalization are completed in `__post_init__` at construction time.
- `DEFAULT_REPORT_URL`: The default reporting address (`http://127.0.0.1:5005`) used when no address is explicitly specified, re-exported by the `celestialflow.runtime` package.
- `ConfigurationError`: The custom configuration exception raised uniformly for illegal addresses.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goal |
|--------|--------|---------|
| `TestReportConfig` | 6 | Default address, whitespace and trailing-slash normalization, empty-string rejection, non-`http`/`https` scheme rejection, non-string rejection, object frozenness |

## Key Test Scenarios

### `TestReportConfig`
1. **Default address** (`test_default_url`): for a no-argument construction, `ReportConfig().url == DEFAULT_REPORT_URL`.
2. **Normalized to a slash-free address** (`test_strips_whitespace_and_trailing_slash`): the `url` of `ReportConfig(url=" http://127.0.0.1:9000/ ")` is `"http://127.0.0.1:9000"`, avoiding a double slash when concatenating with the reporting endpoint.
3. **Rejecting a whitespace-only string** (`test_rejects_empty_url`): `url="   "` becomes empty after stripping whitespace, raising `ConfigurationError`.
4. **Rejecting non-HTTP schemes** (`test_rejects_non_http_scheme`): `url="ftp://127.0.0.1:9000"` raises `ConfigurationError`.
5. **Rejecting non-strings** (`test_rejects_non_string_url`): `url=5005` raises `ConfigurationError`.
6. **Immutability** (`test_is_frozen`): assigning to `url` after construction raises `AttributeError`.

## Test Focus
- **Validation before startup**: the address is validated at `ReportConfig` construction time, so an illegal configuration fails before the runtime resources start.
- **Normalization**: leading/trailing whitespace is removed by `strip()` and trailing slashes by `rstrip("/")`, keeping endpoint path concatenation stable.
- **Explicit opt-in semantics**: whether reporting is enabled is decided by whether a `ReportConfig` is passed to the runtime entry point; `ReportConfig` itself is no longer a combined "switch + address" configuration.
- **Clear failure mode**: every illegal address is rejected with `ConfigurationError` instead of silently falling back to the default value.

## How to Run

```bash
# Run all
pytest tests/runtime/test_config.py -v

# Run only the default address and normalization cases
pytest tests/runtime/test_config.py -k "default_url or strips_whitespace" -v

# Run only the illegal input and frozen-related cases
pytest tests/runtime/test_config.py -k "rejects or frozen" -v
```

## Important Details
- In the implementation, `url` is validated with `urlsplit`: the scheme must be `http` / `https` and `netloc` must be present (so addresses lacking a host, such as `http://`, are also rejected); the test cases cover the illegal-scheme branch with `ftp://`.
- Because `slots=True` and `frozen=True` are set, instances can neither gain attributes dynamically nor have `url` overwritten after construction.
- All cases are pure in-memory construction with no file/network side effects.

## Notes
- The related implementation is located at `src/celestialflow/runtime/core_config.py`, and public symbols are re-exported by `src/celestialflow/runtime/__init__.py`.
- The host project's `pyproject.toml` no longer participates in reading the reporting configuration; the configuration must be passed in explicitly by the caller.
