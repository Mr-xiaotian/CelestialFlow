# TaskMetrics

> 📅 Last Updated: 2026/08/26

The TaskMetrics module is responsible for managing and tracking various metrics during task execution, such as input task count, success count, failure count, duplicate task count, etc. It typically exists as a component of `TaskExecutor`.


## Initialization

```python
class TaskMetrics:
    def __init__(
        self,
        enable_duplicate_check: bool = False,
    ):
        """
        :param enable_duplicate_check: Whether to enable duplicate task checking, default False
        """
```

- **enable_duplicate_check**: Controls whether to maintain `processed_set` for deduplication

## Counter Management

TaskMetrics internally maintains four core counters:

| Counter | Type | Purpose |
|---------|------|---------|
| `task_counter` | `SumCounter` | Total input task count (supports cascading) |
| `success_counter` | `ValueWrapper` | Successful task count |
| `fail_counter` | `ValueWrapper` | Failed task count |
| `duplicate_counter` | `ValueWrapper` | Duplicate task count |

All `ValueWrapper` instances uniformly use `Lock` to guarantee thread safety.

### Initialization and Reset

```python
def reset_counter(self) -> None:
    """Reset all counters to zero."""


def reset_state(self) -> None:
    """Reset statistical state (clear processed_set)."""
```

### Counter Operations

```python
def add_task_count(self, add_count: int = 1):
    """Thread-safely increase the input task count."""


def add_fail_count(self, count: int = 1):
    """Thread-safely increase the failed task count."""


def add_success_count(self, count: int = 1):
    """Thread-safely increase the successful task count."""


def add_duplicate_count(self, count: int = 1):
    """Thread-safely increase the duplicate task count."""
```
### Counter Cascading

```python
def append_task_counter(self, counter: ValueWrapper) -> None:
    """Add an external counter to task_counter (for cross-Stage cascaded statistics)."""
```

Cascading is used in `TaskStage.prev_binding()` — each downstream node registers the upstream node's success counter into its own `task_counter`, achieving "upstream output = downstream input" counting consistency.

## Observer Management

```python
def add_observer(self, observer: BaseObserver) -> None:
    """Register an observer."""


def remove_observer(self, observer: BaseObserver) -> None:
    """Remove an observer."""
```

Registered observers receive callbacks when task counts change:

| Counter Method | Observer Callback |
|---------|-----------|
| `add_task_count()` | `on_tasks_added(count)` |
| `add_success_count()` | `on_task_success(count)` |
| `add_fail_count()` | `on_task_fail(count)` |
| `add_duplicate_count()` | `on_task_duplicate(count)` |
| `on_start()` | `on_start(name, total)` (broadcast executor start) |
| `on_finish()` | `on_finish()` (broadcast executor end) |

## Lifecycle Status

`TaskMetrics` internally maintains `_status` (`StageStatus` enum), updated on executor start/end:

- `on_start(name, total)`: Sets the status to `StageStatus.RUNNING` and broadcasts the start event.
- `on_finish()`: Sets the status to `StageStatus.STOPPED` and broadcasts the end event.
- `get_status()`: Reads the current status, returning a `StageStatus` enum.

## State Queries

### is_tasks_finished

Determine whether all input tasks have been processed.

```python
def is_tasks_finished(self) -> bool:
    """
    Compare task_counter.value against processed (success + fail + duplicate) for equality.
    """
```

### get_counts

Get a snapshot dictionary of all current metrics.

```python
def get_counts(self) -> dict[str, int]:
    return {
        "tasks_input": int,  # Total input task count
        "tasks_succeeded": int,  # Successful task count
        "tasks_failed": int,  # Failed task count
        "tasks_duplicated": int,  # Duplicate task count
        "tasks_processed": int,  # Total processed count
        "tasks_pending": int,  # Pending task count
    }
```

### Individual Queries

```python
def get_task_count(self) -> int: ...
def get_success_count(self) -> int: ...
def get_fail_count(self) -> int: ...
def get_duplicate_count(self) -> int: ...
```

## Task Deduplication

When `enable_duplicate_check=True`, maintains `processed_set: set[bytes]` recording the hash values of processed tasks.

```python
def is_duplicate(self, task_hash: bytes) -> bool:
    """
    Check and mark duplicates (this method is called serially in the executor thread, no extra locking required).
    - If hash is not in the set, add it and return False
    - If already present, return True
    """


def add_processed_set(self, task_hash: bytes) -> None:
    """Add task hash to the processed set (only effective when enable_duplicate_check=True)."""
```

## Retry Management

```python
def set_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """Add exception types that should trigger retries."""
```

Exception types are stored as a `tuple` in `self.retry_exceptions`. `TaskDispatch._worker` / `_async_worker` determine whether to retry via `isinstance(exception, self.task_executor.metrics.retry_exceptions)`. Each call accumulates on top of existing exception types.

```python
def get_retry_error_type_names(self) -> set[str]:
    """Get the set of error type names that the current executor allows recovering from persisted failure records."""
```

Used in `TaskGraph.restore_db()` to filter retryable persisted records by `error_type`.

## Usage Examples

The following example demonstrates full usage of `TaskMetrics`, including initialization, counter operations, deduplication checks, retry exception configuration, and state queries.

```python
from celestialflow.runtime import TaskMetrics

# 1. Initialize metrics manager (with dedup check enabled)
metrics = TaskMetrics(
    enable_duplicate_check=True,
)

# 2. Add retryable exception types
metrics.set_retry_exceptions(ConnectionError, TimeoutError)

# 3. Simulate task processing
# Received 5 input tasks
metrics.add_task_count(5)

# 3 processed successfully
metrics.add_success_count(3)

# 1 failed
metrics.add_fail_count(1)

# 1 duplicate detected
metrics.add_duplicate_count(1)

# 4. Query individual counter values
print(f"Total tasks: {metrics.get_task_count()}")  # 5
print(f"Success count: {metrics.get_success_count()}")  # 3
print(f"Failure count: {metrics.get_fail_count()}")  # 1
print(f"Duplicate count: {metrics.get_duplicate_count()}")  # 1

# 5. Get full snapshot dict
counts = metrics.get_counts()
print(f"Processed: {counts['tasks_processed']}")  # 3+1+1 = 5
print(f"Pending: {counts['tasks_pending']}")  # 0
print(f"All complete: {metrics.is_tasks_finished()}")  # True

# 6. Dedup check example (requires enable_duplicate_check=True)
task_hash = b"\x00\x01\x02"
print(f"First check: {metrics.is_duplicate(task_hash)}")  # False (first time added)
print(f"Repeat check: {metrics.is_duplicate(task_hash)}")  # True (already exists)

# 7. Reset counters
metrics.reset_counter()
print(f"Task count after reset: {metrics.get_task_count()}")  # 0
```

### Counter Cascading

```python
from celestialflow.runtime import TaskMetrics
from celestialflow.runtime.util_types import ValueWrapper

# Create parent and child metrics
parent_metrics = TaskMetrics()
child_counter = ValueWrapper(value=10)

# Cascade child counter into parent task_counter
parent_metrics.append_task_counter(child_counter)
parent_metrics.add_task_count(5)  # Add 5 from self

print(f"Total task count (5 + 10): {parent_metrics.get_task_count()}")  # 15
```

