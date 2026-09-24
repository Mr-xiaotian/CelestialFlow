# src/celestialflow/observability/core_observer.py

> 📅 Last Updated: 2026/09/24

`BaseObserver` is the base class for executor lifecycle observers, defining the event interfaces that `BaseTaskNode` (and its subclasses `TaskExecutor` / `TaskSplitter` / `TaskRouter`) broadcasts during execution.

## BaseObserver

```python
class BaseObserver:
    def on_start(self) -> None: ...
    def on_task_success(self, _count: int = 1) -> None: ...
    def on_task_fail(self, _count: int = 1) -> None: ...
    def on_task_duplicate(self, _count: int = 1) -> None: ...
    def on_task_added(self, _count: int) -> None: ...
    def on_finish(self) -> None: ...

    def observer_error(self, method_name: str, exception: Exception) -> None: ...
```

All methods have default empty implementations (not ABC); subclasses override as needed.

### Event Descriptions

| Event | Trigger Timing | Parameters |
|-------|----------------|------------|
| `on_start` | Executor starts running | None (the total task count is notified via `on_task_added`) |
| `on_task_success` | Task succeeds | `count`: number of successes (default 1) |
| `on_task_fail` | Task fails | `count`: number of failures (default 1) |
| `on_task_duplicate` | Duplicate task count detected | `count`: number of duplicates (default 1) |
| `on_task_added` | New task added to the queue via `put_task` | `count`: number of new tasks |
| `on_finish` | Executor finishes running | None |
| `observer_error` | When an observer callback throws an exception | `method_name`: name of the exception-raising callback, `exception`: the caught exception |

### Automatic Exception Wrapping Mechanism

`BaseObserver` uses `__init_subclass__` to automatically wrap all overridden callback methods (`on_start`, `on_task_success`, `on_task_fail`, `on_task_duplicate`, `on_task_added`, `on_finish`) when a subclass is created:

- The wrapper catches any `Exception` raised by the callback, calls `observer_error(method_name, exception)`, then returns `None`; the exception does not escape into the framework.
- Note: `observer_error` itself is not wrapped; if a subclass overrides it and throws, the exception will propagate outward as usual.

### Trigger Mechanism

Events are not dispatched via a unified `_notify()`, but invoked directly by the framework at specific points:

- `TaskMetrics.on_start()` → broadcasts `on_start` (called by `BaseTaskNode._prepare_start()`)
- `TaskMetrics.add_external_input_count(count)` → broadcasts `on_task_added`
- `TaskMetrics.add_success_count(count)` / `add_fail_count(count)` / `add_duplicate_count(count)` → broadcast the corresponding callbacks
- `TaskMetrics.on_finish()` → broadcasts `on_finish`

Observers are registered via `node.add_observer(observer)` (stored internally in `TaskMetrics._observers`). When the observer list is empty, the broadcast loop is a no-op.

### Usage

```python
from celestialflow import BaseObserver, TaskExecutor


class MyObserver(BaseObserver):
    def on_task_success(self, count=1):
        print(f"Success: {count}")

    def on_task_fail(self, count=1):
        print(f"Fail: {count}")


executor = TaskExecutor("Test", lambda x: x * 2)
executor.add_observer(MyObserver())
executor.run([1, 2, 3])
```

### Observer Management

```python
node.add_observer(observer)  # Register observer
node.remove_observer(observer)  # Remove observer
```

## Existing Implementations

| Class | File | Description |
|---|---------|------|
| `PrintObserver` | `core_observer_print.py` | A `print`-based console observer; requires a `name` prefix at construction; maintains `total` / `succeeded` / `failed` / `duplicated` counts |

> Users can also inherit `BaseObserver` as needed to implement custom observers. See `docs/en/src/observability/core_observer_print.md`.
