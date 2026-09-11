# node/core_node.py

> 📅 Last Updated: 2026/09/09

`core_node.py` defines the core base class `BaseTaskNode[T, R]` of the CelestialFlow node layer. It is responsible for centralizing runtime concerns such as "queue communication / task scheduling / metrics statistics / event tracing / persistence logging / observer callbacks" into a single object, and exposes entry methods like `run` / `start` for reuse by upper-layer `TaskExecutor` / `TaskSplitter` / `TaskRouter`.

> ⚠️ `BaseTaskNode` is an **internal base class** and **not exported as a public API**. Only `TaskExecutor` / `TaskSplitter` / `TaskRouter` are visible to users.

## Core Object

### `BaseTaskNode[T, R]`

| Field | Type | Description |
|------|------|------|
| `dispatch` | `TaskDispatch[T, R]` | Task scheduler (internal component), created by `__init__` |
| `task_queue` | `TaskInQueue[T]` | Input task queue |
| `result_queue` | `TaskOutQueue[R]` | Output result queue |
| `metrics` | `TaskMetrics` | Task metrics statistics object (success / fail / duplicate / elapsed) |
| `ctree_client` | `EventClient` | Event client (ctree), default `LocalEventClient()` |
| `func` | `Callable[[T], R]` or `Callable[[T], Awaitable[R]]` | Callback that actually executes the task |
| `execution_mode` | `str` | `'serial'` / `'thread'` / `'async'` |
| `max_workers` | `int` | Maximum concurrent workers (default `min(32, cpu_count+4)`) |
| `max_retries` | `int` | Maximum retries per task (`1` means "original + 1 retry") |
| `max_queue_size` | `int` | Input queue capacity upper limit (`0` means unbounded) |
| `max_info` | `int` | Maximum string length of each task in logs (default `50`) |
| `enable_duplicate_check` | `bool` | Whether to enable hash-based duplicate check |
| `_name` | `str` | Node / manager name |
| `start_time` | `float` | `time.time()` record of the most recent `start` |

```mermaid
classDiagram
    class BaseTaskNode {
        +TaskDispatch dispatch
        +TaskInQueue task_queue
        +TaskOutQueue result_queue
        +TaskMetrics metrics
        +EventClient ctree_client
        +Callable func
        +str execution_mode
        +int max_workers
        +int max_retries
        +int max_queue_size
        +int max_info
        +bool enable_duplicate_check
        +set_execution_mode(mode)
        +set_retry_exceptions(*exceptions)
        +set_ctree(client)
        +add_observer(observer)
        +remove_observer(observer)
        +put_task(task)
        +put_signal()
        +run(task_source)
        +run_async(task_source)
        +restore_db(db_path)
        +start()
        +start_async()
        +get_binding_counter(downstream_name)*
        +process_task_success(envelope, result, start_time)*
    }
```

## Initialization

```python
def __init__(
    self,
    name: str,
    func: Callable[[T], R] | Callable[[T], Awaitable[R]],
    *,
    execution_mode: str = "serial",
    max_workers: int | None = None,
    max_retries: int = 1,
    max_queue_size: int = 0,
    max_info: int = 50,
    enable_duplicate_check: bool = False,
): ...
```

Key behaviors of `__init__`:

1. Write the name via `set_name`;
2. `_set_func` validates the callback signature (must accept only 1 positional argument), otherwise throws `ConfigurationError`;
3. `set_execution_mode` validates the legality of the mode; if `execution_mode == "async"` but `func` is not `iscoroutinefunction`, throws `ConfigurationError`;
4. Initialize `max_workers / max_retries / max_queue_size / max_info / enable_duplicate_check`;
5. Install `LocalEventClient()` by default, replaceable via `set_ctree(...)` later;
6. Instantiate `TaskDispatch(cast(BaseTaskNode[T, R], self), self.func, self.max_workers)`, and create new `TaskInQueue` / `TaskOutQueue` / `TaskMetrics`.

## Configuration Setters

