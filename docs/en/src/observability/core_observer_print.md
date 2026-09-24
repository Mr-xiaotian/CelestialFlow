# src/celestialflow/observability/core_observer_print.py

> 📅 Last Updated: 2026/09/24

`core_observer_print.py` provides an out-of-the-box console observer, `PrintObserver`. It inherits from `BaseObserver` and outputs task execution progress (start, added, success, fail, duplicate, finish) to standard output via `print`, making it convenient for local debugging and example demonstrations.

## PrintObserver

```python
from threading import Lock

from celestialflow.runtime.util_types import ValueWrapper
from celestialflow.observability.core_observer import BaseObserver


class PrintObserver(BaseObserver):
    def __init__(self, name: str) -> None: ...

    def on_start(self) -> None: ...
    def on_finish(self) -> None: ...
    def on_task_added(self, count: int) -> None: ...
    def on_task_success(self, count: int = 1) -> None: ...
    def on_task_fail(self, count: int = 1) -> None: ...
    def on_task_duplicate(self, count: int = 1) -> None: ...
```

### Constructor Parameters

| Parameter | Type | Description |
|------|------|------|
| `name` | `str` | **Required**; the output prefix, used to distinguish observers of different nodes (in the form `[name] ...`) |

The constructor internally creates a `Lock` and initializes four thread-safe `ValueWrapper` counters:

| Attribute | Type | Description |
|------|------|------|
| `total` | `ValueWrapper` | Total number of injected tasks, incremented by `on_task_added` |
| `succeeded` | `ValueWrapper` | Number of succeeded tasks, incremented by `on_task_success` |
| `failed` | `ValueWrapper` | Number of failed tasks, incremented by `on_task_fail` |
| `duplicated` | `ValueWrapper` | Number of duplicated tasks, incremented by `on_task_duplicate` |
| `name` | `str` | The stored output prefix |

### Callback Behavior

| Callback | Behavior |
|------|------|
| `on_start()` | Prints `[{name}] start total={total}` |
| `on_finish()` | Prints `[{name}] finish total=..., succeeded=..., failed=..., duplicated=...` |
| `on_task_added(count)` | `total += count`, prints `[{name}] total=...(+count)` |
| `on_task_success(count=1)` | `succeeded += count`, prints `[{name}] succeeded=...(+count), total=...` |
| `on_task_fail(count=1)` | `failed += count`, prints `[{name}] failed=...(+count), total=...` |
| `on_task_duplicate(count=1)` | `duplicated += count`, prints `[{name}] duplicated=...(+count), total=...` |

> All counts are read and written through `ValueWrapper` under a shared lock, so they can be safely called in `thread` / `async` execution modes.

## Usage Examples

### Registering Directly to a Node

```python
from celestialflow import TaskExecutor, PrintObserver


def double(x: int) -> int:
    return x * 2


executor = TaskExecutor("Doubler", double, execution_mode="thread", max_workers=4)
executor.add_observer(PrintObserver("Doubler"))
executor.run([1, 2, 3])
# The console output looks like:
# [Doubler] total=3(+3)
# [Doubler] start total=3
# [Doubler] succeeded=1(+1), total=3
# ...
# [Doubler] finish total=3, succeeded=3, failed=0, duplicated=0
```

### Reading the Final Statistics

```python
from celestialflow import TaskExecutor, PrintObserver


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

1. **`name` is a required parameter**: The constructor signature has been changed to `__init__(self, name: str)`; parameterless construction is no longer allowed.
2. **The scope of `total`**: `total` only counts tasks injected via `put_task` / `run`. In graph mode, tasks sent down by upstream nodes do not trigger `on_task_added`, so a non-source node's `total` will be smaller than its actual processing volume.
3. **Callback order**: `run()` injects all tasks first and then starts execution, so `on_task_added` may arrive before `on_start`.
4. **Exception isolation**: Exceptions in callbacks are wrapped by `BaseObserver.__init_subclass__` and handed to `observer_error()`, without interrupting node execution.
