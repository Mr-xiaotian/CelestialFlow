# TaskTypes

> 📅 Last Updated: 2026/06/11

The TaskTypes module defines the basic data types, enums, and helper classes used throughout the framework.

## StageStatus

Enum class representing the running state of a `TaskStage`.

```python
class StageStatus(IntEnum):
    NOT_STARTED = 0  # Not started
    RUNNING = 1      # Running
    STOPPED = 2      # Stopped
```

## TerminationSignal

A sentinel object used to mark the termination of task queues. When a Stage receives this signal, it indicates that no more tasks are coming from upstream and it should prepare to stop.

```python
class TerminationSignal:
    def __init__(self, _id: int = -1, source: str = "input"):
        self.id = _id        # Event ID
        self.source = source  # Source

# Global singleton
TERMINATION_SIGNAL = TerminationSignal()
```

## TerminationIdPool

Termination signal ID pool, used to store all received termination signal IDs.

```python
class TerminationIdPool:
    def __init__(self, ids: list[int]):
        self.ids = ids
```

## NoOpContext

An empty context manager, used to disable `with` logic (e.g., when a lock is not needed).

```python
class NoOpContext:
    def __enter__(self) -> "NoOpContext": ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

## ValueWrapper

A thread-local/single-process counter wrapper, with optional lock.

- **Purpose**: Provides a thread-safe integer counter.
- **Params**: `value` (`int`, default `0`) — initial value; `lock` (`Lock | None`, default `None`) — optional threading lock. When `None`, `get_lock()` returns a `NoOpContext`.
- **Key Method**: `get_lock()` — returns the configured `Lock` or a `NoOpContext`.

```python
class ValueWrapper:
    def __init__(self, value: int = 0, lock: Lock | None = None):
        self.value = value
        self._lock = lock

    def get_lock(self) -> Lock | NoOpContext:
        """Return the lock object or NoOpContext (when no lock)."""
```

## SumCounter

A cumulative counter that sums multiple counters (ValueWrapper).

- **Purpose**: Accumulates values from multiple `ValueWrapper` instances for cross-Stage cascading statistics.
- **Params**: `lock` (`Lock | NoOpContext | None`, default `None`) — optional thread lock. When `None`, uses `NoOpContext`.

```python
class SumCounter:
    def __init__(self, lock: Lock | NoOpContext | None = None):
        """
        :param lock: Optional thread lock, default None (uses NoOpContext)
        """
```

### Methods

| Method | Description |
|------|------|
| `add(value)` | Add initial count value |
| `append_counter(counter)` | Append an external counter |
| `reset()` | Reset all counters to zero |
| `get()` | Get the cumulative value of all counters |
| `value` (property) | Total value accumulating all counters |

### Usage Example

```python
from celestialflow.runtime.util_types import SumCounter, ValueWrapper

counter = SumCounter()
counter.add(10)

sub_counter = ValueWrapper(value=5)
counter.append_counter(sub_counter)

print(counter.get())  # 15
```

## CTreeEvent

CelestialTree event name constants, used for task tracking and visualization.

| Constant | Value | Trigger Timing |
|------|-----|---------|
| `TASK_INPUT` | `"task.input"` | Task enters the system |
| `TASK_SUCCESS` | `"task.success"` | Task executes successfully |
| `TASK_ERROR` | `"task.error"` | Task execution fails |
| `TASK_RETRY_PREFIX` | `"task.retry."` | Retry prefix (appended with retry count) |
| `TASK_DUPLICATE` | `"task.duplicate"` | Duplicate task detected |
| `TERMINATION_INPUT` | `"termination.input"` | Termination signal injected |
| `TERMINATION_MERGE` | `"termination.merge"` | Termination signals merged |

## PersistedErrorRecord

A persistent error record dataclass.

- **Purpose**: Represents a single error record for persistent storage, used by `FailSpout`.
- **Fields**:
  - `ts` (`float | None`) — error timestamp
  - `stage` (`str`) — label of the Stage where the error occurred
  - `error_id` (`int | None`) — error event ID
  - `error_type` (`str`) — error type name
  - `error_message` (`str`) — error message

```python
@dataclass(frozen=True)
class PersistedErrorRecord:
    ts: float | None = None         # Error timestamp
    stage: str = ""                  # Stage label where error occurred
    error_id: int | None = None      # Error event ID
    error_type: str = ""             # Error type name
    error_message: str = ""          # Error message

    def __str__(self) -> str: ...
    def get_group_key(self) -> tuple[str, str]:
        """Return (error_type, error_message) for grouping."""
