# TaskTypes

> 📅 Last Updated: 2026/05/09

The TaskTypes module defines basic data types, enums, and helper classes used in the framework.

## StageStatus

Enum class representing the running state of a `TaskStage`.

```python
class StageStatus(IntEnum):
    NOT_STARTED = 0  # Not started
    RUNNING = 1      # Running
    STOPPED = 2      # Stopped
```

Usage example:
```python
from celestialflow.runtime.util_types import StageStatus

status = stage.get_status()
if status == StageStatus.RUNNING:
    print("Node is running")
```

## TerminationSignal

A sentinel object used to mark task queue termination. When a Stage receives this signal, it indicates that no more tasks are coming from upstream and it should prepare to stop.

```python
class TerminationSignal:
    def __init__(self, _id: int = -1, source: str = "input"):
        self.id = _id        # Event ID
        self.source = source  # Source

# Singleton
TERMINATION_SIGNAL = TerminationSignal()
```

### Usage Scenarios

```python
from celestialflow.runtime import TerminationSignal

# Inject termination signal
queue.put(TerminationSignal())

# Detect termination signal
if isinstance(record, TerminationSignal):
    break  # Stop processing
```

## TerminationIdPool

Termination signal ID pool, used to store all received termination signal IDs.

```python
class TerminationIdPool:
    def __init__(self, ids: list[int]):
        self.ids = ids
```

## NoOpContext

A no-op context manager, useful for disabling `with` logic.

```python
class NoOpContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
```

Usage scenario:
```python
# When no lock is needed, return NoOpContext
def get_lock(self):
    return self._lock or NoOpContext()
```

## ValueWrapper

A counter wrapper for single-thread/single-process use, optionally with a lock.

```python
class ValueWrapper:
    def __init__(self, value=0, lock=None):
        self.value = value
        self._lock = lock

    def get_lock(self):
        """Return the lock object or NoOpContext"""
        return self._lock or NoOpContext()
```

## SumCounter

Accumulates multiple counters (supports ValueWrapper).

```python
class SumCounter:
    def __init__(self, mode: str = "serial"):
        """
        Initialize the counter.

        :param mode: Mode ('serial', 'thread')
        """
```

### Methods

```python
# Add initial value
def add_init_value(self, value: int) -> None

# Append counter
def append_counter(self, counter: ValueWrapper) -> None

# Reset all counters
def reset(self) -> None

# Get total value
@property
def value(self) -> int
```

### Usage Example

```python
from celestialflow.runtime.util_types import SumCounter, ValueWrapper

# Thread mode
counter = SumCounter(mode="thread")
counter.add_init_value(10)

# Add sub-counter
sub_counter = ValueWrapper(value=5)
counter.append_counter(sub_counter)

print(counter.value)  # 15
```

## STAGE_STYLE

Node label style configuration for CelestialTree visualization.

```python
from celestialtree import NodeLabelStyle

STAGE_STYLE = NodeLabelStyle(
    template="{base}  {payload.name}  ‹{type}›",
    missing="-"
)
```

## Exception Classes

Exception classes are defined in `runtime/util_errors.py`:

| Exception Class | Description |
|----------------|-------------|
| `CelestialFlowError` | Base exception class |
| `ConfigurationError` | Configuration error |
| `InvalidOptionError` | Invalid option error |
| `ExecutionModeError` | Execution mode error |
| `StageModeError` | Stage mode error |
| `LogLevelError` | Log level error |
| `RemoteWorkerError` | Remote worker error |
| `UnconsumedError` | Unconsumed task error |
