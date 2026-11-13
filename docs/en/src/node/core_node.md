# src/celestialflow/node/core_node.py

> 📅 Last Updated: 2026/11/13

`core_node.py` defines the core base class `BaseTaskNode[T, R, Y]` of the CelestialFlow node layer. It centralizes runtime concerns such as "queue communication / task scheduling / event tracing / observer callbacks" into a single object, and exposes entry methods like `run` / `start` for reuse by upper-layer `TaskExecutor` / `TaskSplitter` / `TaskRouter`.

> ⚠️ `BaseTaskNode` is an **internal base class** and **not exported as a public API**. Only `TaskExecutor` / `TaskSplitter` / `TaskRouter` are visible to users.

## Core Object

### `BaseTaskNode[T, R, Y]`

The three generic parameters respectively represent: the input task type `T`, the direct return type `R` of `func`, and the result type `Y` sent downstream.

| Field | Type | Description |
|------|------|------|
| `dispatch` | `TaskDispatch[T, R, Y]` | Task scheduler (internal component), created by `__init__` |
| `task_queue` | `TaskInQueue[T]` | Input task queue |
| `yield_queue` | `TaskOutQueue[Y]` | Output result queue (to downstream nodes) |
| `ctree_client` | `EventClient` | Event client (ctree), default `LocalEventClient()` |
| `observers` | `ObserverHub` | Observer dispatch hub; observers are registered via `add_observer()` |
| `func` | `Callable[[T], R]` or `Callable[[T], Awaitable[R]]` | Callback that actually executes the task |
| `execution_mode` | `str` | `'serial'` / `'thread'` / `'async'`, default `'serial'` |
| `max_workers` | `int` | Maximum concurrent workers (default `min(32, cpu_count+4)`) |
| `max_retries` | `int` | Maximum retries per task (`1` means "original attempt + one retry"); clamped to `max(max_retries, 0)` at construction, so negative values are treated as `0` |
| `retry_exceptions` | `tuple[type[Exception], ...]` | Retryable exception types, registered via `set_retry_exceptions` |
| `max_queue_size` | `int` | Input queue capacity upper limit (`0` means unbounded) |
| `max_info` | `int` | Maximum string length of each task in logs (default `50`) |
| `skip_func` | `Callable[[T], bool] | None` | Task-skip decision function, default `None` means never skip |
| `_name` | `str` | Node / manager name |

> The node **does not hold** a lifecycle database path field: when persisted results need to be read, `_find_lifecycle_db_path()` recursively searches the observer hub through `self.observers.find(LifecycleObserver)` (which can look through nested graph-level hubs) and takes its `db_path`.

```mermaid
classDiagram
    class BaseTaskNode {
        +TaskDispatch dispatch
        +TaskInQueue task_queue
        +TaskOutQueue yield_queue
        +EventClient ctree_client
        +ObserverHub observers
        +Callable func
        +str execution_mode
        +int max_workers
        +int max_retries
        +int max_queue_size
        +int max_info
        +set_name(name)
        +set_execution_mode(mode)
        +set_retry_exceptions(*exceptions)
        +set_ctree(client)
        +set_skip_func(func)
        +add_observer(observer)
        +connect_to(next_node)
        +put_task(task)
        +put_signal()
        +drain_task_queue()
        +run(task_source, log_level)
        +run_async(task_source, log_level)
        +restore_db(db_path, log_level)
        +start()
        +start_async()
        +get_meta()
        +get_success_pairs()
        +get_error_pairs()
        +process_task_success(envelope, result, start_perf)*
    }
```

