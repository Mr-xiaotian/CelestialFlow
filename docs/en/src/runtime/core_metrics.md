# TaskMetrics

> 📅 Last updated: 2026/04/24

The TaskMetrics module is responsible for managing and tracking various metrics during task execution, such as input task count, success count, failure count, duplicate task count, etc. It typically exists as a component of `TaskExecutor`.

## Initialization

```python
class TaskMetrics:
    def __init__(
        self,
        execution_mode: str,
        max_retries: int = 1,
        enable_duplicate_check: bool = False,
    ):
        ...
```

- **execution_mode**: Task execution mode. Possible values include `"thread"` or `"async"`, etc. Used to select the counter implementation.
- **max_retries**: Maximum number of retries, default is 1.
- **enable_duplicate_check**: Whether to enable duplicate task checking, default is False.

## Counter Management

TaskMetrics provides a set of methods to safely update counters (typically using locks in multi-thread/multi-process environments).

### Initialization and Reset

```python
def _init_counter(self) -> None:
    """Initialize counters (selects implementation based on execution_mode)."""

def reset_counter(self) -> None:
    """Reset all counters to zero."""

def reset_state(self) -> None:
    """Reset statistical state (clears retry time records and processed task set)."""
```

### Counter Operations

```python
def add_task_count(self, add_count: int = 1):
    """Increment the input task count."""

def add_success_count(self, count: int = 1):
    """Thread-safely increment the success task count."""

async def add_success_count_async(self, count: int = 1):
    """Asynchronously update the success task counter."""

def add_error_count(self, count: int = 1):
    """Thread-safely increment the failed task count."""

def add_duplicate_count(self, count: int = 1):
    """Thread-safely increment the duplicate task count."""
```

### Counter Cascading

```python
def append_task_counter(self, counter) -> None:
    """Append an external counter to the task total counter (used for cross-Stage cascading statistics)."""
```

## State Queries

### is_tasks_finished

Determines whether all input tasks have been processed (success + failure + duplicates == input).

```python
def is_tasks_finished(self) -> bool: ...
```

### get_counts

Gets a snapshot dictionary of all current metrics.

```python
def get_counts(self) -> dict:
    return {
        "tasks_input": int,       # Total input tasks
        "tasks_succeeded": int,   # Successful tasks
        "tasks_failed": int,      # Failed tasks
        "tasks_duplicated": int,  # Duplicate tasks
        "tasks_processed": int,   # Total processed (success + failure + duplicates)
        "tasks_pending": int,     # Pending tasks (input - processed)
    }
```

### Individual Queries

```python
def get_task_count(self) -> int:
    """Get the current total task count."""

def get_success_count(self) -> int:
    """Get the current success task count."""

def get_error_count(self) -> int:
    """Get the current failed task count."""

def get_duplicate_count(self) -> int:
    """Get the current duplicate task count."""
```

## Task Deduplication

If `enable_duplicate_check` is enabled, TaskMetrics maintains a `processed_set` to record the hash values of processed tasks.

```python
def is_duplicate(self, task_hash: str) -> bool:
    """Check whether a task already exists."""

def add_processed_set(self, task_hash: str) -> None:
    """Add a task hash to the processed set."""
```

## Retry Management

TaskMetrics manages the retry logic for tasks.

### Exception Configuration

```python
def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """Add exception types that should trigger retries."""
```

## Execution Mode Configuration

```python
def set_execution_mode(self, execution_mode: str) -> None:
    """Set the task execution mode and reinitialize counters."""
```
