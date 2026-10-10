# src/celestialflow/runtime/util_types.py

> 📅 Last Updated: 2026/10/09

`util_types.py` defines the basic data types, enums, and helper classes used throughout the framework.

## TerminationSignal

A sentinel object used to mark the end of a task queue. When a node receives this signal, it indicates that the upstream has no more tasks, and the node should prepare to stop.

```python
class TerminationSignal:
    def __init__(self, _id: int = -1, source: str = "input"):
        self.id = _id  # Termination signal ID
        self.source = source  # Source identifier


# Global singleton
TERMINATION_SIGNAL = TerminationSignal()
```

## TerminationIdPool

Termination signal ID pool, used to store all received termination signal IDs.

```python
class TerminationIdPool:
    def __init__(self, ids: list[int]):
        self.ids = ids  # Termination signal ID list
```

## NoOpContext

An empty context manager, used to disable `with` logic.

```python
class NoOpContext:
    def __enter__(self) -> NoOpContext: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

`__exit__` ignores all exception information and does not swallow exceptions itself (returns `None`).

## ValueWrapper

A counter wrapper for intra-thread / single-process use, **which creates its own thread lock by default**, or can explicitly disable locking.

```python
class ValueWrapper:
    def __init__(self, value: int, lock: Lock | NoOpContext | None = None):
        """
        :param value: Initial value
        :param lock: Optional thread lock. Default None means a lock is created internally;
            passing in an existing Lock lets multiple counters share the same lock;
            explicitly passing NoOpContext disables locking (only for single-threaded access)
        """
        self.value = value
        self._lock = lock if lock is not None else Lock()
```

| Method | Description |
|------|------|
| `get_lock()` | Returns the lock object; returns `NoOpContext` when locking is disabled |
| `add(value)` | Increments `value` while holding the lock |
| `get()` | Reads the current value while holding the lock |

> Because `lock=None` creates a real `Lock`, `ValueWrapper` is thread-safe by default; you should explicitly pass `NoOpContext` to disable locking only when single-threaded access is certain.

## NodeStatus

The lifecycle-status enum of task graph nodes (`BaseTaskNode` and its subclasses, such as `TaskExecutor`, `TaskSplitter`, `TaskRouter`).

```python
class NodeStatus(IntEnum):
    NOT_STARTED = 0  # Not started
    RUNNING = 1  # Running
    STOPPED = 2  # Stopped
```

## CTreeEvent

CelestialTree event name constants, used for task tracking and visualization.

| Constant | Value | Trigger Timing |
|------|-----|---------|
| `TASK_INPUT` | `"task.input"` | Task enters the system |
| `TASK_SUCCESS` | `"task.success"` | Task execution succeeded |
| `TASK_ERROR` | `"task.error"` | Task execution failed |
| `TASK_SKIP` | `"task.skip"` | Task is skipped |
| `TASK_RETRY_PREFIX` | `"task.retry."` | Retry prefix (concatenated with retry count) |
| `TERMINATION_INPUT` | `"termination.input"` | Termination signal injected |
| `TERMINATION_MERGE` | `"termination.merge"` | Termination signals merged |

## NodeMetrics

A single-node metric snapshot (read-only DTO, `@dataclass(frozen=True, slots=True)`). The metric observer maintains the write model based on events; this class only holds a read-only snapshot at a given moment.

| Field | Type | Description |
|------|------|------|
| `node` | `str` | Node name |
| `status` | `NodeStatus` | Node lifecycle status |
| `start_time` | `float` | Wall-clock time (seconds) when entering the running state; `0.0` if not started |
| `external_input` | `int` | Number of externally injected tasks |
| `upstream_input` | `int` | Number of tasks provided by upstream |
| `input_total` | `int` | Total number of input tasks (sum of external injection and upstream-provided) |
| `succeeded` | `int` | Number of successful tasks |
| `failed` | `int` | Number of failed tasks |
| `skipped` | `int` | Number of skipped tasks |
| `processed` | `int` | Number of processed tasks (success + failure + skip) |
| `pending` | `int` | Number of pending tasks |
| `upstream_counts` | `dict[str, int]` | Mapping of task counts provided by each upstream node |
| `downstream_counts` | `dict[str, int]` | Mapping of task counts sent to each downstream node |

## MetricsView

The metric read-only view protocol (`Protocol`). The write model is maintained by the metric observer based on events; this protocol only exposes an immutable read entry for consumers such as log and reporting, avoiding leaking mutable internal state.

```python
class MetricsView(Protocol):
    def get_node_metrics(self, node: str) -> NodeMetrics | None: ...
    def get_graph_metrics(self) -> dict[str, NodeMetrics]: ...
