# Runtime Exception Tests (test_errors.py)

> 📅 Last Updated: 2026/06/11

## Purpose
Verifies the custom exception hierarchy in `celestialflow.runtime.util_errors`, ensuring that exception inheritance, default messages, and additional fields all meet expectations.

## Coverage Points
- Base exceptions: `CelestialFlowError`, `ConfigurationError`, `RuntimeStateError`, `CelestialFlowTimeoutError` (also inherits `TimeoutError`).
- Option errors: `InvalidOptionError`, `ExecutionModeError`, `StageModeError`, `ScheduleModeError`, `LogLevelError`, and their respective fields (`field`, `value`, `allowed`).
- Graph structure errors: `GraphStructureError`, `DuplicateNodeError`, `UnknownNodeError`.
- Runtime and lifecycle: `RuntimeStateError`, `InitializationError`, `UnconsumedError`.
- Task and logic: `TaskFormatError`, `TerminationMergeError`.
- External dependencies: `ReporterError`, `RemoteWorkerError`, `CelestialTreeConnectionError` (supports default and custom messages).

## Test Coverage Matrix

| Category | Case Count | Exceptions Covered |
|----------|------------|-------------------|
| Base Exceptions | 1 | `CelestialFlowError` |
| Configuration & Options | 8 | `ConfigurationError`, `InvalidOptionError` (with custom prefix), `ExecutionModeError` (with custom mode), `StageModeError`, `LogLevelError`, `ScheduleModeError` |
| Graph Structure | 3 | `GraphStructureError`, `DuplicateNodeError`, `UnknownNodeError` |
| Runtime & Lifecycle | 4 | `RuntimeStateError`, `InitializationError`, `CelestialFlowTimeoutError`, `UnconsumedError` |
| External Services & Communication | 3 | `RemoteWorkerError`, `ReporterError`, `CelestialTreeConnectionError` (default/custom message) |
| Task & Logic | 2 | `TaskFormatError`, `TerminationMergeError` |

## Key Scenarios
- Verify that exceptions inherit from the correct parent class (multi-inheritance chain verification, e.g., `InvalidOptionError → ConfigurationError → CelestialFlowError`).
- Verify that additional fields such as `field`, `value`, and `allowed` are preserved.
- Verify that default text and custom error messages are readable.

## How to Run

```bash
pytest tests/runtime/test_errors.py -v
pytest tests/runtime/test_errors.py -k "invalid_option or connection" -v
pytest tests/runtime/test_errors.py -k "timeout or task_format or termination" -v
```
