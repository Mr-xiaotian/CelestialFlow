# TaskExecutor

> 📅 Last updated: 2026/04/23

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
        enable_success_cache=False,
        enable_duplicate_check=True,
        show_progress=False,
        progress_desc="Executing",
        log_level="SUCCESS",
    ):
        ...
```

### Parameters

- **name**: The name of the executor, used for logging and tracing.
- **func**: The callable object (function) that actually executes the task.
- **execution_mode**: Execution mode.
  - `serial`: Serial execution.
  - `thread`: Multi-threaded execution.
  - `process`: Multi-process execution (Note: this mode is typically not used as part of a `TaskGraph`; instead, it is managed by `TaskStage`).
  - `async`: Asynchronous execution (`asyncio`).
- **max_workers**: Concurrency limit (number of threads/processes/coroutines).
- **max_retries**: Maximum number of retries after task failure.
- **max_info**: Maximum length of each log message.
- **unpack_task_args**: Whether to unpack task arguments (`*args`) when passing them to the function.
- **enable_success_cache**: Whether to cache successful results in `success_dict`.
- **enable_duplicate_check**: Whether to enable hash-based duplicate checking for tasks.
- **show_progress**: Whether to display a progress bar.
- **progress_desc**: Display name for the progress bar.
- **log_level**: Log level (TRACE/DEBUG/SUCCESS/INFO/WARNING/ERROR/CRITICAL).

## Core Methods

### start

```python
def start(self, task_source: Iterable):
    """
    Start the executor and process all tasks in task_source.
    Selects the appropriate execution strategy based on execution_mode.
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
- If the exception is in the `retry_exceptions` list and the maximum retry count has not been reached, the task is re-queued for retry.
- Otherwise, the task is marked as failed, an error log is recorded, and it is placed in the `fail_queue`.

### add_retry_exceptions

```python
def add_retry_exceptions(self, *exceptions):
    """
    Add exception types that should trigger a retry.

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
# Get the success result pairs (requires enable_success_cache=True)
def get_success_pairs(self) -> list[tuple[Any, Any]]:
    ...

# Get the failure result pairs
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
    Set up a CelestialTree client connection.

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

## Status Query Methods

### Getting Basic Information

```python
# Get the executor name
def get_name(self) -> str: ...

# Get the function name
def get_func_name(self) -> str: ...

# Get the class name (private)
def _get_class_name(self) -> str: ...

# Get the tag (used for logging and tracing)
def get_tag(self) -> str: ...

# Get the execution mode description (private)
def _get_execution_mode_desc(self) -> str: ...
```

### Getting Status Snapshots

```python
def get_summary(self) -> dict:
    """
    Get a status snapshot of the current node.
    Returns: name, func_name, class_name, execution_mode
    """

def get_counts(self) -> dict:
    """
    Get the counters of the current node.
    Returns: total, success, error, duplicate
    """
```

## Runtime Information

### get_task_repr

```python
def get_task_repr(self, task) -> str:
    """
    Get a human-readable string representation of task arguments.
    Used for log output; automatically truncates overly long arguments.
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

### Cache and Duplicate Checking

When caching is enabled but duplicate checking is disabled, a warning is triggered:

```python
# Warning: may cause mismatch between cached result count and input task count
executor = TaskExecutor(
    "Processor",
    process,
    enable_success_cache=True,
    enable_duplicate_check=False  # Not recommended
)
```

### Execution Mode Selection

| Mode | Use Case | Notes |
|------|----------|-------|
| `serial` | Debugging, simple tasks | No concurrency |
| `thread` | I/O-intensive tasks | Be aware of GIL limitations |
| `process` | CPU-intensive tasks | Requires pickleable functions |
| `async` | Network I/O | Requires using start_async |