```

## Usage Examples

The following examples demonstrate typical usage of the data classes and helper classes in the `util_types` module.

### TerminationSignal and TerminationIdPool

```python
from celestialflow.runtime.util_types import (
    TerminationSignal,
    TERMINATION_SIGNAL,
    TerminationIdPool,
)

# Create a custom termination signal
signal = TerminationSignal(_id=42, source="my_source")
print(f"Signal ID: {signal.id}, source: {signal.source}")

# Use the global singleton
print(f"Default termination signal ID: {TERMINATION_SIGNAL.id}")  # -1
print(f"Default source: {TERMINATION_SIGNAL.source}")  # "input"
print(
    f"Same instance: {TERMINATION_SIGNAL is TerminationSignal()}"
)  # False (a new instance is created each time)

# Create a termination signal ID pool
pool = TerminationIdPool(ids=[1, 2, 3])
print(f"ID pool: {pool.ids}")  # [1, 2, 3]
```

### NodeStatus Enum

```python
from celestialflow.runtime.util_types import NodeStatus

# Enum values
print(f"NOT_STARTED = {NodeStatus.NOT_STARTED.value}")  # 0
print(f"RUNNING = {NodeStatus.RUNNING.value}")  # 1
print(f"STOPPED = {NodeStatus.STOPPED.value}")  # 2

# State transition
status = NodeStatus.NOT_STARTED
print(f"Initial status: {status.name}")
```

### NodeMetrics and MetricsView

```python
from celestialflow.runtime.util_types import NodeMetrics, NodeStatus, MetricsView

# Construct a read-only metric snapshot
snapshot = NodeMetrics(
    node="processor",
    status=NodeStatus.RUNNING,
    start_time=1234.5,
    external_input=3,
    upstream_input=2,
    input_total=5,
    succeeded=3,
    failed=1,
    skipped=1,
    processed=5,
    pending=0,
    upstream_counts={"producer": 2},
    downstream_counts={"store": 5},
)
print(snapshot.processed)  # 5
```

### ValueWrapper

```python
from celestialflow.runtime.util_types import ValueWrapper

# Real thread lock by default
counter = ValueWrapper(value=10)
print(f"Initial value: {counter.value}")  # 10

counter.add(5)
print(f"After increment: {counter.get()}")  # 15

# Share the same lock with other counters
from threading import Lock

shared = Lock()
a = ValueWrapper(value=0, lock=shared)
b = ValueWrapper(value=0, lock=shared)
print(f"Shared lock: {a.get_lock() is b.get_lock()}")  # True
```

### NoOpContext

```python
from celestialflow.runtime.util_types import NoOpContext, ValueWrapper

# Empty context manager, used to disable with logic
ctx = NoOpContext()
with ctx:
    print("This is a no-op context")

# Explicitly disable locking in single-threaded scenarios
single_thread_counter = ValueWrapper(value=0, lock=NoOpContext())
```

### CTreeEvent Constants

```python
from celestialflow.runtime.util_types import CTreeEvent

# Event name constants
print(f"Task input event: {CTreeEvent.TASK_INPUT}")  # "task.input"
print(f"Task success event: {CTreeEvent.TASK_SUCCESS}")  # "task.success"
print(f"Task error event: {CTreeEvent.TASK_ERROR}")  # "task.error"
print(f"Retry prefix: {CTreeEvent.TASK_RETRY_PREFIX}")  # "task.retry."
print(f"Termination input event: {CTreeEvent.TERMINATION_INPUT}")  # "termination.input"
print(f"Termination merge event: {CTreeEvent.TERMINATION_MERGE}")  # "termination.merge"
```

## Notes

- `ValueWrapper` uses a real `Lock` by default, so it is thread-safe by default; `NoOpContext` is used to explicitly eliminate lock overhead in single-threaded mode.
- `TERMINATION_SIGNAL` is a module-level singleton with default `id=-1` and `source="input"`.
- `NodeStatus` is an `IntEnum`, so it can be compared directly with integers.