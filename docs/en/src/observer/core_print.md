# src/celestialflow/observer/core_print.py

> 📅 Last Updated: 2026/11/13

`core_print.py` provides an out-of-the-box console observer, `PrintObserver`. It inherits from `Observer`, updates counters by event type in the unified `on_event`, and outputs task execution progress (start, input, success, fail, skip, end) to standard output via `print`, making it convenient for local debugging and example demonstrations.

## PrintObserver

```python
class PrintObserver(Observer):
    def __init__(self, name: str) -> None: ...

    def on_event(self, event: Event) -> None: ...
```

### Constructor Parameters

| Parameter | Type | Description |
|------|------|------|
| `name` | `str` | **Required**; the output prefix, used to distinguish observers of different nodes (in the form `[name] ...`) |

The constructor internally creates a `Lock` and makes four thread-safe `ValueWrapper` counters share it:

| Attribute | Type | Description |
|------|------|------|
| `total` | `ValueWrapper` | Total number of tasks that entered the current node (external injection + upstream delivery), incremented by `TaskInputEvent` |
| `succeeded` | `ValueWrapper` | Number of succeeded tasks, incremented by `TaskSuccessEvent` |
| `failed` | `ValueWrapper` | Number of failed tasks, incremented by `TaskFailEvent` |
| `skipped` | `ValueWrapper` | Number of skipped tasks, incremented by `TaskSkipEvent` |
| `name` | `str` | The stored output prefix |

### Event Handling

`on_event` dispatches with `match`; `TaskRetryEvent`, termination-signal events, graph-level events, etc. all fall into `case _: pass` and are neither counted nor printed.

| Event | Behavior |
|------|------|
| `NodeStartEvent` | Prints `[{name}] start total={total}` |
| `NodeEndEvent` | Prints `[{name}] finish total=..., skipped=..., succeeded=..., failed=...` (does not modify any counter) |
| `TaskInputEvent` | `total += 1`, prints `[{name}] total=...(+1)` |
| `TaskSuccessEvent` | `succeeded += 1`, prints `[{name}] succeeded=...(+1), total=...` |
| `TaskFailEvent` | `failed += 1`, prints `[{name}] failed=...(+1), total=...` |
| `TaskSkipEvent` | `skipped += 1`, prints `[{name}] skipped=...(+1), total=...` |

> All counts are read and written through `ValueWrapper`s sharing the same lock, so they can be safely called in `thread` / `async` execution modes.

## Usage Examples

### Registering Directly to a Node's Observer Hub

```python
from celestialflow.node import TaskExecutor
from celestialflow.observer import PrintObserver


def double(x: int) -> int:
    return x * 2


executor = TaskExecutor("Doubler", double, execution_mode="thread", max_workers=4)
executor.add_observer(PrintObserver("Doubler"))
executor.run([1, 2, 3])
# The console output looks like:
# [Doubler] total=1(+1)
# [Doubler] total=2(+1)
# [Doubler] total=3(+1)
# [Doubler] start total=3
# [Doubler] succeeded=1(+1), total=3
# ...
# [Doubler] finish total=3, skipped=0, succeeded=3, failed=0
```

> In `run()`, the node injects tasks via `put_task()` before starting, so the `total` printed for `NodeStartEvent` already includes the tasks injected before startup; the termination signal emitted by `put_signal()` is a `TerminationInputEvent` and is not counted in `total`.

### Reading the Final Statistics

```python
from celestialflow.node import TaskExecutor
from celestialflow.observer import PrintObserver


def may_fail(x: int) -> int:
    if x % 2 == 0:
        raise ValueError(f"bad {x}")
    return x


executor = TaskExecutor("Odd", may_fail)
observer = PrintObserver("Odd")
executor.add_observer(observer)
executor.run([1, 2, 3, 4])

print(observer.succeeded.get(), observer.failed.get())
```

### Delivering Events Manually

```python
from celestialflow.observer import PrintObserver, TaskInputEvent, TaskSuccessEvent

observer = PrintObserver("Manual")
observer.on_event(
    TaskInputEvent(node="Manual", task="x", task_repr="'x'", input_id=1)
)
observer.on_event(
    TaskSuccessEvent(
        node="Manual",
        task="x",
        task_repr="'x'",
        result="xx",
        result_repr="'xx'",
        elapsed=0.01,
        task_id=1,
        success_id=2,
    )
)
print(observer.total.get(), observer.succeeded.get())  # 1 1
```

## Notes

1. **`name` is a required parameter**: The constructor signature is `__init__(self, name: str)`; the output prefix must be passed in.
2. **The scope of `total`**: `total` counts all tasks entering the current node, **including** both externally injected and upstream-delivered tasks (incremented by `TaskInputEvent`).
3. **Single event entry**: only `on_event` is overridden, with dispatch via `match`; the per-event callbacks such as `on_node_start` / `on_task_success` no longer exist.
4. **Exception isolation**: Exceptions in `on_event` are caught by `ObserverHub` and handed to this observer's `handle_exception`, without interrupting node execution.
