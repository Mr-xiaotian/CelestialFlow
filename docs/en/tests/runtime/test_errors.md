# Runtime Exception Tests (test_errors.py)

> 📅 Last Updated: 2026/07/16

## Purpose
Verifies the custom exception hierarchy in `celestialflow.runtime.util_errors`, ensuring that exception inheritance, default messages, and additional fields all meet expectations.

## Coverage Points
- Base exception: `CelestialFlowError`.
- Option errors: `InvalidOptionError`, `ExecutionModeError`, `StageModeError`, `ScheduleModeError`, `LogLevelError`, and their respective fields (`field`, `value`, `allowed`).
- Graph structure errors: `GraphStructureError`, `DuplicateNodeError`, `UnknownNodeError`.
- Runtime and lifecycle: `RuntimeStateError`, `InitializationError`, `CelestialFlowTimeoutError` (also inherits `TimeoutError`), `UnconsumedError`.
- Task and logic: `TerminationMergeError`.
- External dependencies: `ReporterError`, `RemoteWorkerError`.

## Test Coverage Matrix

| Category | Case Count | Exceptions Covered |
|----------|------------|-------------------|
| Base Exceptions | 1 | `CelestialFlowError` |
| Configuration & Options | 8 | `ConfigurationError`, `InvalidOptionError` (with custom prefix), `ExecutionModeError` (with custom mode), `StageModeError`, `LogLevelError`, `ScheduleModeError` |
| Graph Structure | 3 | `GraphStructureError`, `DuplicateNodeError`, `UnknownNodeError` |
| Runtime & Lifecycle | 4 | `RuntimeStateError`, `InitializationError`, `CelestialFlowTimeoutError`, `UnconsumedError` |
| External Services & Communication | 2 | `RemoteWorkerError`, `ReporterError` |
| Task & Logic | 1 | `TerminationMergeError` |

## Key Scenarios
- Verify that exceptions inherit from the correct parent class (multi-inheritance chain verification, e.g., `InvalidOptionError → ConfigurationError → CelestialFlowError`).
- Verify that additional fields such as `field`, `value`, and `allowed` are preserved.
- Verify that default text and custom error messages are readable.

## How to Run

```bash
pytest tests/runtime/test_errors.py -v
pytest tests/runtime/test_errors.py -k "invalid_option or execution_mode" -v
pytest tests/runtime/test_errors.py -k "timeout or termination or graph_structure" -v
```
