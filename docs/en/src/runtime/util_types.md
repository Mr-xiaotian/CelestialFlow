# TaskTypes

> 📅 Last Updated: 2026/05/24

The TaskTypes module defines basic data types, enums, and helper classes used in the framework.

## StageStatus

Enum class representing the running state of a `TaskStage`.

```python
class StageStatus(IntEnum):
    NOT_STARTED = 0  # Not started
    RUNNING = 1      # Running
    STOPPED = 2      # Stopped
```

## TerminationSignal

A sentinel object used to mark task queue termination. When a Stage receives this signal, it indicates that no more tasks are coming from upstream and it should prepare to stop.

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

A no-op context manager, useful for disabling `with` logic (e.g., when no lock is needed).

```python
class NoOpContext:
    def __enter__(self) -> "NoOpContext": ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

## ValueWrapper

A counter wrapper for single-thread/single-process use, optionally with a lock.

```python
class ValueWrapper:
    def __init__(self, value: int = 0, lock: Lock | None = None):
        self.value = value
        self._lock = lock

    def get_lock(self) -> Lock | NoOpContext:
        """Return the lock object or NoOpContext (when no lock)."""
```

## SumCounter

Accumulates multiple counters (ValueWrapper) into a total sum.

```python
class SumCounter:
    def __init__(self, mode: str = "serial"):
        """
        :param mode: Execution mode, 'serial' (no lock) or 'thread' (with lock)
        """
```

### Methods

| Method | Description |
|--------|-------------|
| `add_init_value(value)` | Add an initial value |
| `append_counter(counter)` | Append an external counter |
| `reset()` | Reset all counters to zero |
| `value` (property) | Accumulated total of all counters |

### Usage Example

```python
from celestialflow.runtime.util_types import SumCounter, ValueWrapper

counter = SumCounter(mode="thread")
counter.add_init_value(10)

sub_counter = ValueWrapper(value=5)
counter.append_counter(sub_counter)

print(counter.value)  # 15
```

## CTreeEvent

CelestialTree event name constants, used for task tracking and visualization.

| Constant | Value | Trigger Timing |
|----------|-------|----------------|
| `TASK_INPUT` | `"task.input"` | Task enters the system |
| `TASK_SUCCESS` | `"task.success"` | Task execution succeeds |
| `TASK_ERROR` | `"task.error"` | Task execution fails |
| `TASK_RETRY_PREFIX` | `"task.retry."` | Retry prefix (appended with retry count) |
| `TASK_DUPLICATE` | `"task.duplicate"` | Duplicate task detected |
| `TERMINATION_INPUT` | `"termination.input"` | Termination signal injected |
| `TERMINATION_MERGE` | `"termination.merge"` | Termination signals merged |

## PersistedErrorRecord

Persisted error record dataclass.

```python
@dataclass(frozen=True)
class PersistedErrorRecord:
    error_type: str          # Error type name
    error_message: str       # Error message
    error_repr: str          # Full representation string of the error
    stage: str               # Node label where the error occurred
    error_id: int | None     # Error event ID
    timestamp: str           # Error timestamp string
    ts: float | None         # Error timestamp

    def __str__(self) -> str: ...
    def get_group_key(self) -> tuple[str, str]:
        """Returns (error_type, error_message) for grouping."""
```

## Usage Examples

The following examples demonstrate typical usage of the dataclasses and utility classes in the `util_types` module.

### TerminationSignal and TerminationIdPool

```python
from celestialflow.runtime.util_types import TerminationSignal, TERMINATION_SIGNAL, TerminationIdPool

# Create custom termination signal
signal = TerminationSignal(_id=42, source="my_source")
print(f"Signal ID: {signal.id}, Source: {signal.source}")

# Use global singleton
print(f"Default termination signal ID: {TERMINATION_SIGNAL.id}")      # -1
print(f"Default source: {TERMINATION_SIGNAL.source}")                # "input"
print(f"Is same instance: {TERMINATION_SIGNAL is TerminationSignal()}")  # False (new instance each time)

# Create termination signal ID pool
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
print(f"Initial status: {status.name}")
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

print(f"Sum (100 + 20 + 30): {sum_counter.value}")  # 150

# Reset
sum_counter.reset()
print(f"After reset: {sum_counter.value}")  # 0
```

### NoOpContext

```python
from celestialflow.runtime.util_types import NoOpContext

# No-op context manager for disabling with logic
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
print(f"Termination input event: {CTreeEvent.TERMINATION_INPUT}")  # "termination.input"
print(f"Termination merge event: {CTreeEvent.TERMINATION_MERGE}")  # "termination.merge"
```

### PersistedErrorRecord

```python
from celestialflow.runtime.util_types import PersistedErrorRecord

# Create a persisted error record
record = PersistedErrorRecord(
    error_type="ValueError",
    error_message="Invalid input: negative value",
    error_repr="ValueError: Invalid input: negative value",
    stage="StageA",
    error_id=123,
    timestamp="2026-05-24T10:30:00",
    ts=1716546600.0,
)

print(f"Error type: {record.error_type}")
print(f"Error message: {record.error_message}")
print(f"Node: {record.stage}")
print(f"String representation: {record}")

# Get grouping key (for grouping stats by type + message)
group_key = record.get_group_key()
print(f"Group key: {group_key}")  # ("ValueError", "Invalid input: negative value")
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