| Method | Purpose | Throws |
|------|------|------|
| `set_name(name)` | Write node / manager name | — |
| `set_execution_mode(execution_mode)` | Switch between `'serial'` / `'thread'` / `'async'` | `InvalidOptionError` (invalid mode), `ConfigurationError` (`async` but `func` is not a coroutine) |
| `set_ctree(ctree_client)` | Replace event client | — |
| `set_retry_exceptions(*exceptions)` | Register retryable exception types to `metrics` | — |
| `add_observer(observer)` / `remove_observer(observer)` | Register / unbind `BaseObserver` | — |
| `_set_func(func)` | Write and validate `func` signature | `ConfigurationError` (parameter count ≠ 1), `CallableParameterKindError` (contains VAR/KEYWORD parameters) |

> All setters must be called before `start()` / `start_async()`. They are **not guaranteed** to remain valid if modified again after `start`.

## Template Methods (Subclass must implement)

`BaseTaskNode` exposes two **abstract hooks** for `TaskExecutor` / `TaskSplitter` / `TaskRouter` to override:

| Method | Purpose |
|------|------|
| `get_binding_counter(downstream_name) -> ValueWrapper` | Tells upstream (predecessor) which downstream counter the current node expects to be bound to; a newly-created `BaseTaskNode` directly throws `NotImplementedError` |
| `process_task_success(envelope, result, start_time) -> None` | When the worker successfully gets a result, the node needs to do "metrics + persistence + downstream dispatch" etc.; a newly-created `BaseTaskNode` directly throws `NotImplementedError` |

> `TaskExecutor` uses `success_counter`, `TaskSplitter` uses its own `split_counter`, and `TaskRouter` maintains `route_counters` by downstream name.

Helper template method:

- `prev_binding(pending_prev_binding)`: Register the predecessor node's counter into the current node's `metrics.task_counter`.

## Task Injection

| Method | Behavior |
|------|------|
| `put_task(task)` | Wrap a single task into `TaskEnvelope`, emit `TASK_INPUT` event and enqueue; synchronously increment `metrics.add_task_count` |
| `put_signal()` | Put `TerminationSignal(source="input")` into the queue, emit `TERMINATION_INPUT` event |
| `drain_task_queue()` | Clear remaining tasks, process each leftover task as `UnconsumedError()` via `handle_task_fail` |

> `put_task` / `put_signal` both write persistence records via `get_lifecycle_inlet()` / `get_log_inlet()` simultaneously.

## Entry Methods

### `run(task_source, *, if_put_signal=True)`

```python
def run(self, task_source: Iterable[T], *, if_put_signal: bool = True) -> None:
    with funnel_scope():
        for task in task_source:
            self.put_task(task)
        if if_put_signal:
            self.put_signal()
        self.start()
```

`funnel_scope()` is responsible for starting/stopping the global `LifecycleSpout` / `LogSpout`.

### `async run_async(task_source, *, if_put_signal=True)`

Async version, calls `await self.start_async()`, also executed within the `funnel_scope()` context.

### `restore_db(db_path, statuses=None, *, filter_by_error_type=False)`

Load and replay unfinished tasks from the sqlite database:

1. `statuses` defaults to `["failed", "pending"]`;
2. When `filter_by_error_type=True`, the current node's `metrics.get_retry_error_type_names()` is used to filter `error_type`;
3. Take the `record["task_json"]` field and call `self.run(tasks)`.

### `start()`

- Preparation phase calls `self.metrics.reset_state()` and `metrics.on_start(...)`;
- Selects `dispatch.dispatch_serial()` / `dispatch.dispatch_thread()` based on `execution_mode`; `async` goes through `start_async`;
- The cleanup phase `_finish_start` closes the spout timing and broadcasts `on_finish`;
- Any exceptions in any phase are finally aggregated as `ExceptionGroup("Errors occurred during execution", ...)` thrown.

### `async start_async()`

- Only valid when `execution_mode == "async"`, otherwise throws `InvalidOptionError`;
- Internally `await self.dispatch.dispatch_async()`, exceptions additionally trigger `get_log_inlet().executor_crash(...)`.

## Results / Snapshots / Error Handling

| Method | Purpose |
|------|------|
| `handle_task_fail(envelope, exception)` | Record failure count + `TASK_ERROR` event + persist failure info |
| `log_task_retry(envelope, exception, retry_time)` | Write retry log |
| `deal_duplicate(envelope)` | Mark task as duplicate, write `TASK_DUPLICATE` event |
| `get_counts() -> dict` | Transparent pass-through of `metrics.get_counts()` |
| `get_lifecycle_path() -> Path` | Return absolute path of `LifecycleSpout.db_path` (returns empty `Path` when unset) |
| `snapshot(interval) -> dict` | Runtime snapshot for reporter (includes `status`, counts, estimated elapsed, remaining time, average task elapsed) |
| `get_success_pairs() -> list[tuple[T, R]]` | Pull successful tasks and results from `LifecycleSpout` |
| `get_error_pairs() -> list[tuple[T, PersistedError]]` | Pull failed tasks and `PersistedError` (with type and message) |