> Note: the node **no longer holds `TaskMetrics`**. Counting and statistics are maintained by `MetricsObserver` based on events (registered by the graph/node assembly entry when running independently; see below), and `BaseTaskNode` itself only broadcasts events through `observers`.

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
    skip_func: Callable[[T], bool] | None = None,
): ...
```

Key behaviors of `__init__`:

1. Write the name via `set_name`; `_set_func` validates the callback signature (must accept only 1 positional argument), otherwise throw `ConfigurationError`;
2. `set_skip_func` registers the task-skip decision function (also requiring a single positional argument); `None` means never skip;
3. `set_execution_mode` validates the legality of the mode; if `execution_mode == "async"` but `func` is not `iscoroutinefunction`, throw `ConfigurationError`;
4. Initialize `max_workers / max_retries / max_queue_size / max_info`: `max_workers` defaults to `min(32, (os.cpu_count() or 1) + 4)`; `max_retries` is clamped via `max(max_retries, 0)`, so negative values are treated as `0`; then `retry_exceptions` is preset to an empty tuple;
5. Install `LocalEventClient()` by default, replaceable via `set_ctree(...)` later;
6. Instantiate `TaskDispatch(cast(BaseTaskNode[T, R, Y], self), self.func, self.max_workers)`, and create new `TaskInQueue` (with `out_name` as the node name) / `TaskOutQueue` (with `in_name` as the node name) / `ObserverHub`;
7. No lifecycle path field is set: persistence observers are registered into `observers` by `run_node_resources` (independent run) or by graph-level observers (graph scheduling), and are located via `observers.find(...)` when results need to be read.

## Configuration Setters

| Method | Purpose | Throws |
|------|------|------|
| `set_name(name)` | Write node / manager name | — |
| `set_execution_mode(execution_mode)` | Switch between `'serial'` / `'thread'` / `'async'` | `InvalidOptionError` (invalid mode), `ConfigurationError` (`async` but `func` is not a coroutine) |
| `set_ctree(ctree_client)` | Replace event client | — |
| `set_retry_exceptions(*exceptions)` | Append retryable exception types to `retry_exceptions` | — |
| `set_skip_func(skip_func)` | Set the task-skip decision function | `ConfigurationError` (parameter count ≠ 1), `CallableParameterKindError` (contains VAR/KEYWORD parameters) |
| `add_observer(observer)` | Register an `Observer` into `ObserverHub` | — |
| `_set_func(func)` | Write and validate `func` signature | `ConfigurationError` (parameter count ≠ 1), `CallableParameterKindError` (contains VAR/KEYWORD parameters) |

> All setters must be called before `start()` / `start_async()`. They are **not guaranteed** to remain valid if modified again after `start`.

## Template Methods and Queries

`BaseTaskNode` exposes only one **abstract hook** for `TaskExecutor` / `TaskSplitter` / `TaskRouter` to override:

| Method | Purpose |
|------|------|
| `process_task_success(task_envelope, result, start_perf) -> None` | When the worker successfully gets a result, the node needs to do "event broadcasting + downstream dispatch" etc.; a newly-created `BaseTaskNode` directly throws `NotImplementedError` |

Helper query methods:

- `get_name() -> str`: Returns the node name.
- `_get_class_name() -> str`: Returns the current node class name.
- `get_meta() -> dict[str, Any]`: Returns the build-time metadata `{"class_name", "execution_mode", "max_workers"}`, reported once along with the graph structure.
- `get_retry_error_type_names() -> set[str]`: Returns the set of `__name__` of each class in `retry_exceptions`, used by `restore_db` to filter by error type.
- `get_success_pairs() -> list[tuple[T, R]]`: Locates the lifecycle database via `_find_lifecycle_db_path()` and reads successful `(task, result)` records. **Available both when running independently and under graph scheduling**; returns an empty list only when no `LifecycleObserver` is found (or its `db_path` is not ready yet).
- `get_error_pairs() -> list[tuple[T, PersistedError]]`: Likewise reads failure records from the lifecycle database and wraps them as `PersistedError`; the conditions for availability are the same as `get_success_pairs()`.

> The node **no longer provides** legacy interfaces such as `get_snapshot()` / `get_lifecycle_path()` / `start_time`. Runtime state is provided by the snapshot view of `MetricsObserver` (`MetricsView.get_node_metrics()`), and the lifecycle database path is obtained by recursively searching the observer hub (`_find_lifecycle_db_path()`).

## Binding Downstream

`connect_to(next_node)` establishes the transport connection from the current node to a downstream:

```python
def connect_to(self, next_node: BaseTaskNode[Any, Any, Any]) -> None:
    self.yield_queue.add_queue(next_node.get_name(), next_node.task_queue)
    next_node.task_queue.add_source_name(self.get_name())
```

Binding only establishes the data path between nodes and queues. Upstream/downstream transport counts **no longer share counter objects**; instead, `MetricsObserver` derives them when it receives `TaskInputEvent` (an upstream delivery is counted into both the receiver's upstream count and the source's downstream count). Therefore `connect_to` only does binding and does not participate in counting.

## Task Injection

| Method | Behavior |
|------|------|
| `put_task(task)` | Wrap a single task into `TaskEnvelope(task, input_id)`, where `input_id` is generated by `ctree_client.emit(CTreeEvent.TASK_INPUT)`; then enqueue it and broadcast `TaskInputEvent` (`from_node=None` indicates external injection) |
| `put_signal()` | Use `ctree_client.emit(CTreeEvent.TERMINATION_INPUT)` to generate `termination_id`, construct `TerminationSignal(termination_id, source="input")` into the queue, and broadcast `TerminationInputEvent` |
| `drain_task_queue()` | Clear the task queue, processing each leftover task as `UnconsumedError()` via `handle_task_fail` |

## Entry Methods

### `run(task_source, *, if_put_signal=True, log_level=DEFAULT_LOG_LEVEL)`

```python
def run(
    self,
    task_source: Iterable[T],
    *,
    if_put_signal: bool = True,
    log_level: str = DEFAULT_LOG_LEVEL,
) -> None:
    error_list: list[Exception] = []
    try:
        with run_node_resources(self.observers, log_level=log_level):
            for task in task_source:
                self.put_task(task)
            if if_put_signal:
                self.put_signal()
            self.start()
    except Exception as exception:
        error_list.append(exception)
    if error_list:
        raise ExceptionGroup("Errors occurred during run", error_list)
