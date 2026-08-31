# BaseObserver

> 📅 Last Updated: 2026/08/26

`BaseObserver` is the base class for executor lifecycle observers, defining the event interfaces that `TaskExecutor` broadcasts during execution.

## BaseObserver

```python
class BaseObserver:
    def on_start(self, _name: str, _total: int) -> None: ...
    def on_task_success(self, _count: int = 1) -> None: ...
    def on_task_fail(self, _count: int = 1) -> None: ...
    def on_task_duplicate(self, _count: int = 1) -> None: ...
    def on_tasks_added(self, _count: int) -> None: ...
    def on_finish(self) -> None: ...

    def observer_error(self, method_name: str, exception: Exception) -> None: ...
```

All methods have default empty implementations (not ABC); subclasses override as needed.

### Event Descriptions

| Event | Trigger Timing | Parameters |
|-------|----------------|------------|
| `on_start` | Executor starts running | `_name`: executor full name, `_total`: fixed at 0 (actual task count is notified via `on_tasks_added`) |
| `on_task_success` | Single task succeeds | `count`: number of successes (default 1) |
| `on_task_fail` | Single task fails | `count`: number of failures (default 1) |
| `on_task_duplicate` | Duplicate task detected | `count`: number of duplicates (default 1) |
| `on_tasks_added` | New tasks enqueued | `count`: number of new tasks |
| `on_finish` | Executor finishes running | None |
| `observer_error` | When an observer callback throws an exception | `method_name`: name of the exception-raising callback, `exception`: the caught exception |

### Automatic Exception Wrapping Mechanism

`BaseObserver` uses `__init_subclass__` to automatically wrap all overridden callback methods (`on_start`, `on_task_success`, `on_task_fail`, `on_task_duplicate`, `on_tasks_added`, `on_finish`) when a subclass is created:

- The wrapper catches any `Exception` raised by the callback, calls `observer_error(method_name, exception)`, then returns `None`; the exception does not escape into the framework.
- Note: `observer_error` itself is not wrapped; if a subclass overrides it and throws, the exception will propagate outward as usual.

### Trigger Mechanism

Events are not dispatched via a unified `_notify()`, but invoked directly by the framework at specific points:

- `TaskMetrics.on_start(name, total)` → broadcasts `on_start` (called by `TaskExecutor._prepare_start()`, `total` is always `0`)
- `TaskMetrics.add_task_count(count)` → broadcasts `on_tasks_added`
- `TaskMetrics.add_success_count(count)` / `add_fail_count(count)` / `add_duplicate_count(count)` → broadcast the corresponding callbacks
- `TaskMetrics.on_finish()` → broadcasts `on_finish`

Observers are registered via `executor.add_observer(observer)` (stored internally in `TaskMetrics._observers`). When the observer list is empty, the broadcast loop is a no-op.

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
executor.run([1, 2, 3])
```

### Observer Management

```python
executor.add_observer(observer)  # Register observer
executor.remove_observer(observer)  # Remove observer
```

## Existing Implementations

| Class | Description |
|-------|-------------|
| (No built-in implementation) | Users can inherit `BaseObserver` and implement custom observers as needed |
