# TaskErrors

> 📅 Last Updated: 2026/05/09

The TaskErrors module defines custom exception classes used in the framework.

## Exception Hierarchy

```
CelestialFlowError
├── ConfigurationError
│   └── InvalidOptionError
│       ├── ExecutionModeError
│       ├── StageModeError
│       ├── LogLevelError
│       └── ScheduleModeError
├── RemoteWorkerError
├── CelestialTreeConnectionError
├── UnconsumedError
```

## Base Class

### CelestialFlowError

Base class for all custom exceptions.

```python
class CelestialFlowError(Exception):
    """Base class for all CelestialFlow custom exceptions"""
    pass
```

## Configuration Exceptions

### ConfigurationError

Base class for configuration errors (invalid parameters, unsupported combinations, etc.).

```python
class ConfigurationError(CelestialFlowError):
    """Configuration error base class"""
    pass
```

### InvalidOptionError

A configuration option value is not valid (not in the allowed set).

```python
class InvalidOptionError(ConfigurationError):
    def __init__(
        self,
        field: str,
        value: Any,
        allowed: Iterable[Any],
        *,
        prefix: str = "Invalid",
    ):
        """
        :param field: Configuration field name
        :param value: Actual value
        :param allowed: List of allowed values
        :param prefix: Error message prefix
        """
```

### ExecutionModeError

`execution_mode` configuration error.

```python
class ExecutionModeError(InvalidOptionError):
    """Invalid execution_mode configuration error"""

    def __init__(self, execution_mode: str, valid_modes=None):
        # valid_modes defaults to ("serial", "thread", "async")
```

### StageModeError

`stage_mode` configuration error.

```python
class StageModeError(InvalidOptionError):
    """Invalid stage_mode configuration error"""

    def __init__(self, stage_mode: str, valid_modes=None):
        # valid_modes defaults to ("serial", "thread")
```

### LogLevelError

`log_level` configuration error.

```python
class LogLevelError(InvalidOptionError):
    """Invalid log_level configuration error"""

    def __init__(self, log_level: str, valid_levels=None):
        # valid_levels defaults to ("TRACE", "DEBUG", "SUCCESS", "INFO", "WARNING", "ERROR", "CRITICAL")
```

## Runtime Exceptions

### RemoteWorkerError

Exception thrown when a remote worker (e.g., Go Worker) fails to execute.

```python
class RemoteWorkerError(CelestialFlowError):
    pass
```

### ScheduleModeError

`schedule_mode` configuration error.

```python
class ScheduleModeError(InvalidOptionError):
    """Invalid schedule_mode configuration error"""

    def __init__(self, schedule_mode: str, valid_modes=None):
        # valid_modes defaults to ("eager", "staged")
```

### CelestialTreeConnectionError

CelestialTree connection error.

```python
class CelestialTreeConnectionError(CelestialFlowError):
    def __init__(self, message: str = "CelestialTreeClient is not available"):
        ...
```

### UnconsumedError

Exception class for marking unconsumed tasks.

```python
class UnconsumedError(CelestialFlowError):
    """Exception class for marking unconsumed tasks"""
    pass
```

When `TaskGraph` stops, it collects all unconsumed tasks and records them as `UnconsumedError`.

## Error Handling Strategy

In `TaskExecutor`, exceptions are categorized into two types:

1. **Retryable Exceptions**: If the exception type is in the `retry_exceptions` list and the retry limit has not been reached, the framework will automatically retry the task.
2. **Non-Retryable Exceptions**: The task is marked as failed, an error log is recorded, and it is placed in the `fail_queue`.

## Error Persistence

`TaskGraph` automatically persists all unhandled errors (including retry failures and UnconsumedError) to the local `fallback/` directory in JSONL format.

Each error record contains:
- Timestamp
- Stage tag
- Error message
- Original task data
- Error ID

## Usage Example

### Catching Specific Exceptions

```python
from celestialflow.runtime.util_errors import (
    ExecutionModeError,
    StageModeError,
    RemoteWorkerError,
)

try:
    stage.set_execution_mode("invalid_mode")
except ExecutionModeError as e:
    print(f"Invalid execution mode: {e.execution_mode}")
    print(f"Valid options: {e.valid_modes}")
```

### Adding Retryable Exceptions

```python
executor = TaskExecutor("Processor", process, max_retries=3)
executor.add_retry_exceptions(ConnectionError, TimeoutError)
```

## Notes

1. **Error Propagation**: `RemoteWorkerError` contains error information returned by the remote worker
2. **Logging**: All exceptions are logged
3. **Graceful Degradation**: Even when exceptions occur, the framework attempts to properly clean up resources