```

Parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task_source` | `Iterable[T]` | required | Task source to inject |
| `if_put_signal` | `bool` | `True` | Whether to automatically call `put_signal()` after injecting tasks |
| `log_level` | `str` | `DEFAULT_LOG_LEVEL` (`"INFO"`) | Log filter level for `LogObserver`, passed through unchanged to `run_node_resources` |

`run_node_resources` (located in `celestialflow.assembly`) is responsible for assembling the runtime resources of a single node: creating and registering `MetricsObserver`, and assembling `LifecycleObserver` / `LogObserver` (each holding and starting/stopping its spout). When this context manager is entered it still produces the lifecycle database path, but `BaseTaskNode.run` no longer caches it—`get_success_pairs()` / `get_error_pairs()` retrieve it on demand via `observers.find(LifecycleObserver)`. `log_level` is normalized by `normalize_log_level` (ignoring case and leading/trailing whitespace); an invalid level raises `InvalidOptionError`, and a non-string raises `ConfigurationError`.

### `async run_async(task_source, *, if_put_signal=True, log_level=DEFAULT_LOG_LEVEL)`

Async version; the parameter meanings are exactly the same as `run` (including `log_level` pass-through), except that it finally calls `await self.start_async()`, likewise executing within the `run_node_resources(self.observers, log_level=log_level)` context.

### `restore_db(db_path, statuses=None, *, filter_by_error_type=False, log_level=DEFAULT_LOG_LEVEL)`

Load and replay unfinished tasks from the sqlite database:

1. `statuses` defaults to `["failed", "pending"]`;
2. Load records by node name via `load_tasks_grouped_by_node(db_path, statuses)`;
3. When `filter_by_error_type=True`, use `get_retry_error_type_names()` to filter `error_type` (`pending` records are always retained);
4. Take the `record["task_json"]` field and call `self.run(tasks, log_level=log_level)`, i.e. `log_level` is further passed through to the independent-run entry.

### `start()`

- The preparation phase `_prepare_start` broadcasts the start event via `observers.on_event(NodeStartEvent(...))` (including `execution_mode` / `max_workers` / `start_time=time.time()`);
- Selects `dispatch.dispatch_serial()` / `dispatch.dispatch_thread()` based on `execution_mode`; `async` goes through `start_async`, otherwise throws `InvalidOptionError`;
- The cleanup phase `_finish_start` broadcasts the end event via `observers.on_event(NodeEndEvent(...))` (including `elapsed` and `end_time=time.time()`);
- Any exceptions in any phase are finally aggregated as `ExceptionGroup("Errors occurred during execution", ...)` thrown.

### `async start_async()`

- Only valid when `execution_mode == "async"`, otherwise throws `InvalidOptionError`;
- Internally `await self.dispatch.dispatch_async()`; the cleanup phase likewise broadcasts via `observers.on_event(NodeEndEvent(...))` (carrying `end_time`).

## Results / Events / Error Handling

| Method | Purpose |
|------|------|
| `process_task_success(envelope, result, start_perf)` | Abstract hook; subclasses implement successful handling |
| `handle_task_fail(envelope, exception)` | Use `ctree_client.emit(CTreeEvent.TASK_ERROR, parents=[task_id])` to generate `error_id`, then `observers.on_event(TaskFailEvent(...))` |
| `handle_task_skip(envelope)` | Use `ctree_client.emit(CTreeEvent.TASK_SKIP, parents=[task_id])` to generate `skip_id`, then `observers.on_event(TaskSkipEvent(...))` |
| `log_task_retry(envelope, exception, fail_times)` | `observers.on_event(TaskRetryEvent(...))` (including `retry_times`); the lifecycle status update is completed by `LifecycleObserver` in response to the event |
| `_get_repr(task) -> str` | Generate a readable string via `format_repr(task, self.max_info)` |
| `_find_lifecycle_db_path() -> Path | None` | Recursively locate and return the observer's `db_path` via `observers.find(LifecycleObserver)`; `None` when not found |

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
        PTS --> YieldQueue[TaskOutQueue]
        YieldQueue --> Downstream[(Downstream node)]
        PTS -->|TaskSuccessEvent| Hub[ObserverHub]
        HTF -->|TaskFailEvent| Hub
        LTR -->|TaskRetryEvent| Hub
    end

    PutTask --> CT[ctree_client]
    HTF --> CT
    PTS --> CT

    Hub --> Metrics[MetricsObserver]
    Hub --> Lifecycle[LifecycleObserver]
    Hub --> Log[LogObserver]
    Lifecycle --> SQLite[(sqlite persistence)]
    Log --> LogStore[(log file)]
