# tests/runtime/test_errors.py

> 📅 Last Updated: 2026/11/13

## Purpose
Verifies the custom exception hierarchy in `celestialflow.runtime.util_errors`, ensuring that exception inheritance, default messages, and additional fields all meet expectations.

## Coverage Points
- Base exception: `CelestialFlowError`.
- Configuration & option errors: `ConfigurationError`, `InvalidOptionError` (with `field`, `value`, `allowed` fields and custom prefix).
- Graph structure errors: `GraphStructureError`, `DuplicateNodeError`, `UnknownNodeError`.
- Runtime and lifecycle: `RuntimeStateError`, `InitializationError`, `CelestialFlowTimeoutError` (also inherits `TimeoutError`), `UnconsumedError`.
- Task and logic: `TerminationMergeError`.
- External dependencies: `ReporterError`, `RemoteWorkerError`.

## Test Coverage Matrix

| Category | Case Count | Exceptions Covered |
|----------|------------|-------------------|
| Base Exceptions | 1 | `CelestialFlowError` |
| Configuration & Options | 6 | `ConfigurationError`, `InvalidOptionError` (with custom prefix; invalid field values such as `execution_mode` / `graph_mode` / `log_level`) |
| Graph Structure | 3 | `GraphStructureError`, `DuplicateNodeError`, `UnknownNodeError` |
| Runtime & Lifecycle | 4 | `RuntimeStateError`, `InitializationError`, `CelestialFlowTimeoutError`, `UnconsumedError` |
| External Services & Communication | 2 | `RemoteWorkerError`, `ReporterError` |
| Task & Logic | 1 | `TerminationMergeError` |
| **Total** | **17** | |

> **Exception classes not covered by this file**: `CallableParameterKindError` (currently no test instantiates it directly), `NodeNotFoundError` (covered by `tests/graph/test_graph.py`), `InvalidStructureError` (covered by `tests/graph/test_structure.py`), and `PersistedError` (covered by `tests/node/test_nodes.py`). This file only guarantees the construction, inheritance, and message contracts of the 13 exception classes in the table above.

## Key Scenarios
- Verify that exceptions inherit from the correct parent class (multi-inheritance chain verification, e.g., `InvalidOptionError → ConfigurationError → CelestialFlowError`).
- Verify that additional fields such as `field`, `value`, and `allowed` are preserved; `allowed` is normalized to a `tuple`.
- Verify the default message format `"{prefix} {field}: {value}. Valid options are {allowed}."`, as well as the custom prefix when `prefix="Bad"`.
- Verify that different invalid field values (e.g., `execution_mode`, `graph_mode`, `log_level`) are all handled uniformly through `InvalidOptionError` and expose field information.
- Verify that the default text and custom error messages are readable.

## How to Run

```bash
uv run pytest tests/runtime/test_errors.py -v
uv run pytest tests/runtime/test_errors.py -k "invalid_option or execution_mode" -v
uv run pytest tests/runtime/test_errors.py -k "timeout or termination or graph_structure" -v
```
