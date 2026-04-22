# TaskQueue

The `TaskQueue` module provides `TaskInQueue` and `TaskOutQueue` classes, which serve as pipelines connecting different stages. They support multi-producer, multi-consumer models and integrate logging and monitoring capabilities.

## Overview

- **TaskInQueue**: Task input queue for receiving tasks from upstream
- **TaskOutQueue**: Task output queue for sending tasks to downstream

Both support multiple backends: `queue.Queue` (Thread), `multiprocessing.Queue` (Process), `asyncio.Queue` (Async).

---

## TaskInQueue

Task input queue for receiving and merging tasks from multiple upstream sources.

### Initialization

```python
class TaskInQueue:
    def __init__(
        self,
        queue: ThreadQueue | MPQueue | AsyncQueue,
        queue_tags: list[str],
        out_tag: str,
        log_inlet: "LogInlet",
    ):
        """
        Initialize the task input queue.

        :param queue: Queue object
        :param queue_tags: List of upstream queue tags
        :param out_tag: Current node tag
        :param log_inlet: Logger
        """
```

### Main Methods

#### put / put_async

```python
def put(self, item: TaskEnvelope | TerminationSignal):
    """
    Enqueue a task or termination signal.

    :param item: Task or termination signal to enqueue
    """

async def put_async(self, item: TaskEnvelope | TerminationSignal):
    """
    Asynchronously enqueue a task or termination signal.
    """
```

#### get / get_async

```python
def get(self) -> TaskEnvelope | TerminationIdPool:
    """
    Dequeue a task or termination signal pool.

    :return: Task envelope or termination signal ID pool
    """

async def get_async(self) -> TaskEnvelope | TerminationIdPool:
    """
    Asynchronously dequeue a task or termination signal pool.
    """
```

**Termination signal merging logic**:
- When a termination signal from `"input"` is received, it is returned immediately
- When a termination signal from the current node tag (`out_tag`) is received, it is returned immediately
- When termination signals from all `queue_tags` are received, they are merged and returned

#### drain

```python
def drain(self) -> list[TaskEnvelope]:
    """
    Drain all tasks from the queue and return a task list.
    Records termination signal status but does not return TerminationIdPool.

    :return: List containing all tasks
    """
```

### Helper Methods

```python
def add_source_tag(self, tag: str):
    """
    Add an upstream queue tag.

    :param tag: Upstream queue tag
    :raises ValueError: If the tag already exists
    """

def reset(self):
    """
    Reset the task input queue state (clears termination signal records).
    """
```

---

## TaskOutQueue

Task output queue for sending tasks to multiple downstream targets.

### Initialization

```python
class TaskOutQueue:
    def __init__(
        self,
        queue_list: list[ThreadQueue] | list[MPQueue] | list[AsyncQueue],
        queue_tags: list[str],
        in_tag: str,
        log_inlet: "LogInlet",
    ):
        """
        Initialize the task output queue.

        :param queue_list: List of output queues
        :param queue_tags: List of queue tags
        :param in_tag: Current node tag
        :param log_inlet: Logger
        :raises ValueError: If the queue list and tag list have different lengths
        """
```

### Main Methods

#### put / put_async

```python
def put(self, item: TaskEnvelope | TerminationSignal):
    """
    Enqueue a task or termination signal to all output channels.
    """

async def put_async(self, item: TaskEnvelope | TerminationSignal):
    """
    Asynchronously enqueue a task or termination signal to all output channels.
    """
```

#### put_target

```python
def put_target(self, item: TaskEnvelope | TerminationSignal, tag: str):
    """
    Enqueue a task or termination signal to the output channel with the specified tag.

    :param item: Task or termination signal to enqueue
    :param tag: Output queue tag
    """
```

Commonly used for targeted routing in `TaskRouter`.

#### put_channel / put_channel_async

```python
def put_channel(self, item: TaskEnvelope | TerminationSignal, idx: int):
    """
    Enqueue a task or termination signal to the output channel at the specified index.

    :param item: Task or termination signal to enqueue
    :param idx: Output channel index
    """

async def put_channel_async(self, item: TaskEnvelope | TerminationSignal, idx: int):
    """
    Asynchronously enqueue a task or termination signal to the output channel at the specified index.
    """
```

### Helper Methods

```python
def add_queue(self, queue: ThreadQueue | MPQueue | AsyncQueue, tag: str):
    """
    Add an output queue to the queue list.

    :param queue: Output queue to add
    :param tag: Queue tag
    :raises ValueError: If the tag already exists
    """
```

---

## Termination Signal Mechanism

### Signal Flow

```
Upstream node ──TaskOutQueue──> Queue ──TaskInQueue──> Current node
    │                              │
    └── TerminationSignal ──────> termination_dict
                                        │
                                        v
                               Merged into TerminationIdPool
```

### Merging Rules

`TaskInQueue` waits for termination signals from all `queue_tags`, then merges them into a single `TerminationIdPool`:

1. When a termination signal is received, it is recorded in `termination_dict`
2. Checks whether all upstream sources have sent termination signals
3. If all are received, merges them into a `TerminationIdPool` and returns it
4. Otherwise, continues waiting

Special handling:
- Termination signals with the `"input"` tag are returned immediately
- Termination signals with the current node tag (`out_tag`) are returned immediately

---

## Usage Example

### Using in TaskGraph

```python
from celestialflow.runtime import TaskInQueue, TaskOutQueue
from multiprocessing import Queue as MPQueue

# Input queue
in_queue = TaskInQueue(
    queue=MPQueue(),
    queue_tags=["upstream_stage"],
    out_tag="current_stage",
    log_inlet=log_inlet,
)

# Output queue
out_queue = TaskOutQueue(
    queue_list=[MPQueue()],
    queue_tags=["downstream_stage"],
    in_tag="current_stage",
    log_inlet=log_inlet,
)
```

### Dynamically Adding Downstream

```python
# Add a new downstream queue
out_queue.add_queue(new_queue, "new_downstream")
```

### Handling Termination Signals

```python
# Get a task
item = in_queue.get()

if isinstance(item, TaskEnvelope):
    # Process the task
    result = process(item.task)
    out_queue.put(TaskEnvelope.wrap(result, result_id))
elif isinstance(item, TerminationIdPool):
    # All upstream sources have terminated, send termination signal downstream
    out_queue.put(TerminationSignal())
```

---

## Notes

1. **Multi-Channel**: A single `TaskOutQueue` can manage multiple downstream queues
2. **Logging**: All enqueue/dequeue operations are logged
3. **Async Support**: Provides async methods such as `put_async` and `get_async`
4. **Thread Safety**: Internally uses queue implementations that support multi-thread/multi-process access
5. **Termination Merging**: Properly handles merging of termination signals from multiple upstream sources
