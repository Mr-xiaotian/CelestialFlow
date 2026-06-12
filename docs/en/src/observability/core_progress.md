# TaskProgress

> 📅 Last Updated: 2026/06/11

`TaskProgress` inherits `BaseObserver` and provides visual display of task progress based on `tqdm`.

## Features

- **Dynamic Updates**: Supports dynamically increasing total task count via `on_tasks_added`, adapting to streaming tasks or task splitting scenarios.
- **Lifecycle Management**: Creates a progress bar on `on_start` and closes it on `on_finish`.
- **Event-Driven**: Updates progress via `on_task_success/fail/duplicate`.

## Interface

```python
class TaskProgress(BaseObserver):
    _bar: tqdm[Any]

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

When a progress bar is not needed, simply don't add the observer; no Null implementation is required.

## Usage Examples

### TaskProgress Used with TaskExecutor

```python
from celestialflow import TaskExecutor, TaskProgress


def slow_task(n: int) -> int:
    """Simulate a time-consuming task"""
    import time
    time.sleep(0.05)
    return n * n


# 1. Create executor, thread mode
executor = TaskExecutor(
    "Square Calculator",
    slow_task,
    execution_mode="thread",
    max_workers=10,
)

# 2. Add progress bar observer
executor.add_observer(TaskProgress())

# 3. Start executor to process 100 tasks
executor.start(range(100))
print("All tasks completed!")
```

### Progress Bar with Dynamically Added Tasks

When tasks may dynamically increase during execution (e.g., task splitting scenarios), `TaskProgress` automatically expands the progress bar total:

```python
from celestialflow import TaskExecutor, TaskProgress


def dynamic_task(n: int) -> list[int]:
    """Dynamically generate new tasks based on input value"""
    if n % 10 == 0:
        return [n + 1, n + 2]
    return [n]


executor = TaskExecutor("Dynamic Task", dynamic_task, execution_mode="thread")

progress = TaskProgress()
executor.add_observer(progress)

# Initial 20 tasks, dynamically increased during execution
executor.start(range(20))
```
