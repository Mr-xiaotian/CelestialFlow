# Runtime Exception Tests (test_errors.py)

> Last Updated: 2026/06/05

## Purpose
Validates the custom exception hierarchy in `celestialflow.runtime.util_errors`, ensuring inheritance, default messages, and extra fields all behave as expected.

## Coverage
- Base exceptions: `CelestialFlowError`, `ConfigurationError`, `RuntimeStateError`.
- Option errors: `InvalidOptionError`, `ExecutionModeError`, `StageModeError`, `ScheduleModeError`, `LogLevelError`.
- Graph and runtime errors: `DuplicateNodeError`, `UnknownNodeError`, `InitializationError`, `UnconsumedError`.
- External dependency errors: `ReporterError`, `RemoteWorkerError`, `CelestialTreeConnectionError`.

## Key Scenarios
- Check whether each exception inherits from the correct parent.
- Check whether extra fields such as `field`, `value`, and `allowed` are preserved.
- Check whether default messages and custom messages remain readable.

## How to Run

```bash
pytest tests/runtime/test_errors.py -v
pytest tests/runtime/test_errors.py -k "invalid_option or connection" -v
```

