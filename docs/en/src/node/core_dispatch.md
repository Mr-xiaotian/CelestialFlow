# src/celestialflow/node/core_dispatch.py

> 📅 Last Updated: 2026/10/30

`core_dispatch.py` defines `TaskDispatch[T, R, Y]`, the "task scheduler" component held by `BaseTaskNode`. It pulls `TaskEnvelope` / termination signals from the node object's input queue, invokes the node callback serially / in threads / asynchronously according to `execution_mode`, and is responsible for merging termination signals, initializing / releasing thread pools, and handing exceptions caught at the worker's outermost layer back to the host's `handle_task_fail` for unified handling.

> `TaskDispatch` is an **internal component** of `BaseTaskNode`, automatically created by `BaseTaskNode.__init__` at construction; it is not a public API and does not appear in `__all__` of `node/__init__.py`.

## Core Object

### `TaskDispatch[T, R, Y]`

```python
class TaskDispatch[T, R, Y]:
    def __init__(
        self,
        task_node: BaseTaskNode[T, R, Y],
        func: Callable[[T], R] | Callable[[T], Awaitable[R]],
        max_workers: int,
    ): ...
```

| Field | Type | Description |
|------|------|------|
| `task_node` | `BaseTaskNode[T, R, Y]` | Host node (**not** `TaskExecutor`, but the base class) |
| `func` | `Callable[[T], R] | Callable[[T], Awaitable[R]]` | Node callback reference |
| `max_workers` | `int` | Concurrency upper limit |
| `_pool` | `ThreadPoolExecutor | None` | Thread pool (used only in thread mode) |

> The scheduler will reverse-call through the host object: `task_node.observers` / `task_node.process_task_success` / `handle_task_fail` / `log_task_retry` / `get_name` / `ctree_client.emit` / `task_queue` / `yield_queue`, etc.

## Public Dispatch Methods

| Method | Purpose |
|------|------|
| `dispatch_serial()` | Consume the task queue synchronously in the current thread; merge and exit when encountering `TerminationIdPool` |
| `dispatch_thread()` | Concurrent consumption using `ThreadPoolExecutor`; block and wait for a free slot when the number of tasks ≥ `max_workers` |
| `async dispatch_async()` | Async consumption throttled by a `pending` task set; stream-arriving, run-as-it-comes |

### `dispatch_serial`

Main loop pseudocode:

```text
while True:
    envelope = task_queue.get()
    if isinstance(envelope, TerminationIdPool):
        termination_signal = _process_termination_signal(envelope)
        break
    _worker(envelope)
yield_queue.put(termination_signal)
```

### `dispatch_thread`

```text
_init_pool("thread")
try:
    pending = set[Future[None]]()
    while True:
        envelope = task_queue.get()
        if isinstance(envelope, TerminationIdPool):
            termination_signal = _process_termination_signal(envelope)
            break
        # Throttle: block until completed futures when pending count ≥ max_workers
        while len(pending) >= max_workers:
            _, pending = wait(pending, return_when=FIRST_COMPLETED)
        pending.add(_pool.submit(_worker, envelope))
    wait(pending)  # Wait for the current batch to complete
    yield_queue.put(termination_signal)
finally:
    _release_pool()
```

### `dispatch_async`

```text
pending = set[asyncio.Task[None]]()

async def worker(envelope):
    await _async_worker(envelope)

while True:
    envelope = await asyncio.to_thread(task_queue.get)  # Do not block the event loop
    if isinstance(envelope, TerminationIdPool):
        termination_signal = _process_termination_signal(envelope)
        break

    # Throttle: wait for the earliest completed task when pending count ≥ max_workers
    while len(pending) >= max_workers:
        _, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

    task = asyncio.create_task(worker(envelope))
    pending.add(task)

if pending:
    await asyncio.gather(*pending)  # Wait for the batch still executing after the queue is drained
yield_queue.put(termination_signal)
```

> The async path **does not use `asyncio.Semaphore`**: the concurrency limit is controlled entirely by the `len` of the `pending` set. Each iteration checks `len(pending) >= self.max_workers` before creating a new task, and waits for a free slot via `asyncio.wait(..., return_when=asyncio.FIRST_COMPLETED)`; after receiving the termination signal no new tasks are accepted, but `asyncio.gather` waits for all in-flight tasks to finish before delivering the merged termination signal downstream.

## Internal Helper Methods

| Method | Behavior |
|------|------|
| `_call_sync(task) -> R` | Call sync callback; raise `ConfigurationError` if it returns awaitable |
| `_call_async(task) -> R` | Call async callback; raise `ConfigurationError` if the return value is not awaitable |
| `_worker(envelope) -> None` | Execute a single task synchronously: first check `skip_func`, then loop over `for fail_times in range(1, max_retries + 2)`; call `task_node.log_task_retry` when hitting `retry_exceptions`, call `handle_task_fail` when the retry limit is reached or for a non-retryable exception, and call `process_task_success` on success. The outermost `try` likewise calls `task_node.handle_task_fail(task_envelope, exception)` as a fallback for unhandled exceptions |
| `_async_worker(envelope) -> None` | Async version of `_worker`, using `await self._call_async(task)`; outermost exceptions are likewise handed to `handle_task_fail` as a fallback |
| `_process_termination_signal(pool) -> TerminationSignal` | Merge all ids in `TerminationIdPool.ids` into a single `TerminationSignal(source=task_node.get_name())` via `ctree_client.emit(CTreeEvent.TERMINATION_MERGE, parents=...)`, and broadcast `TerminationMergeEvent` |
| `_init_pool(execution_mode)` | Only when `execution_mode == "thread"` and `_pool is None`, construct `ThreadPoolExecutor(max_workers=self.max_workers)` |
| `_release_pool()` | Close and clear `_pool` (called when thread mode ends) |