## Key Data Flow

```mermaid
flowchart LR
    subgraph "BaseTaskNode"
        PutTask[put_task] -->|envelope| TaskQueue[TaskInQueue]
        PutSignal[put_signal] -->|signal| TaskQueue
        TaskQueue --> Dispatch[TaskDispatch]
        Dispatch -->|serial / thread / async| Worker[worker / async_worker]
        Worker -->|on success| PTS[process_task_success]
        Worker -->|on fail| HTF[handle_task_fail]
        Worker -->|on retry| LTR[log_task_retry]
        Worker -->|duplicate| DD[deal_duplicate]
        PTS --> ResultQueue[TaskOutQueue]
        ResultQueue --> Downstream[(Downstream node)]
        PTS --> Metrics[TaskMetrics]
        HTF --> Metrics
        DD --> Metrics
    end

    PutTask --> CT[ctree_client]
    HTF --> CT
    DD --> CT
    PTS --> CT

    PutTask --> LCI[get_lifecycle_inlet]
    PutTask --> GLI[get_log_inlet]
    PTS --> LCI
    PTS --> GLI
    HTF --> LCI
    HTF --> GLI
    DD --> LCI
    DD --> GLI
    LCI --> SQLite[(sqlite persistence)]
    GLI --> LogStore[(log spout)]
```

## Usage Example

> `BaseTaskNode` is not used directly externally. The following example shows how to inherit it to write a custom node; in actual production, inheriting from `TaskExecutor` is more recommended.

```python
from celestialflow.node.core_node import BaseTaskNode
from celestialflow.runtime import TaskEnvelope


class SquareNode(BaseTaskNode[int, int]):
    """Minimal node example that squares an integer."""

    def get_binding_counter(self, _downstream_name):
        return self.metrics.success_counter

    def process_task_success(self, envelope, result, start_time):
        # Report + persist + forward
        task = envelope.get_task()
        result_id = self.ctree_client.emit("task.success", parents=[envelope.get_id()])
        self.metrics.add_success_count()
        for target in self.result_queue.get_target_names():
            downstream_id = self.ctree_client.emit("task.input", parents=[result_id])
            self.result_queue.put_target(TaskEnvelope(result, downstream_id), target)


node = SquareNode("Square", func=lambda x: x * x, execution_mode="serial")
node.run([1, 2, 3, 4])
print(node.get_counts())
```

## Exception Summary

| Exception | Trigger scenario |
|------|---------|
| `ConfigurationError` | Parameter count ≠ 1 in `_set_func`; `set_execution_mode("async")` but `func` is not a coroutine |
| `InvalidOptionError` | `execution_mode` not in `("serial", "thread", "async")` |
| `CallableParameterKindError` | Callback has non-`POSITIONAL_ONLY` / `POSITIONAL_OR_KEYWORD` parameters |
| `NotImplementedError` | Subclass does not override `get_binding_counter` / `process_task_success` |
| `ExceptionGroup` | Any exception during `start` / `start_async` is finally aggregated and thrown |

## Notes

1. **One-time `start`**: `start()` / `start_async()` are one-time calls and **not guaranteed** to be safely reset and reused after execution; if repeat execution is needed, create a new node.
2. **Setter timing**: All setters must be completed before `start`; do not replace `func` during runtime.
3. **Lifecycle management**: The global `LifecycleSpout` / `LogSpout` is managed by `funnel_scope()`; `BaseTaskNode` does not directly hold the spout / inlet.
4. **ctree client**: The default `LocalEventClient()` auto-increments event IDs internally; it can be replaced at any time via `set_ctree(...)` with a client that connects to `celestialtree`.
5. **Duplicate check**: When `enable_duplicate_check=True`, the scheduler calls `metrics.is_duplicate(task_hash)` before consuming the envelope; on hit, it is handled by `deal_duplicate`.
