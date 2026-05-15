# TaskExecutor

> 📅 Last Updated: 2026/05/15

`TaskExecutor` is the core component for executing single task logic. It is responsible for task execution, concurrency control, error handling, retry mechanisms, and logging.

## Initialization

```python
class TaskExecutor:
    def __init__(
        self,
        name,
        func,
        execution_mode="serial",
        max_workers=20,
        max_retries=1,
        max_info=50,
        unpack_task_args=False,
        enable_duplicate_check=True,
        log_level="INFO",
    ):
        ...
```

### Parameter Description

- **name**: Executor name, used for logging and tracing.
- **func**: Callable object (function) that actually executes the task.
- **execution_mode**: Execution mode.
  - `serial`: Serial execution.
  - `thread`: Multi-threaded execution.
  - `async`: Asynchronous execution (`asyncio`).
- **max_workers**: Concurrency limit (number of threads/coroutines).
- **max_retries**: Maximum retry count after task failure.
- **max_info**: Maximum length of each log message.
- **unpack_task_args**: Whether to unpack task arguments (`*args`) when passing to the function.
- **enable_duplicate_check**: Whether to enable hash-based duplicate checking.
- **log_level**: Log level (TRACE/DEBUG/SUCCESS/INFO/WARNING/ERROR/CRITICAL).

## Observer Pattern

`TaskExecutor` broadcasts lifecycle events to external observers through the observer pattern.

### Register and Remove

```python
executor.add_observer(observer)     # Register observer
executor.remove_observer(observer)  # Remove observer
```

### Usage Example

```python
from celestialflow import TaskExecutor, TaskProgress, CallbackObserver

# Use TaskProgress to display progress bar
executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)

# Use CallbackObserver
observer = CallbackObserver(
    on_task_success=lambda count=1: print(f"Success: {count}"),
)
executor.add_observer(observer)
```

### Broadcast Events

| Event | Trigger Timing |
|-------|---------------|
| `on_start(name, total)` | Execution starts |
| `on_task_success(count)` | Task succeeds |
| `on_task_fail(count)` | Task fails |
| `on_task_duplicate(count)` | Duplicate detected |
| `on_tasks_added(count)` | New tasks added |
| `on_finish()` | Execution ends |

## Core Methods

### start

```python
def start(self, task_source: Iterable):
    """
    Start the executor, processing all tasks in task_source.
    Selects the appropriate running strategy based on execution_mode.
    """
```

### start_async

```python
async def start_async(self, task_source: Iterable):
    """
    Start the executor asynchronously (for async mode).
    """
```

## Error Handling

`TaskExecutor` catches exceptions during task execution:
- If the exception is in the `retry_exceptions` list and the maximum retry count has not been reached, the task is re-enqueued for retry.
- Otherwise, the task is marked as failed, an error log is recorded, and it is placed in the `fail_queue`.

### add_retry_exceptions

```python
def add_retry_exceptions(self, *exceptions):
    """
    Add exception types that should trigger retries.

    :param exceptions: List of exception types
    """
```

Example:
```python
executor = TaskExecutor("Processor", process, max_retries=3)
executor.add_retry_exceptions(ValueError, ConnectionError, TimeoutError)
```

## Result Handling

### Overridable Methods

- **process_result(task, result)**: Override this method to customize result processing logic.
- **get_args(task)**: Override this method to customize argument extraction logic.

### Retrieving Results

```python
# Get success result list
def get_success_pairs(self) -> list[tuple[Any, Any]]:
    ...

# Get failure result list
def get_error_pairs(self) -> list[tuple[Any, Exception]]:
    ...
```

### Processing Result Dictionaries

```python
# Process result dictionary (merge success and failure)
def process_result_dict(self) -> dict:
    ...

# Handle error dictionary (group by error type)
def handle_error_dict(self) -> dict:
    ...
```

## CelestialTree Integration

`TaskExecutor` supports the CelestialTree event tracking system for task tracing and debugging.

### set_ctree

```python
def set_ctree(self, host: str = "127.0.0.1", http_port: int = 7777, grpc_port: int = 7778):
    """
    Set up the CelestialTree client connection.

    :param host: CelestialTree service host address
    :param http_port: HTTP port
    :param grpc_port: gRPC port
    """
```

### set_nullctree

```python
def set_nullctree(self, event_id=None):
    """
    Set up a null client (no external service connection, only generates event IDs).

    :param event_id: Optional event ID
    """
```

## State Query Methods

### Getting Basic Information

```python
# Get executor name
def get_name(self) -> str: ...

# Get function name
def get_func_name(self) -> str: ...

# Get class name (private)
def _get_class_name(self) -> str: ...

# Get tag (for logging and tracing)
def get_tag(self) -> str: ...

# Get execution mode description (private)
def _get_execution_mode_desc(self) -> str: ...
```

### Getting State Snapshots

```python
def get_summary(self) -> dict:
    """
    Get the current node state snapshot.
    Returns: name, func_name, class_name, execution_mode
    """

def get_counts(self) -> dict:
    """
    Get the current node counters.
    Returns: tasks_input, tasks_succeeded, tasks_failed, tasks_duplicated, tasks_processed, tasks_pending
    """
```

## Runtime Information

### get_task_repr

```python
def get_task_repr(self, task) -> str:
    """
    Get a human-readable string representation of task arguments.
    Used for log output, automatically truncates overly long arguments.
    """
```

### _get_result_repr

```python
def _get_result_repr(self, result) -> str:
    """
    Get a human-readable string representation of the result.
    """
```

## Notes

### Execution Mode Selection

| Mode | Use Case | Notes |
|------|----------|-------|
| `serial` | Debugging, simple tasks | No concurrency |
| `thread` | I/O-intensive | Be aware of GIL limitations |
| `async` | Network I/O | Requires start_async |
