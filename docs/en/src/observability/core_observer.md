# BaseObserver / CallbackObserver

> 📅 Last updated: 2026/05/08

`BaseObserver` is the base class for executor lifecycle observers, defining the event interface that `TaskExecutor` broadcasts during execution. `CallbackObserver` is a lightweight implementation that receives events via callback functions.

## BaseObserver

```python
class BaseObserver:
    def on_start(self, name: str, total: int) -> None: ...
    def on_task_success(self, count: int = 1) -> None: ...
    def on_task_fail(self, count: int = 1) -> None: ...
    def on_task_duplicate(self, count: int = 1) -> None: ...
    def on_tasks_added(self, count: int) -> None: ...
    def on_finish(self) -> None: ...
```

All methods have default empty implementations (not ABC); subclasses override as needed.

### Event Description

| Event | Trigger | Parameters |
|-------|---------|------------|
| `on_start` | Executor begins running | `name`: executor name, `total`: initial task count |
| `on_task_success` | A task succeeds | `count`: number of successes (default 1) |
| `on_task_fail` | A task fails | `count`: number of failures (default 1) |
| `on_task_duplicate` | Duplicate task detected | `count`: number of duplicates (default 1) |
| `on_tasks_added` | New tasks added to queue | `count`: number of new tasks |
| `on_finish` | Executor finishes running | None |

### Usage

```python
from celestialflow import BaseObserver, TaskExecutor

class MyObserver(BaseObserver):
    def on_task_success(self, count=1):
        print(f"Success: {count}")

    def on_task_fail(self, count=1):
        print(f"Failed: {count}")

executor = TaskExecutor("Test", my_func)
executor.add_observer(MyObserver())
executor.start(tasks)
```

### Observer Management

```python
executor.add_observer(observer)     # Register observer
executor.remove_observer(observer)  # Remove observer
```

Internally, the executor broadcasts events to all registered observers via `_notify(method_name, *args, **kwargs)`. When the observer list is empty, there is no overhead (no Null implementation needed).

## CallbackObserver

A lightweight observer that accepts callback functions via keyword arguments, without requiring subclassing.

```python
class CallbackObserver(BaseObserver):
    def __init__(self, **callbacks):
        for name, fn in callbacks.items():
            setattr(self, name, fn)
```

### Usage

```python
from celestialflow import CallbackObserver, TaskExecutor

observer = CallbackObserver(
    on_task_success=lambda count=1: print(f"Success: {count}"),
    on_finish=lambda: print("Done"),
)

executor = TaskExecutor("Test", my_func)
executor.add_observer(observer)
executor.start(tasks)
```

Only override the events you care about; the rest use `BaseObserver`'s default empty implementation.

## Existing Implementations

| Class | Description |
|-------|-------------|
| `TaskProgress` | tqdm-based progress bar display (see `core_progress.md`) |
| `CallbackObserver` | Callback-based observer |