```

## Usage Examples

The following examples demonstrate typical usage of the various dataclasses and utility classes in the `util_types` module.

### TerminationSignal and TerminationIdPool

```python
from celestialflow.runtime.util_types import TerminationSignal, TERMINATION_SIGNAL, TerminationIdPool

# Create a custom termination signal
signal = TerminationSignal(_id=42, source="my_source")
print(f"Signal ID: {signal.id}, source: {signal.source}")

# Use the global singleton
print(f"Default termination signal ID: {TERMINATION_SIGNAL.id}")      # -1
print(f"Default source: {TERMINATION_SIGNAL.source}")                 # "input"
print(f"Same instance?: {TERMINATION_SIGNAL is TerminationSignal()}")  # False (new instance each time)

# Create a termination signal ID pool
pool = TerminationIdPool(ids=[1, 2, 3])
print(f"ID pool: {pool.ids}")  # [1, 2, 3]
```

### StageStatus Enum

```python
from celestialflow.runtime.util_types import StageStatus

# Enum values
print(f"NOT_STARTED = {StageStatus.NOT_STARTED.value}")  # 0
print(f"RUNNING = {StageStatus.RUNNING.value}")          # 1
print(f"STOPPED = {StageStatus.STOPPED.value}")          # 2

# State transitions
status = StageStatus.NOT_STARTED
print(f"Initial state: {status.name}")
```

### ValueWrapper and SumCounter

```python
from celestialflow.runtime.util_types import ValueWrapper, SumCounter

# ValueWrapper: counter with optional lock
counter = ValueWrapper(value=10)
print(f"Initial value: {counter.value}")  # 10
with counter.get_lock():
    counter.value += 5
print(f"After locked increment: {counter.value}")  # 15

# SumCounter: multi-counter accumulator
sum_counter = SumCounter(mode="serial")
sum_counter.add_init_value(100)

sub1 = ValueWrapper(value=20)
sub2 = ValueWrapper(value=30)
sum_counter.append_counter(sub1)
sum_counter.append_counter(sub2)

print(f"Sum (100 + 20 + 30): {sum_counter.value}")  # 150

# Reset
sum_counter.reset()
print(f"After reset: {sum_counter.value}")  # 0
```

### NoOpContext

```python
from celestialflow.runtime.util_types import NoOpContext

# Empty context manager, used to disable with logic
ctx = NoOpContext()
with ctx:
    print("This is a no-op context")
```

### CTreeEvent Constants

```python
from celestialflow.runtime.util_types import CTreeEvent

# Event name constants
print(f"Task input event: {CTreeEvent.TASK_INPUT}")           # "task.input"
print(f"Task success event: {CTreeEvent.TASK_SUCCESS}")       # "task.success"
print(f"Task error event: {CTreeEvent.TASK_ERROR}")           # "task.error"
print(f"Retry prefix: {CTreeEvent.TASK_RETRY_PREFIX}")        # "task.retry."
print(f"Duplicate task event: {CTreeEvent.TASK_DUPLICATE}")   # "task.duplicate"
print(f"Termination inject event: {CTreeEvent.TERMINATION_INPUT}")  # "termination.input"
print(f"Termination merge event: {CTreeEvent.TERMINATION_MERGE}")   # "termination.merge"
```

### PersistedErrorRecord

```python
from celestialflow.runtime.util_types import PersistedErrorRecord

# Create a persistent error record
record = PersistedErrorRecord(
    error_type="ValueError",
    error_message="Invalid input: negative value",
    stage="StageA",
    error_id=123,
    ts=1716546600.0,
)

print(f"Error type: {record.error_type}")
print(f"Error message: {record.error_message}")
print(f"Stage: {record.stage}")
print(f"String representation: {record}")

# Get group key (for grouping statistics by type + message)
group_key = record.get_group_key()
print(f"Group key: {group_key}")  # ("ValueError", "Invalid input: negative value")
```

## Notes

- Thread safety of `ValueWrapper` and `SumCounter` depends on the caller passing the correct `Lock` object.
- `NoOpContext` is used in `serial`/`async` modes as a replacement for a real lock, avoiding unnecessary lock overhead.
- `PersistedErrorRecord` is a frozen dataclass; it is immutable after creation.
