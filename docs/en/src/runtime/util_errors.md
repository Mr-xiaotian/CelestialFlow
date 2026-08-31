# TaskErrors

> 📅 Last Updated: 2026/08/31

The TaskErrors module defines the complete exception class system used in the CelestialFlow framework.

## Exception Hierarchy

```mermaid
classDiagram
    direction TB

    class CelestialFlowError {
        +Base class
    }

    class ConfigurationError {
        +Configuration error base class
    }
    class InvalidOptionError {
        +field: str
        +value: Any
        +allowed: tuple
        Invalid configuration option value
    }
    class CallableParameterKindError {
        +callable_name: str
        +parameter_kind: Any
        +valid_kinds: tuple
        Invalid callable parameter kind
    }
    class GraphStructureError {
        +Graph structure error base class
    }
    class DuplicateNodeError {
        +Duplicate node name
    }
    class UnknownNodeError {
        +Unknown node name
    }
    class NodeNotFoundError {
        +Specified node not found in graph
    }
    class InvalidStructureError {
        +Invalid graph structure input
    }
    class RuntimeStateError {
        +Runtime state error base class
    }
    class InitializationError {
        +Initialization failure
    }
    class PersistedError {
        +error_type: str
        +error_message: str
        +Persisted error summary
    }
    class RemoteWorkerError {
        +Remote Worker execution failure
    }
    class ReporterError {
        +Reporter error
    }
    class CelestialFlowTimeoutError {
        +Timeout error
    }
    class UnconsumedError {
        +Marks unconsumed tasks
    }
    class TerminationMergeError {
        +Termination signal merge error
    }

    CelestialFlowError <|-- ConfigurationError
    CelestialFlowError <|-- RuntimeStateError
    CelestialFlowError <|-- PersistedError
    CelestialFlowError <|-- RemoteWorkerError
    CelestialFlowError <|-- ReporterError
    CelestialFlowError <|-- CelestialFlowTimeoutError
    CelestialFlowError <|-- UnconsumedError
    CelestialFlowError <|-- TerminationMergeError

    ConfigurationError <|-- InvalidOptionError
    ConfigurationError <|-- GraphStructureError

    InvalidOptionError <|-- CallableParameterKindError

    GraphStructureError <|-- DuplicateNodeError
    GraphStructureError <|-- UnknownNodeError
    GraphStructureError <|-- NodeNotFoundError
    GraphStructureError <|-- InvalidStructureError

    RuntimeStateError <|-- InitializationError
```

## Base Class

### CelestialFlowError

Base class for all custom exceptions.

```python
class CelestialFlowError(Exception):
    """Base class for all CelestialFlow custom exceptions"""

    pass
```

## Configuration-Related Exceptions (ConfigurationError)

### ConfigurationError

Base class for configuration errors (illegal parameters, unsupported combinations, etc.).

```python
class ConfigurationError(CelestialFlowError):
    """Configuration error (illegal parameters, unsupported combinations, etc.)"""

    pass
```

### InvalidOptionError

