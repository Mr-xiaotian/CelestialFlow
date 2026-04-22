# TaskMetrics

> 📅 Last updated: 2026/04/22

The TaskMetrics module manages and tracks various metrics during task execution, such as input task count, success count, failure count, duplicate task count, and more. It typically exists as a component of `TaskExecutor`.

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

- **execution_mode**: Task execution mode. Possible values include `"thread"`, `"async"`, etc. Used to select the counter implementation.
- **max_retries**: Maximum number of retries, default is 1.
- **enable_duplicate_check**: Whether to enable duplicate task checking, default is False.

## Counter Management

TaskMetrics provides a set of methods for safely updating counters (typically using locks in multi-thread/multi-process environments).

### Initialization and Reset

```python
def init_counter(self) -> None:
    """Initialize counters (selects implementation based on execution_mode)."""

def reset_counter(self) -> None:
    """Reset all counters to zero."""

def reset_state(self) -> None:
    """Reset statistics state (clears retry time records and processed task sets)."""
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
    """Append an external counter to the task total counter (used for cross-stage cascading statistics)."""
```

## State Queries

### is_tasks_finished

Determines whether all input tasks have been processed (success + failure + duplicate == input).

```python
def is_tasks_finished(self) -> bool: ...
```

### get_counts

Gets a snapshot dictionary of all current metrics.

```python
def get_counts(self) -> dict:
    return {
        "tasks_input": int,       # Total input tasks
        "tasks_successed": int,   # Successful tasks
        "tasks_failed": int,      # Failed tasks
        "tasks_duplicated": int,  # Duplicate tasks
        "tasks_processed": int,   # Total processed (success+failure+duplicate)
        "tasks_pending": int,     # Pending tasks (input-processed)
    }
```

### Individual Queries

```python
def get_task_count(self) -> int:
    """Get the current total task count."""

def get_success_count(self) -> int:
    """Get the current successful task count."""

def get_error_count(self) -> int:
    """Get the current failed task count."""

def get_duplicate_count(self) -> int:
    """Get the current duplicate task count."""
```

## Task Deduplication

If `enable_duplicate_check` is enabled, TaskMetrics maintains a `processed_set` to record the hashes of processed tasks.

```python
def is_duplicate(self, task_hash: str) -> bool:
    """Check whether a task already exists."""

def add_processed_set(self, task_hash: str) -> None:
    """Add a task hash to the processed set."""

def discard_processed_set(self, task_hash: str) -> None:
    """Remove a task from the processed set (used to allow reprocessing during retries)."""
```

## Retry Management

TaskMetrics manages task retry logic, including retryable exception types and retry count tracking.

### Exception Configuration

```python
def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """Add exception types that should trigger retries."""
```

### Retry Evaluation

```python
def is_retry_able(self, task_hash: str, exception: Exception) -> bool:
    """
    Check whether a task can be retried.
    Based on exception type and current retry count.
    """
```

### Retry Counting

```python
def get_retry_time(self, task_hash: str) -> int:
    """Get the retry count for a task (returns 0 if not found)."""

def add_retry_time(self, task_hash: str, retry_time: int = 1) -> int:
    """Increment the retry count for a task and return the new count."""

def pop_retry_time(self, task_hash: str) -> int | None:
    """Pop and return the retry count for a task (called after success or final failure)."""
```

## Execution Mode Setting

```python
def set_execution_mode(self, execution_mode: str) -> None:
    """Set the task execution mode and reinitialize counters."""
```
