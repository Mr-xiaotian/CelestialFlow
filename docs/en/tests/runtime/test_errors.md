# Runtime Exception Tests (test_errors.py)

> 📅 Last Updated: 2026/08/19

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

## Key Scenarios
- Verify that exceptions inherit from the correct parent class (multi-inheritance chain verification, e.g., `InvalidOptionError → ConfigurationError → CelestialFlowError`).
- Verify that additional fields such as `field`, `value`, and `allowed` are preserved.
- Verify that different invalid field values (e.g., `execution_mode`, `graph_mode`, `log_level`) are all handled uniformly through `InvalidOptionError` and expose field information.
- Verify that default text and custom error messages are readable.

## How to Run

```bash
pytest tests/runtime/test_errors.py -v
pytest tests/runtime/test_errors.py -k "invalid_option or execution_mode" -v
pytest tests/runtime/test_errors.py -k "timeout or termination or graph_structure" -v
```
