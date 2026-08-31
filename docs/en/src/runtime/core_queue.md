# TaskQueue

> 📅 Last Updated: 2026/08/26

The `TaskQueue` module provides `TaskInQueue` and `TaskOutQueue`, two classes used for connecting pipelines between different Stages. They support a multi-producer, multi-consumer model and integrate termination signal merge functionality.

## Overview

- **TaskInQueue**: Task input queue, aggregating tasks from multiple upstream sources and merging termination signals
- **TaskOutQueue**: Task output queue, broadcasting results to one or more downstream queue channels

Both internally use `queue.Queue` (thread-safe queue) as the default backend.

---

## TaskInQueue

Task input queue, used to receive, deduplicate, and merge tasks from multiple upstream sources.

### Initialization

```python
class TaskInQueue:
    def __init__(
        self,
        out_name: str,
        maxsize: int = 0,
    ):
        """
        :param out_name: Unique name of the current node
        :param maxsize: Maximum queue capacity, default 0 (unlimited)
        """
```

The queue is automatically created internally; no external injection is required. Upstream sources are dynamically added via `add_source_name()`.

### Main Methods

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal) -> None:
    """
    Enqueue a task or termination signal.
    """
```

#### get

```python
def get(self) -> TaskEnvelope | TerminationIdPool:
    """
    Dequeue a task or termination signal ID pool.

    Termination signal merging logic:
    - Receive termination signal from "input" → immediately return TerminationIdPool
    - Receive termination signals from all source_names → merge and return
    - Only partial upstream signals received → continue waiting (internal loop retry)
    """
```

#### drain

```python
def drain(self) -> list[TaskEnvelope]:
    """
    Drain all tasks from the queue, returning a list of tasks.
    Records termination signals but does not return TerminationIdPool (only for synchronous environments, e.g., _finish_start).
    """
```

### Helper Methods

```python
def add_source_name(self, name: str) -> None:
    """
    Dynamically add an upstream source name.

    :param name: Upstream node name
    :raises DuplicateNodeError: If the name already exists
    """
```

## TaskOutQueue

Task output queue, used to broadcast tasks to multiple downstream targets.

### Initialization

```python
class TaskOutQueue:
    def __init__(
        self,
        in_name: str,
    ):
        """
        :param in_name: Unique name of the current node, used for logging
        """
```

The output queue list is initially empty, with downstream channels dynamically added via `add_queue()`.

### Main Methods

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal) -> None:
    """Enqueue a task or termination signal to all output channels."""
```

#### put_target

```python
def put_target(self, item: TaskEnvelope | TerminationSignal, name: str) -> None:
    """
    Enqueue to the output channel with the specified name.

    :param name: Downstream Stage name
    """
```

Used for directed dispatch to a specific downstream Stage.

#### get_target_names

```python
def get_target_names(self) -> list[str]:
    """Get the names of all output queue target nodes."""
```

Returns the list of names of all currently registered downstream channels (i.e., the keys of `_queues`).



### Helper Methods

```python
def add_queue(self, queue: Any, name: str) -> None:
    """
    Dynamically add an output queue.

    :param queue: Queue instance
    :param name: Target node name
    :raises DuplicateNodeError: If the name already exists
    """
```

---

## Termination Signal Mechanism

### Signal Flow

```
Upstream node → out_queue.put(TerminationSignal) → queue
                                                    ↓
                                            in_queue.get()
                                                    ↓
                                        termination_dict[source] = id
                                                    ↓
                                        All sources collected? → Yes → merge → TerminationIdPool
                                        Direct input termination?  → Yes → return immediately
                                        Otherwise                 → continue waiting
```

### Merge Rules

`TaskInQueue` waits for termination signals from all `source_names` and merges them into a single `TerminationIdPool`:

1. In `_record_termination`, validate source legitimacy (must be in `source_names ∪ {"input"}`)
2. If `"input"` is present → immediately return `TerminationIdPool(ids=[...])`
3. If `_can_merge_termination()` is True → call `_merge_termination()`
4. Otherwise continue waiting (`_process_item` returns `None`, outer `get` loop continues)

---

## Usage Examples

The following example demonstrates basic usage of `TaskInQueue` and `TaskOutQueue`, including task put/get, termination signal merging, and dynamic channel addition.

```python
from queue import Queue as ThreadQueue
from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue
from celestialflow.runtime.util_types import TerminationSignal

# ===== TaskInQueue Usage Example =====

# Create input queue, specifying current node name and queue capacity
in_queue = TaskInQueue(
    out_name="processor",
    maxsize=0,  # 0 means unlimited
)

# Add upstream source names
in_queue.add_source_name("producer1")
in_queue.add_source_name("producer2")

# Upstream producers put tasks
env1 = TaskEnvelope(task=100, id=1)
env2 = TaskEnvelope(task=200, id=2)
in_queue.put(env1)
in_queue.put(env2)

# Downstream consumer gets tasks
task1 = in_queue.get()
print(f"Received task: {task1.get_task()}, ID: {task1.get_id()}")

# Dynamically add a new upstream source
in_queue.add_source_name("producer3")
print(f"Upstream source count: {len(in_queue.source_names)}")

# ===== TaskOutQueue Usage Example =====

# Create output queue (initially empty, channels are added dynamically via add_queue)
out_queue = TaskOutQueue(
    in_name="processor",
)

# Dynamically add downstream queue channels
consumer_q1 = ThreadQueue()
consumer_q2 = ThreadQueue()
out_queue.add_queue(consumer_q1, "consumer1")
out_queue.add_queue(consumer_q2, "consumer2")

# Broadcast task to all downstream
env3 = TaskEnvelope(task="broadcast_msg", id=3)
out_queue.put(env3)

# Verify both consumers received it
print(f"consumer1 received: {consumer_q1.get().get_task()}")
print(f"consumer2 received: {consumer_q2.get().get_task()}")

# Directed send to a specific downstream
consumer_q3 = ThreadQueue()
out_queue.add_queue(consumer_q3, "consumer3")

env4 = TaskEnvelope(task="targeted_msg", id=4)
out_queue.put_target(env4, "consumer3")
print(f"consumer3 received: {consumer_q3.get().get_task()}")

# ===== Termination Signal Merging =====

# Both upstream send termination signals
in_queue.put(TerminationSignal(_id=1, source="producer1"))
in_queue.put(TerminationSignal(_id=2, source="producer2"))

# get() automatically merges all upstream termination signals and returns TerminationIdPool
result = in_queue.get()
from celestialflow.runtime.util_types import TerminationIdPool

if isinstance(result, TerminationIdPool):
    print(f"Received merged termination signal, containing IDs: {result.ids}")

# ===== drain — flush queue =====
# Create a new queue and put residual tasks
residual_q = TaskInQueue(
    out_name="drain_test",
)
residual_q.add_source_name("src")
residual_q.put(TaskEnvelope(task="leftover", id=5))

# drain flushes all remaining tasks
leftovers = residual_q.drain()
print(f"Residual task count: {len(leftovers)}")
```

## Notes

1. **Multi-channel**: `TaskOutQueue` manages multiple downstream queues
2. **Source management**: Both `add_source_name` and `add_queue` prevent duplicates (`DuplicateNodeError`)
3. **Termination merge**: `_merge_termination` checks for missing sources and raises `TerminationMergeError` if any are absent
4. **drain characteristics**: Only used in synchronous environments (`_finish_start`) to collect unconsumed tasks
