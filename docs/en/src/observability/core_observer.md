# BaseObserver

> 📅 Last Updated: 2026/06/18

`BaseObserver` is the base class for executor lifecycle observers, defining the event interfaces that `TaskExecutor` broadcasts during execution.

> ⚠️ **Deprecated**: Previous documentation included a `CallbackObserver` section. The source implementation of this class has been removed from `core_observer.py` and is no longer available.

## BaseObserver

```python
class BaseObserver:
    def on_start(self, _name: str, _total: int) -> None: ...
    def on_task_success(self, _count: int = 1) -> None: ...
    def on_task_fail(self, _count: int = 1) -> None: ...
    def on_task_duplicate(self, _count: int = 1) -> None: ...
    def on_tasks_added(self, _count: int) -> None: ...
    def on_finish(self) -> None: ...
```

All methods have default empty implementations (not ABC); subclasses override as needed.

### Event Descriptions

| Event | Trigger Timing | Parameters |
|------|----------|------|
| `on_start` | Executor starts running | `_name`: executor full name, `_total`: fixed at 0 (actual task count notified via `on_tasks_added`) |
| `on_task_success` | Single task succeeds | `count`: number of successes (default 1) |
| `on_task_fail` | Single task fails | `count`: number of failures (default 1) |
| `on_task_duplicate` | Duplicate task detected | `count`: number of duplicates (default 1) |
| `on_tasks_added` | New tasks enqueued | `count`: number of new tasks |
| `on_finish` | Executor finishes running | None |

### Usage

```python
from celestialflow import BaseObserver, TaskExecutor

class MyObserver(BaseObserver):
    def on_task_success(self, count=1):
        print(f"Success: {count}")

    def on_task_fail(self, count=1):
        print(f"Fail: {count}")

executor = TaskExecutor("Test", my_func)
executor.add_observer(MyObserver())
executor.start(tasks)
```

### Observer Management

```python
executor.add_observer(observer)     # Register observer
executor.remove_observer(observer)  # Remove observer
```

The executor internally broadcasts events to all registered observers via `_notify(method_name, *args, **kwargs)`. When the observer list is empty, it is equivalent to having no observers (no Null implementation needed).

## Existing Implementations

| Class | Description |
|---|------|
| `TaskProgress` | tqdm-based progress bar display (see `core_progress.md`) |