### `_worker` Retry Loop Details

```python
def _worker(self, task_envelope: TaskEnvelope[T]) -> None:
    try:
        task = task_envelope.get_task()
        if self.task_node.skip_func is not None and self.task_node.skip_func(task):
            self.task_node.handle_task_skip(task_envelope)
            return

        max_retries = self.task_node.max_retries
        for fail_times in range(1, max_retries + 2):
            try:
                start_perf = time.perf_counter()
                result = self._call_sync(task)
                self.task_node.process_task_success(task_envelope, result, start_perf)
                return
            except Exception as exception:
                if fail_times > max_retries or not isinstance(
                    exception, self.task_node.retry_exceptions
                ):
                    self.task_node.handle_task_fail(task_envelope, exception)
                    return
                self.task_node.log_task_retry(task_envelope, exception, fail_times)
    except Exception as exception:
        self.task_node.handle_task_fail(task_envelope, exception)
```

## Key Data Flow

```mermaid
sequenceDiagram
    participant Q as TaskInQueue
    participant D as TaskDispatch
    participant W as _worker / _async_worker
    participant N as BaseTaskNode
    participant R as TaskOutQueue

    loop Consume tasks
        D->>Q: get()
        alt Termination signal pool
            D->>N: _process_termination_signal(pool)
            D->>R: put(termination_signal)
            Note over D: Exit loop
        else Normal envelope
            D->>W: _worker(envelope)
            W->>N: process_task_success / handle_task_fail / log_task_retry
            N->>N: observers broadcast the corresponding event
        end
    end
```

## Exception Summary

| Exception | Trigger scenario |
|------|---------|
| `ConfigurationError` | Sync call returns awaitable / async call returns non-awaitable |
| `InitializationError` | `_pool is None` in `dispatch_thread` (theoretically guaranteed by `_init_pool`, but code retains a fallback) |

> Other exceptions caught at the worker's outermost layer are not re-raised into the framework scheduling path; instead they are counted in the task's failure record via `task_node.handle_task_fail(task_envelope, exception)` (which triggers `TaskFailEvent` and persists `error_type` / `error_message`).

## Relationship with Host `BaseTaskNode`

```mermaid
classDiagram
    class BaseTaskNode {
        +TaskDispatch dispatch
        +TaskInQueue task_queue
        +TaskOutQueue yield_queue
        +ObserverHub observers
        +EventClient ctree_client
    }
    class TaskDispatch {
        +BaseTaskNode task_node
        +Callable func
        +int max_workers
        +dispatch_serial()
        +dispatch_thread()
        +dispatch_async()
    }

    BaseTaskNode "1" *-- "1" TaskDispatch : Created at construction
    TaskDispatch ..> BaseTaskNode : Reverse-calls process_task_success etc.
```

> In `BaseTaskNode.__init__`, host binding is completed via `self.dispatch = TaskDispatch(cast(BaseTaskNode[T, R, Y], self), self.func, self.max_workers)`.

## Notes

1. **Host type is `BaseTaskNode` rather than `TaskExecutor`**: Even if the actual instance passed in is `TaskSplitter` / `TaskRouter`, the scheduler only accesses the host through the `BaseTaskNode` interface.
2. **Termination signal path**: A single `TerminationSignal` in `TaskInQueue` will be merged with other sources into `TerminationIdPool`; when receiving the pool, the scheduler uniformly emits `TERMINATION_MERGE` and broadcasts `TerminationMergeEvent`.
3. **Thread pool lifecycle**: `_pool` only temporarily exists in `dispatch_thread`, with `_init_pool` at entry and `_release_pool` at exit, so the same scheduler does not support cross-`start` reuse.
4. **Async path does not block the event loop**: `dispatch_async` pulls input with `asyncio.to_thread(task_queue.get)` and controls concurrency through the `len` of the `pending` set plus `asyncio.wait(FIRST_COMPLETED)`, achieving "stream-while-running" without stalling the event loop; `asyncio.Semaphore` is not used.
5. **Worker fallback exceptions go back to the host**: the outermost `except Exception` in `_worker` / `_async_worker` calls `task_node.handle_task_fail(task_envelope, exception)`; it no longer broadcasts a crash event to observers, nor writes `worker_crash` to the log inlet.
6. **Skip detection is supported**: `_worker` / `_async_worker` check `skip_func` before execution; if it is hit, they call `handle_task_skip` and return directly.
