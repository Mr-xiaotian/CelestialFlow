# TaskDispatch

`TaskDispatch` is the core task execution runner responsible for fetching tasks from queues, executing them, and handling results and errors. It supports three execution modes: serial, thread pool, and async.

## Initialization

```python
class TaskDispatch:
    def __init__(self, task_executor: TaskExecutor, func, max_workers: int):
        """
        Initialize the task runner.

        :param task_executor: Task executor (TaskExecutor instance)
        :param func: Task function
        :param max_workers: Maximum number of worker threads or processes
        """
```

## Execution Modes

### run_in_serial

Executes tasks serially, processing one after another.

```python
def run_in_serial(self):
    """
    Execute tasks serially.

    Fetches tasks from task_queues, executes them sequentially until a termination signal
    is received and all tasks are completed.
    """
```

Execution flow:
1. Fetch a task from `task_queues.get()`
2. Check if it is a termination signal (`TerminationIdPool`)
3. Check if the task is a duplicate
4. Execute the task and handle the result or error
5. Update the progress bar
6. After receiving a termination signal, check if all tasks are completed

### run_in_thread

Executes tasks in parallel using a thread pool.

```python
def run_in_thread(self):
    """
    Execute tasks in parallel using a thread pool.
    """
```

Execution flow:
1. Initialize the thread pool
2. Fetch tasks from the queue and submit them to the pool
3. Wait for all futures to complete, then handle the termination signal
4. Shut down the pool and release resources

### run_in_async

Executes tasks asynchronously using coroutines and semaphores for concurrency control.

```python
async def run_in_async(self):
    """
    Execute tasks asynchronously with limited concurrency.
    """
```

Execution flow:
1. Create a semaphore to limit concurrency
2. Fetch tasks asynchronously
3. Execute tasks concurrently using `asyncio.gather`
4. Handle results and errors
5. Check termination conditions

## Internal Methods

### _worker / _async_worker

```python
def _worker(self, envelope: TaskEnvelope):
    """Worker function in the thread pool that executes a single task and handles retries."""

async def _async_worker(self, envelope: TaskEnvelope):
    """Async worker function that executes a single task and handles retries."""
```

### process_termination_signal

```python
def process_termination_signal(self, termination_pool: TerminationIdPool) -> TerminationSignal:
    """
    Process a termination signal and generate a merge event.

    :param termination_pool: Pool containing multiple termination signal IDs
    :return: Merged termination signal
    """
```

### release_pool

```python
def release_pool(self):
    """Shut down the thread pool and release resources."""
```

## Relationship with TaskExecutor

`TaskDispatch` is an internal component of `TaskExecutor`:

```
TaskExecutor
    ├── func               # Task function
    ├── task_queues        # Input queue (TaskInQueue)
    ├── result_queues      # Output queue (TaskOutQueue)
    ├── metrics            # Task metrics
    └── dispatch           # TaskDispatch instance
            ├── func               # Task function
            ├── max_workers        # Concurrency limit
            ├── run_in_serial()
            ├── run_in_thread()
            └── run_in_async()
```

`TaskExecutor` selects which `TaskDispatch` method to call based on `execution_mode`:
- `serial` → `run_in_serial()`
- `thread` → `run_in_thread()`
- `async` → `run_in_async()`

## Notes

1. **Concurrency Control**: `max_workers` limits the number of concurrent tasks to prevent resource exhaustion
2. **Termination Handling**: Properly handles merging and forwarding of termination signals
3. **Error Propagation**: Exceptions are caught and passed to `TaskExecutor.handle_task_fail()`
4. **Retry Mechanism**: Workers internally support task retries, controlled by `max_retries`
5. **Async Limitation**: `run_in_async` requires the task function to be a coroutine function
