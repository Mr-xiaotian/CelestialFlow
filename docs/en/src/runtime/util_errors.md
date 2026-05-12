# TaskErrors

> 📅 Last updated: 2026/05/08

The TaskErrors module defines the custom exception classes used in the framework.

## Exception Hierarchy

```
CelestialFlowError
├── ConfigurationError
│   └── InvalidOptionError
│       ├── ExecutionModeError
│       ├── StageModeError
│       ├── ScheduleModeError
│       └── LogLevelError
├── RemoteWorkerError
├── UnconsumedError
├── PickleError
└── CelestialTreeConnectionError
```

## Base Class

### CelestialFlowError

Base class for all custom exceptions.

```python
class CelestialFlowError(Exception):
    """Base class for all CelestialFlow custom exceptions"""
    pass
```

## Configuration-Related Exceptions

### ConfigurationError

Base class for configuration errors (invalid parameters, unsupported combinations, etc.).

```python
class ConfigurationError(CelestialFlowError):
    """Base class for configuration errors"""
    pass
```

### InvalidOptionError

Raised when a configuration option value is not in the allowed set.

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
        :param field: Configuration option name
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
        # valid_modes defaults to ("serial", "thread", "process")
```

### LogLevelError

`log_level` configuration error.

```python
class LogLevelError(InvalidOptionError):
    """Invalid log_level configuration error"""

    def __init__(self, log_level: str, valid_levels=None):
        # valid_levels defaults to ("TRACE", "DEBUG", "SUCCESS", "INFO", "WARNING", "ERROR", "CRITICAL")
```

### ScheduleModeError

`schedule_mode` configuration error.

```python
class ScheduleModeError(InvalidOptionError):
    """Invalid schedule_mode configuration error"""

    def __init__(self, schedule_mode: str, valid_modes=None):
        # valid_modes defaults to ("eager", "staged")
```

## Runtime Exceptions

### RemoteWorkerError

Exception raised when a remote worker (e.g., Go Worker) fails during execution.

```python
class RemoteWorkerError(CelestialFlowError):
    pass
```

### UnconsumedError

Exception class that marks tasks as unconsumed.

```python
class UnconsumedError(CelestialFlowError):
    """Exception class used to mark unconsumed tasks"""
    pass
```

When a `TaskGraph` stops, it collects all unconsumed tasks and records them as `UnconsumedError`.

### PickleError

Error raised when a task function or its arguments cannot be pickle-serialized.

```python
class PickleError(CelestialFlowError):
    """
    Error raised when a task function or its arguments cannot be pickle-serialized.
    """

    def __init__(self, obj: Any):
        message = f"Object of type {type(obj).__name__} is not pickleable."
        super().__init__(message)
        self.obj = obj
        self.type = type(obj).__name__
        self.message = message
```

### CelestialTreeConnectionError

Error raised when the CelestialTree service connection fails.

```python
class CelestialTreeConnectionError(CelestialFlowError):
    """Error raised when the CelestialTree service connection fails"""
    pass
```

In `TaskStage.set_func()`, the function is checked for pickle compatibility:

```python
from celestialflow.runtime.util_errors import PickleError
from celestialflow.utils.util_debug import find_unpickleable

if find_unpickleable(func):
    raise PickleError(func)
```

## Error Handling Strategies

In `TaskExecutor`, exceptions are categorized into two types:

1. **Retryable Exceptions**: If the exception type is in the `retry_exceptions` list and the retry count has not reached the limit, the framework automatically retries the task.
2. **Non-Retryable Exceptions**: The task is marked as failed, an error log is recorded, and it is placed into the `fail_queue`.

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
    PickleError,
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

1. **Pickle Check**: In process mode, ensure all functions and arguments are pickleable
2. **Error Propagation**: `RemoteWorkerError` contains the error message returned by the remote worker
3. **Logging**: All exceptions are logged
4. **Graceful Degradation**: Even when exceptions occur, the framework attempts to properly clean up resources
