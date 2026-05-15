# TaskProgress

> 📅 Last Updated: 2026/05/08

`TaskProgress` inherits from `BaseObserver` and provides task progress visualization based on `tqdm`.

## Features

- **Dynamic Updates**: Supports dynamically increasing the total task count via `on_tasks_added`, adapting to streaming tasks or task splitting scenarios.
- **Lifecycle Management**: Creates the progress bar on `on_start` and closes it on `on_finish`.
- **Event-Driven**: Updates progress via `on_task_success/fail/duplicate`.

## Interface

```python
class TaskProgress(BaseObserver):
    def on_start(self, name: str, total: int) -> None:
        # Create tqdm progress bar
    def on_task_success(self, count: int = 1) -> None:
        # Update progress
    def on_task_fail(self, count: int = 1) -> None:
        # Update progress
    def on_task_duplicate(self, count: int = 1) -> None:
        # Update progress
    def on_tasks_added(self, count: int) -> None:
        # Increase total task count and refresh
    def on_finish(self) -> None:
        # Close progress bar
```

## Usage

```python
from celestialflow import TaskExecutor, TaskProgress

executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)
```

When a progress bar is not needed, simply do not add the observer -- no Null implementation is required.
