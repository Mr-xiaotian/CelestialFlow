# BaseObserver / CallbackObserver

> 📅 Last Updated: 2026/05/08

`BaseObserver` is the base class for executor lifecycle observers, defining the event interfaces that `TaskExecutor` broadcasts during execution. `CallbackObserver` is a lightweight implementation that receives events through callback functions.

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

All methods have empty default implementations (not ABC); subclasses override as needed.

### Event Description

| Event | Trigger Timing | Parameters |
|-------|---------------|------------|
| `on_start` | Executor starts running | `name`: executor name, `total`: initial total task count |
| `on_task_success` | A single task succeeds | `count`: number of successes (default 1) |
| `on_task_fail` | A single task fails | `count`: number of failures (default 1) |
| `on_task_duplicate` | A duplicate task is detected | `count`: number of duplicates (default 1) |
| `on_tasks_added` | New tasks added to the queue | `count`: number of new tasks |
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
executor.add_observer(observer)     # Register an observer
executor.remove_observer(observer)  # Remove an observer
```

The executor internally broadcasts events to all registered observers via `_notify(method_name, *args, **kwargs)`. When the observer list is empty, it is equivalent to having no observers (no Null implementation needed).

## CallbackObserver

A lightweight observer that receives events through callback functions passed as keyword arguments, without the need to define a subclass.

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
| `TaskProgress` | Progress bar display based on tqdm (see `core_progress.md`) |
| `CallbackObserver` | Callback function-based observer |
