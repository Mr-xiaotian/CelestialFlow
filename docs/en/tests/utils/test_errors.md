# Custom Exception Class Tests (test_errors.py)

> 📅 Last Updated: 2026/05/28

## Purpose

Validates instantiation, inheritance, and message completeness for all custom exception classes in `celestialflow.runtime.util_errors`, ensuring that each framework module can correctly raise and catch exceptions of the expected types.

## Core Test Targets

All custom exception classes, grouped into four categories:

| Group | Exception Classes | Description |
|-------|-------------------|-------------|
| Base | `CelestialFlowError` | Base class for all framework exceptions |
| Configuration & Options | `ConfigurationError`, `InvalidOptionError`, `ExecutionModeError`, `StageModeError`, `LogLevelError`, `ScheduleModeError` | Parameter validation and mode configuration errors |
| Graph Structure | `GraphStructureError`, `DuplicateNodeError`, `UnknownNodeError` | DAG topology and node validation errors |
| Runtime & External | `RuntimeStateError`, `InitializationError`, `CelestialFlowTimeoutError`, `UnconsumedError`, `RemoteWorkerError`, `ReporterError`, `CelestialTreeConnectionError`, `TaskFormatError`, `TerminationMergeError` | Lifecycle, external service, and task logic errors |

## Key Test Scenarios

- **Base class instantiation**: `CelestialFlowError("something went wrong")` is a subclass of `Exception`
- **Inheritance chain verification**: `ExecutionModeError` is an instance of both `CelestialFlowError` and `InvalidOptionError`
- **Field completeness**: `InvalidOptionError`'s `field`, `value`, and `allowed` attributes are correctly populated
- **Valid value enumeration**: `ExecutionModeError`, `StageModeError`, `LogLevelError`, etc. have `valid_modes` / `valid_levels` containing the correct enum values
- **Default messages**: `CelestialTreeConnectionError()` with no arguments produces a message containing `"CelestialTreeClient"`
- **`PersistedErrorRecord` is not tested in this file** (that type is covered in `test_types.py`)

## How to Run

```bash
# Run all
pytest tests/utils/test_errors.py -v

# Configuration exception tests only
pytest tests/utils/test_errors.py -k "config or option or execution or stage or log or schedule" -v

# Graph structure exception tests only
pytest tests/utils/test_errors.py -k "graph or duplicate or unknown" -v

# Runtime exception tests only
pytest tests/utils/test_errors.py -k "runtime or init or timeout or unconsumed" -v
```

## Performance Reference

| Test Class | Duration |
|------------|----------|
| `TestUtilErrors` | ~0.05s |

## Key Details

- The exception inheritance hierarchy is designed as `CelestialFlowError → ConfigurationError → InvalidOptionError → {specific error}`, ensuring flexible catch levels.
- `InvalidOptionError` automatically converts `allowed` to a tuple and formats it into a descriptive error message.

## Notes

- All exceptions raised by the framework should inherit from `CelestialFlowError` to allow users to catch them uniformly.
- Related implementation is in `src/celestialflow/runtime/util_errors.py`.
