# TaskTypes

> 📅 Last Updated: 2026/06/18

> ⚠️ **Deprecated**: The `PersistedErrorRecord` dataclass described in previous documentation no longer exists in the current source code.

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

A sentinel object used to mark the end of a task queue. When a Stage receives this signal, it indicates that the upstream has no more tasks and the Stage should prepare to stop.

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

An empty context manager, used to disable `with` logic (e.g., when no lock is needed).

```python
class NoOpContext:
    def __enter__(self) -> "NoOpContext": ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

## ValueWrapper

A counter wrapper for intra-thread / single-process use, with an optional lock.

```python
class ValueWrapper:
    def __init__(self, value: int, lock: Lock | NoOpContext | None = None):
        self.value = value
        self._lock = lock or NoOpContext()

    def get_lock(self) -> Lock | NoOpContext:
        """Return the lock object or NoOpContext (when lock-free)."""
```

## SumCounter

A sum counter that accumulates multiple counters (ValueWrapper).

```python
class SumCounter:
    def __init__(self, lock: Lock | NoOpContext | None = None):
        """
        :param lock: Optional thread lock, default None (uses NoOpContext)
        """
        self.init_value = ValueWrapper(value=0, lock=self.lock)
        self.counters = []
```

### Methods

| Method | Description |
|------|------|
| `add(value)` | Increase the initial count value (added to `init_value`) |
| `append_counter(counter)` | Append an external counter |
| `reset()` | Reset all counters to zero |
| `get()` | Get the accumulated value of all counters |
| `value` (property) | The total accumulated value of all counters |

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
| `TASK_SUCCESS` | `"task.success"` | Task execution succeeded |
| `TASK_ERROR` | `"task.error"` | Task execution failed |
| `TASK_RETRY_PREFIX` | `"task.retry."` | Retry prefix (concatenated with retry count) |
| `TASK_DUPLICATE` | `"task.duplicate"` | Duplicate task detected |
| `TERMINATION_INPUT` | `"termination.input"` | Termination signal injected |
| `TERMINATION_MERGE` | `"termination.merge"` | Termination signals merged |

## Usage Examples

The following examples demonstrate typical usage of the dataclasses and helper classes in the `util_types` module.

### TerminationSignal and TerminationIdPool

```python
from celestialflow.runtime.util_types import TerminationSignal, TERMINATION_SIGNAL, TerminationIdPool

# Create a custom termination signal
signal = TerminationSignal(_id=42, source="my_source")
print(f"Signal ID: {signal.id}, Source: {signal.source}")

# Use the global singleton
print(f"Default termination signal ID: {TERMINATION_SIGNAL.id}")      # -1
print(f"Default source: {TERMINATION_SIGNAL.source}")                 # "input"
print(f"Is same instance: {TERMINATION_SIGNAL is TerminationSignal()}")  # False (each call creates a new instance)

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

# SumCounter: multi-counter accumulation
sum_counter = SumCounter(mode="serial")
sum_counter.add_init_value(100)

sub1 = ValueWrapper(value=20)
sub2 = ValueWrapper(value=30)
sum_counter.append_counter(sub1)
sum_counter.append_counter(sub2)

print(f"Total (100 + 20 + 30): {sum_counter.value}")  # 150

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
print(f"Task failure event: {CTreeEvent.TASK_ERROR}")         # "task.error"
print(f"Retry prefix: {CTreeEvent.TASK_RETRY_PREFIX}")        # "task.retry."
print(f"Duplicate task event: {CTreeEvent.TASK_DUPLICATE}")   # "task.duplicate"
print(f"Termination injection event: {CTreeEvent.TERMINATION_INPUT}")  # "termination.input"
print(f"Termination merge event: {CTreeEvent.TERMINATION_MERGE}")      # "termination.merge"
```

## Notes

- The thread safety of `ValueWrapper` and `SumCounter` depends on the caller passing the correct `Lock` object.
- `NoOpContext` is used in `serial`/`async` modes as a substitute for a real lock, avoiding unnecessary lock overhead.
- `PersistedErrorRecord` is a frozen dataclass and is immutable after creation.
