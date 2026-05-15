# RuntimeFactories

> 📅 Last Updated: 2026/05/15

`runtime/util_factories.py` provides factory functions for runtime objects, used to create corresponding queue objects.

## Design Goals

- Encapsulate queue creation logic
- Simplify conditional logic in upper-layer code

---

## Main Functions

### make_task_in_queue

Creates a task input queue instance.

```python
def make_task_in_queue(
    *,
    queue: Any,
    executor: "TaskExecutor",
) -> TaskInQueue:
    """
    Construct a TaskInQueue instance.

    :param queue: Queue instance
    :param executor: Task executor
    :return: TaskInQueue instance
    """
```

Internal implementation:
```python
return TaskInQueue(
    queue=queue,
    queue_tags=[],
    out_tag=executor.get_tag(),
    log_inlet=executor.log_inlet,
)
```

### make_task_out_queue

Creates a task output queue instance.

```python
def make_task_out_queue(
    *,
    queue: Any,
    executor: "TaskExecutor",
) -> TaskOutQueue:
    """
    Construct a TaskOutQueue instance.

    :param queue: Queue instance
    :param executor: Task executor
    :return: TaskOutQueue instance
    """
```

Internal implementation:
```python
return TaskOutQueue(
    queue_list=[queue],
    queue_tags=[None],
    in_tag=executor.get_tag(),
    log_inlet=executor.log_inlet,
)
```

---

## Usage Example

### Using in TaskExecutor

```python
from celestialflow.runtime.util_factories import (
    make_task_in_queue,
    make_task_out_queue,
)

# Create task input queue
in_queue = make_task_in_queue(queue=queue, executor=executor)

# Create task output queue
out_queue = make_task_out_queue(queue=queue, executor=executor)
```

---

## Notes

1. **Executor Dependency**: `make_task_in_queue` and `make_task_out_queue` require a `TaskExecutor` instance to obtain tags and logger.
