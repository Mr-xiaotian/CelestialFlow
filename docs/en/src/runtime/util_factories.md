# RuntimeFactories

`runtime/util_factories.py` provides factory functions for runtime objects, creating the appropriate queues, counters, and other objects based on the execution mode.

## Design Goals

- Unify the underlying resource creation logic across serial/thread/process/async modes
- Encapsulate implementation differences between modes
- Simplify conditional logic in upper-layer code

---

## Main Functions

### make_counter

Creates a counter, selecting the appropriate implementation based on the execution mode.

```python
def make_counter(
    mode: str, *, lock: LockType | None = None, init: int = 0
) -> ValueWrapper:
    """
    Returns a counter.

    :param mode: Execution mode ('serial', 'thread', 'process', 'async')
    :param lock: Optional lock object (used in thread mode)
    :param init: Initial value
    :return: ValueWrapper or MPValue
    """
```

Return types:
- `process` mode: `MPValue("i", init)`
- `thread` mode: `ValueWrapper(init, lock=lock or Lock())`
- `serial`/`async` mode: `ValueWrapper(init)`

### make_queue_backend

Returns a queue class/constructor for creating single-channel queues.

```python
def make_queue_backend(mode: str):
    """
    Returns a queue class.

    :param mode: Execution mode
    :return: Queue class
    """
```

Return types:
- `async` mode: `AsyncQueue`
- `thread`/`serial`/`process` mode: `ThreadQueue`

> Note: `process` mode also uses `ThreadQueue` because the queue is used internally within a node and does not cross process boundaries.

### make_task_in_queue

Creates a task input queue instance.

```python
def make_task_in_queue(
    *,
    mode: str,
    executor: "TaskExecutor",
) -> TaskInQueue:
    """
    Constructs a TaskInQueue instance.

    :param mode: Execution mode
    :param executor: Task executor
    :return: TaskInQueue instance
    """
```

Internal implementation:
```python
Q = make_queue_backend(mode)
return TaskInQueue(
    queue=Q(),
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
    mode: str,
    executor: "TaskExecutor",
) -> TaskOutQueue:
    """
    Constructs a TaskOutQueue instance.

    :param mode: Execution mode
    :param executor: Task executor
    :return: TaskOutQueue instance
    """
```

Internal implementation:
```python
Q = make_queue_backend(mode)
return TaskOutQueue(
    queue_list=[Q()],
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
    make_counter,
    make_queue_backend,
    make_task_in_queue,
    make_task_out_queue,
)

# Create a counter
counter = make_counter("thread", init=0)

# Create a queue backend
QueueClass = make_queue_backend("async")
queue = QueueClass()

# Create a task input queue
in_queue = make_task_in_queue(mode="thread", executor=executor)

# Create a task output queue
out_queue = make_task_out_queue(mode="thread", executor=executor)
```

### Creating Queues Directly

```python
# Get queue classes
ThreadQueue = make_queue_backend("thread")
AsyncQueue = make_queue_backend("async")

# Create instances
sync_queue = ThreadQueue()
async_queue = AsyncQueue()
```

---

## Mode Reference Table

| Mode | Counter | Queue Backend |
|------|---------|---------------|
| `serial` | `ValueWrapper` | `ThreadQueue` |
| `thread` | `ValueWrapper` + Lock | `ThreadQueue` |
| `process` | `MPValue` | `ThreadQueue` |
| `async` | `ValueWrapper` | `AsyncQueue` |

---

## Notes

1. **Process Mode Queue**: In the current implementation, `process` mode uses `ThreadQueue` because the queue is used internally within a node. If cross-process communication is needed, it should be changed to `MPQueue`.

2. **Lock Passing**: The `lock` parameter of `make_counter` is used to reuse lock objects in thread mode.

3. **Executor Dependency**: `make_task_in_queue` and `make_task_out_queue` require a `TaskExecutor` instance to obtain tags and loggers.