A specific configuration option has an invalid value.

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
        :param field: Configuration item name
        :param value: Actual passed-in value
        :param allowed: Allowed value set
        :param prefix: Error message prefix
        """
        # Example: "Invalid execution mode: xxx. Valid options are ('serial', 'thread', 'async')."
```

### CallableParameterKindError

Callable parameter kind is invalid.

```python
class CallableParameterKindError(InvalidOptionError):
    def __init__(
        self, callable_name: str, parameter_kind: Any, valid_kinds: Iterable[Any]
    ):
        """
        :param callable_name: Callable name
        :param callable_name: Actual parameter kind
        :param valid_kinds: Allowed parameter kind set
        """
```

## Graph Structure Exceptions (GraphStructureError)

### GraphStructureError

Base class for graph structure errors.

```python
class GraphStructureError(ConfigurationError):
    """Graph structure error"""

    pass
```

### DuplicateNodeError

Duplicate node name (triggered during `set_stages` or `add_source_name` / `add_queue`).

```python
class DuplicateNodeError(GraphStructureError):
    """Duplicate node name"""

    pass
```

### UnknownNodeError

Unknown node name (triggered during termination signal source validation).

```python
class UnknownNodeError(GraphStructureError):
    """Unknown node name"""

    pass
```

### NodeNotFoundError

Specified node not found in graph (triggered during `connect()` or queries).

```python
class NodeNotFoundError(GraphStructureError):
    """Specified node not found in graph"""

    pass
```

## Runtime Exceptions (RuntimeStateError)

### RuntimeStateError

Base class for runtime state errors (duplicate start, not initialized, etc.).

```python
class RuntimeStateError(CelestialFlowError):
    """Runtime state error"""

    pass
```

### InitializationError

Initialization error (e.g., using thread pool when not initialized).

```python
class InitializationError(RuntimeStateError):
    """Initialization error"""

    pass
```

## Persistence Exception

### PersistedError

Error summary object recovered from the persistence layer.

```python
class PersistedError(CelestialFlowError):
    def __init__(self, error_type: str, error_message: str) -> None:
        self.error_type = error_type
        self.error_message = error_message

    def __str__(self) -> str:
        """Return a compact representation in the form ``ErrorType(message)``."""
```

## External Service Exceptions

### RemoteWorkerError

Thrown when a remote Worker (e.g., Go Worker) execution fails.

```python
class RemoteWorkerError(CelestialFlowError):
    """Remote Worker execution failed"""

    pass
```

### ReporterError

Reporter error.

```python
class ReporterError(CelestialFlowError):
    """Reporter error"""

    pass
```

## Other Runtime Exceptions

### Timeout Exception

### CelestialFlowTimeoutError

Timeout error (inherits built-in `TimeoutError`).

```python
class CelestialFlowTimeoutError(CelestialFlowError, TimeoutError):
    """Timeout error"""

    pass
```

### UnconsumedError

Marks tasks that were not consumed.

```python
class UnconsumedError(CelestialFlowError):
    """Exception class used to mark unconsumed tasks"""

    pass
```

When `TaskGraph._finish_start()` finds remaining tasks in queues during the finalization phase, they are marked as `UnconsumedError` and persisted to a date-organized lifecycle sqlite database via `get_lifecycle_inlet()` / `LifecycleSpout`.

### TerminationMergeError

Termination signal merge error (triggered when upstream termination signals are missing).

```python
class TerminationMergeError(CelestialFlowError):
    """Termination signal merge error"""

    pass
```

## Usage Scenarios

### 1. Adding Retryable Exceptions

```python
from celestialflow import TaskExecutor

executor = TaskExecutor("Processor", process, max_retries=3)
executor.set_retry_exceptions(ConnectionError, TimeoutError)
```

### 2. Catching Configuration Errors

```python
from celestialflow.runtime.util_errors import InvalidOptionError

try:
    raise InvalidOptionError(
        field="execution_mode",
        value="invalid",
        allowed=("serial", "thread", "async"),
    )
except InvalidOptionError as e:
    print(f"Field: {e.field}")
    print(f"Passed value: {e.value}")
    print(f"Valid values: {e.allowed}")
```

### 3. Graph Structure Validation

```python
from celestialflow.runtime.util_errors import DuplicateNodeError

try:
    graph.set_stages([stage_a, stage_a])  # Duplicate node name
except DuplicateNodeError as e:
    print(f"Duplicate node: {e}")
```

## Usage Examples

The following examples demonstrate typical raise and catch patterns for CelestialFlow exceptions.

### Configuration Exceptions

```python
from celestialflow.runtime.util_errors import InvalidOptionError

# Use InvalidOptionError
try:
    raise InvalidOptionError(
        field="strategy",
        value="aggressive",
        allowed=("conservative", "balanced"),
    )
except InvalidOptionError as e:
    print(f"Field: {e.field}")
    print(f"Passed value: {e.value}")
    print(f"Valid values: {e.allowed}")
```

### Graph Structure Exceptions

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.runtime.util_errors import DuplicateNodeError, UnknownNodeError

graph = TaskGraph(name="ErrorTestGraph")

stage_a = TaskStage("A", func=lambda x: x)
stage_b = TaskStage("A", func=lambda x: x * 2)  # Duplicate node name

try:
    graph.set_stages([stage_a, stage_b])
except DuplicateNodeError as e:
    print(f"Duplicate node: {e}")

try:
    from celestialflow.runtime.util_types import TerminationSignal

    # UnknownNodeError is triggered when in_queue._record_termination validates the source
    from celestialflow.runtime import TaskInQueue

    in_queue = TaskInQueue(out_name="test")
    in_queue.add_source_name("known")
    in_queue._record_termination(TerminationSignal(source="unknown_source"))
except UnknownNodeError as e:
    print(f"Unknown source: {e}")
```

### Runtime and Timeout Exceptions

```python
from celestialflow.runtime.util_errors import (
    RuntimeStateError,
    CelestialFlowTimeoutError,
    UnconsumedError,
    TerminationMergeError,
)

# Timeout error (inherits built-in TimeoutError)
try:
    raise CelestialFlowTimeoutError("Task execution timed out after 30s")
except CelestialFlowTimeoutError as e:
    print(f"Timeout: {e}")

# Termination signal merge error
try:
    raise TerminationMergeError("Missing termination from source: B")
except TerminationMergeError as e:
    print(f"Merge error: {e}")
```

### External Service Exceptions

```python
from celestialflow.runtime.util_errors import RemoteWorkerError

try:
    raise RemoteWorkerError("Go worker returned status code 500")
except RemoteWorkerError as e:
    print(f"Remote Worker error: {e}")
```



## Handling Unconsumed Tasks

`UnconsumedError` is primarily used to mark tasks that were not properly consumed. During the `TaskGraph._finish_start()` finalization phase, each stage's `drain_task_queue()` is called:

1. Drain the stage's task queue, collecting remaining tasks.
2. For each remaining task, call `handle_task_fail(source, UnconsumedError())`.
3. Failure information is written to `LifecycleSpout` via `get_lifecycle_inlet()` (`task_fail()` promotes pending records to failed), and ultimately persisted to a date-organized lifecycle sqlite database (`./lifecycles/YYYY-MM-DD/flow_lifecycle(...).sqlite3`).

Thus, the "persistence" of unconsumed tasks is not performed by `util_errors.py` itself, but relies on the lifecycle persistence mechanism at the Stage / Graph layer.
