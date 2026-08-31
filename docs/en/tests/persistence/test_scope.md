# Scope Management Tests (test_scope.py)

> 📅 Last Updated: 2026/08/26

## Purpose

Verifies the `funnel_scope()` context manager in `celestialflow.persistence.core_scope` for automatic lifecycle management of the global `LogSpout` / `LifecycleSpout`, ensuring the background thread is started upon entering the scope, and properly cleaned up and persisted upon exit.

## Core Test Objects

- `funnel_scope()`: A context manager that automatically manages the start and stop of the global log/lifecycle spouts.
- `get_log_spout()` / `get_lifecycle_spout()`: Get the global singleton spouts.
- `get_log_inlet()` / `get_lifecycle_inlet()`: Get the corresponding inlet entry points.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Target |
|--------|--------|---------|
| `TestFunnelScope` | 4 | Lifecycle management, reusability, exception safety, single-layer scope semantics |

## Key Test Scenarios

### `test_funnel_scope_starts_and_stops_global_spouts`

Verifies that entering `funnel_scope()` starts the background threads of two global spouts, and that exit automatically stops and cleans up thread references.

- Within the scope, asserts that `log_spout._thread` and `lifecycle_spout._thread` are non-empty and alive.
- Writes logs via `get_log_inlet().start_graph()`, and writes to sqlite via `get_lifecycle_inlet().task_in()` + `task_success()`.
- After exiting the scope, asserts that `_thread` is `None`, and the log file and sqlite file have been persisted and contain the correct content.

### `test_funnel_scope_is_reusable`

Verifies that `funnel_scope()` supports multiple independent enter/exit operations.

- Enters and exits twice, asserting on each entry that the thread is recreated and alive, and that the thread reference is `None` after exit.

### `test_funnel_scope_wraps_body_error_and_stops_spouts`

Verifies that when an exception is raised inside the scope, `funnel_scope()` still performs finalization cleanup.

- Raises a `RuntimeError` inside `funnel_scope()`.
- Asserts that the exception is raised as an `ExceptionGroup` (matches `"Errors occurred during funnel scope"`).
- After exit, asserts that `_thread` is `None` for both global spouts.

### `test_funnel_scope_does_not_claim_nested_reuse`

Verifies that the current `funnel_scope()` is a single-layer scope and does not validate nested-reuse semantics.

- Enters `funnel_scope()` once for a simple operation, then exits, asserting that `_thread` has been cleaned up.

## How to Run

```bash
# Run all
pytest tests/persistence/test_scope.py -v

# Match by keyword
pytest tests/persistence/test_scope.py -k "lifecycle" -v
pytest tests/persistence/test_scope.py -k "error" -v
pytest tests/persistence/test_scope.py -k "reusable" -v
```

## Notes

- Each case uses the `autouse` fixture `_cleanup_global_spouts` to clean up the global spouts before and after, avoiding cross-contamination of background threads and file state.
- Tests use `monkeypatch.chdir(tmp_path)` to switch the working directory, ensuring log and sqlite files are written to a temporary path.
- The related implementation is located at `src/celestialflow/persistence/core_scope.py`.