```

`ObserverHub` is the export end of node event broadcasting: when an event occurs, nodes uniformly call `self.observers.on_event(SomeEvent(...))`, and the registered `MetricsObserver` / `LifecycleObserver` / `LogObserver` etc. respectively update counts, write to the database, and write logs. These observers are assembled and injected by `run_node_resources` (for independent running) or the graph-level client; during graph scheduling, a graph-level hub is nested inside the node's hub, so `observers.find(...)` can look through it.

## Usage Example

> `BaseTaskNode` is not used directly externally. The following example shows how to inherit it to write a custom node; in actual production, inheriting from `TaskExecutor` is more recommended.

```python
from celestialflow.node.core_node import BaseTaskNode
from celestialflow.runtime import TaskEnvelope
from celestialflow.runtime.util_types import CTreeEvent
from celestialflow.observer import TaskSuccessEvent, TaskInputEvent


class SquareNode(BaseTaskNode[int, int, int]):
    """Minimal node example that squares an integer."""

    def process_task_success(self, task_envelope, result, start_perf):
        task = task_envelope.get_task()
        task_id = task_envelope.get_id()

        result_id = self.ctree_client.emit(CTreeEvent.TASK_SUCCESS, parents=[task_id])
        self.observers.on_event(
            TaskSuccessEvent(
                node=self.get_name(),
                task=task,
                task_repr=str(task),
                result=result,
                result_repr=str(result),
                elapsed=0.0,
                task_id=task_id,
                success_id=result_id,
            )
        )

        for target in self.yield_queue.get_target_names():
            downstream_id = self.ctree_client.emit(
                CTreeEvent.TASK_INPUT, parents=[result_id]
            )
            self.observers.on_event(
                TaskInputEvent(
                    node=target,
                    task=result,
                    task_repr=str(result),
                    input_id=downstream_id,
                    from_node=self.get_name(),
                )
            )
            self.yield_queue.put_target(
                target, TaskEnvelope(task=result, id=downstream_id)
            )


node = SquareNode("Square", lambda x: x * x, execution_mode="serial")
node.run([1, 2, 3, 4])
```

## Exception Summary

| Exception | Trigger scenario |
|------|---------|
| `ConfigurationError` | Parameter count ≠ 1 in `_set_func` / `set_skip_func`; `set_execution_mode("async")` but `func` is not a coroutine; `log_level` is not a string |
| `InvalidOptionError` | `execution_mode` not in `("serial", "thread", "async")`; `start()` when the mode is neither serial nor thread; `log_level` not in the allowed level set for `run` / `run_async` / `restore_db` |
| `CallableParameterKindError` | Callback has non-`POSITIONAL_ONLY` / `POSITIONAL_OR_KEYWORD` parameters |
| `NotImplementedError` | Subclass does not override `process_task_success` |
| `ExceptionGroup` | Any exception during `run` / `run_async` / `start` / `start_async` is finally aggregated and thrown |

## Notes

1. **One-time `start`**: `start()` / `start_async()` are one-time calls and **not guaranteed** to be safely reset and reused after execution; if repeat execution is needed, create a new node.
2. **Setter timing**: All setters must be completed before `start`; do not replace `func` during runtime.
3. **Runtime resources are managed by the assembly entry**: `MetricsObserver` / `LifecycleObserver` / `LogObserver` are assembled by `run_node_resources` (for independent running) or the graph-level client; `BaseTaskNode` itself does not directly hold spouts / inlets; `get_success_pairs()` / `get_error_pairs()` are likewise available under graph scheduling.
4. **ctree client**: The default `LocalEventClient()` auto-increments event IDs internally; it can be replaced at any time via `set_ctree(...)` with a client that connects to `celestialtree`.
5. **Removed capabilities**: The node layer no longer carries `TaskMetrics`, nor does it provide legacy interfaces such as `get_snapshot()` / `get_lifecycle_path()` / `remove_observer()`; count statistics are uniformly maintained by `MetricsObserver` based on events.
