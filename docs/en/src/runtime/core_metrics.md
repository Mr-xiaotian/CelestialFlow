# TaskMetrics

> 📅 Last Updated: 2026/05/24

The TaskMetrics module is responsible for managing and tracking various metrics during task execution, such as input task count, success count, failure count, duplicate task count, etc. It typically exists as a component of `TaskExecutor`.

## Initialization

```python
class TaskMetrics:
    def __init__(
        self,
        execution_mode: str,
        enable_duplicate_check: bool = False,
    ):
        """
        :param execution_mode: Task execution mode, options: "serial", "thread", "async"
        :param enable_duplicate_check: Whether to enable duplicate task checking, default False
        """
```

- **execution_mode**: Determines the thread-safety implementation of counters (uses `Lock` in thread mode)
- **enable_duplicate_check**: Controls whether to maintain `processed_set` for deduplication

## Counter Management

TaskMetrics internally maintains four core counters:

| Counter | Type | Purpose |
|---------|------|---------|
| `task_counter` | `SumCounter` | Total input tasks (supports cascading) |
| `success_counter` | `ValueWrapper` | Successful tasks |
| `error_counter` | `ValueWrapper` | Failed tasks |
| `duplicate_counter` | `ValueWrapper` | Duplicate tasks |

In `thread` mode, the three `ValueWrapper` instances share a single `Lock`, reducing lock overhead.

### Initialization and Reset

```python
def reset_counter(self) -> None:
    """Reset all counters to zero."""

def reset_state(self) -> None:
    """Reset statistical state (clears processed_set)."""
```

### Counter Operations

```python
def add_task_count(self, add_count: int = 1):
    """Thread-safely increment the input task count."""

def add_success_count(self, count: int = 1):
    """Thread-safely increment the success task count."""

def add_error_count(self, count: int = 1):
    """Thread-safely increment the failed task count."""

def add_duplicate_count(self, count: int = 1):
    """Thread-safely increment the duplicate task count."""
```

### Counter Cascading

```python
def append_task_counter(self, counter: ValueWrapper) -> None:
    """Append an external counter to task_counter (used for cross-Stage cascading statistics)."""
```

Cascading is used in `TaskStage.prev_bindings()` — each downstream node registers the upstream node's success counter to its own `task_counter`, achieving count consistency of "upstream output = downstream input".

## State Queries

### is_tasks_finished

Determines whether all input tasks have been processed.

```python
def is_tasks_finished(self) -> bool:
    """
    Compares task_counter.value against processed (success + error + duplicate) for equality.
    """
```

### get_counts

Gets a snapshot dictionary of all current metrics.

```python
def get_counts(self) -> dict[str, int]:
    return {
        "tasks_input": int,       # Total input tasks
        "tasks_succeeded": int,   # Successful tasks
        "tasks_failed": int,      # Failed tasks
        "tasks_duplicated": int,  # Duplicate tasks
        "tasks_processed": int,   # Total processed
        "tasks_pending": int,     # Pending tasks
    }
```

### Individual Queries

```python
def get_task_count(self) -> int: ...
def get_success_count(self) -> int: ...
def get_error_count(self) -> int: ...
def get_duplicate_count(self) -> int: ...
```

## Task Deduplication

When `enable_duplicate_check=True`, maintains `processed_set: set[bytes]` recording the hash values of processed tasks.

```python
def is_duplicate(self, task_hash: bytes) -> bool:
    """
    Atomic operation: check and mark duplicate.
    - If hash is not in the set, add it and return False
    - If already present, return True
    """

def add_processed_set(self, task_hash: bytes) -> None:
    """Add a task hash to the processed set (only effective when enable_duplicate_check=True)."""
```

## Retry Management

```python
def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """Add exception types that should trigger retries."""
```

Exception types are stored as a `tuple` in `self.retry_exceptions`. `TaskDispatch._worker` determines whether to retry using `isinstance(exception, self.retry_exceptions)`.

## Execution Mode Configuration

## Usage Examples

The following example demonstrates the complete usage of `TaskMetrics`, including initialization, counter operations, deduplication checks, retry exception configuration, and state queries.

```python
from celestialflow.runtime import TaskMetrics

# 1. Initialize metrics manager (with deduplication enabled)
metrics = TaskMetrics(
    execution_mode="serial",
    enable_duplicate_check=True,
)

# 2. Add retryable exception types
metrics.add_retry_exceptions(ConnectionError, TimeoutError)

# 3. Simulate task processing
# Received 5 input tasks
metrics.add_task_count(5)

# 3 succeeded
metrics.add_success_count(3)

# 1 failed
metrics.add_error_count(1)

# 1 duplicate detected
metrics.add_duplicate_count(1)

# 4. Query counter values
print(f"Total tasks: {metrics.get_task_count()}")         # 5
print(f"Success count: {metrics.get_success_count()}")    # 3
print(f"Failure count: {metrics.get_error_count()}")      # 1
print(f"Duplicate count: {metrics.get_duplicate_count()}")# 1

# 5. Get full snapshot dictionary
counts = metrics.get_counts()
print(f"Processed: {counts['tasks_processed']}")          # 3+1+1 = 5
print(f"Pending: {counts['tasks_pending']}")              # 0
print(f"All completed: {metrics.is_tasks_finished()}")    # True

# 6. Deduplication check example (requires enable_duplicate_check=True)
task_hash = b"\x00\x01\x02"
print(f"First check: {metrics.is_duplicate(task_hash)}")   # False (first time added)
print(f"Duplicate check: {metrics.is_duplicate(task_hash)}")# True (already exists)

# 7. Reset counters
metrics.reset_counter()
print(f"Task count after reset: {metrics.get_task_count()}") # 0

# 8. Switch execution mode (reinitialize thread-safety strategy)
metrics.set_execution_mode("thread")
print(f"New mode: {metrics.execution_mode}")
```

### Counter Cascading

```python
from celestialflow.runtime import TaskMetrics
from celestialflow.runtime.util_types import ValueWrapper

# Create parent and child metrics
parent_metrics = TaskMetrics(execution_mode="serial")
child_counter = ValueWrapper(value=10)

# Cascade child counter to parent task_counter
parent_metrics.append_task_counter(child_counter)
parent_metrics.add_task_count(5)  # Add 5 of its own

print(f"Total task count (5 + 10): {parent_metrics.get_task_count()}")  # 15
```

### set_execution_mode

```python
def set_execution_mode(self, execution_mode: str) -> None:
    """Set the task execution mode and reinitialize counters (switch thread-safety strategy)."""
```
