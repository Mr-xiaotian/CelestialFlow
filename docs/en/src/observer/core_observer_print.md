# src/celestialflow/observer/core_observer_print.py

> 📅 Last Updated: 2026/10/09

`core_observer_print.py` provides an out-of-the-box console observer, `PrintObserver`. It inherits from `Observer` and outputs task execution progress (start, input, success, fail, skip, end) to standard output via `print`, making it convenient for local debugging and example demonstrations.

## PrintObserver

```python
class PrintObserver(Observer):
    def __init__(self, name: str) -> None: ...

    def on_node_start(self, event: NodeStartEvent) -> None: ...
    def on_node_end(self, event: NodeEndEvent) -> None: ...
    def on_task_input(self, event: TaskInputEvent) -> None: ...
    def on_task_success(self, event: TaskSuccessEvent) -> None: ...
    def on_task_fail(self, event: TaskFailEvent) -> None: ...
    def on_task_skip(self, event: TaskSkipEvent) -> None: ...
```

### Constructor Parameters

| Parameter | Type | Description |
|------|------|------|
| `name` | `str` | **Required**; the output prefix, used to distinguish observers of different nodes (in the form `[name] ...`) |

The constructor internally creates a `Lock` and initializes four thread-safe `ValueWrapper` counters:

| Attribute | Type | Description |
|------|------|------|
| `total` | `ValueWrapper` | Total number of tasks that entered the current node (external injection + upstream delivery), incremented by `on_task_input` |
| `succeeded` | `ValueWrapper` | Number of succeeded tasks, incremented by `on_task_success` |
| `failed` | `ValueWrapper` | Number of failed tasks, incremented by `on_task_fail` |
| `skipped` | `ValueWrapper` | Number of skipped tasks, incremented by `on_task_skip` |
| `name` | `str` | The stored output prefix |

### Callback Behavior

| Callback | Behavior |
|------|------|
| `on_node_start(event)` | Prints `[{name}] start total={total}` |
| `on_node_end(event)` | `total += ...`, prints `[{name}] finish total=..., skipped=..., succeeded=..., failed=...` |
| `on_task_input(event)` | `total += 1`, prints `[{name}] total=...(+1)` |
| `on_task_success(event)` | `succeeded += 1`, prints `[{name}] succeeded=...(+1), total=...` |
| `on_task_fail(event)` | `failed += 1`, prints `[{name}] failed=...(+1), total=...` |
| `on_task_skip(event)` | `skipped += 1`, prints `[{name}] skipped=...(+1), total=...` |

> All counts are read and written through `ValueWrapper` under a shared lock, so they can be safely called in `thread` / `async` execution modes.

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
# [Doubler] total=3(+1)
# [Doubler] start total=3
# [Doubler] succeeded=1(+1), total=3
# ...
# [Doubler] finish total=3, skipped=0, succeeded=3, failed=0
```

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

## Notes

1. **`name` is a required parameter**: The constructor signature is `__init__(self, name: str)`; the output prefix must be passed in.
2. **The scope of `total`**: `total` counts all tasks entering the current node, **including** both externally injected and upstream-delivered tasks (incremented by `on_task_input`).
3. **Callback parameters are event objects**: Unlike legacy observers based on basic `count` parameters, all callbacks receive the corresponding read-only event `dataclass` from `core_event.py`.
4. **Exception isolation**: Exceptions in callbacks are caught by `ObserverHub` and handed to this observer's `handle_exception`, without interrupting node execution.