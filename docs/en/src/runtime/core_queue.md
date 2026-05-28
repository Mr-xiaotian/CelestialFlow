# TaskQueue

> 📅 Last Updated: 2026/05/28

The `TaskQueue` module provides two classes, `TaskInQueue` and `TaskOutQueue`, used as pipelines connecting different Stages. They support multi-producer, multi-consumer models and integrate logging and termination signal merging capabilities.

## Overview

- **TaskInQueue**: Task input queue, aggregates tasks and termination signals from multiple upstream sources
- **TaskOutQueue**: Task output queue, broadcasts results to one or more downstream queue channels

Both support multiple queue backends: `queue.Queue` (Thread), `asyncio.Queue` (Async).

---

## TaskInQueue

Task input queue for receiving, deduplicating, and merging tasks from multiple upstream sources.

### Initialization

```python
class TaskInQueue:
    def __init__(
        self,
        queue: Any,
        source_names: list[str],
        out_name: str,
    ):
        """
        :param queue: Queue object
        :param source_names: List of upstream node names
        :param out_name: Unique name of the current node
        """
```

### Main Methods

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal) -> None:
    """
    Enqueue a task or termination signal. Records enqueue log.
    """
```

#### get

```python
def get(self) -> TaskEnvelope | TerminationIdPool:
    """
    Dequeue a task or termination signal ID pool.

    Termination signal merging logic:
    - Termination signal from "input" → immediately return TerminationIdPool
    - Termination signals from all source_names received → merge and return
    - Only partial upstream signals received → continue waiting (return None, loop retries internally)
    """
```

#### drain

```python
def drain(self) -> list[TaskEnvelope]:
    """
    Drain all tasks from the queue, returning a list of tasks.
    Records termination signals but does not return TerminationIdPool (only used in sync environments such as _finalize_nodes).
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

Task output queue for broadcasting tasks to multiple downstream nodes.

### Initialization

```python
class TaskOutQueue:
    def __init__(
        self,
        queue_list: list[Any],
        target_names: list[str],
        in_name: str,
    ):
        """
        :param queue_list: List of output queues
        :param target_names: List of downstream node names (must match queue_list length)
        :param in_name: Unique name of the current node
        :raises ConfigurationError: If the two list lengths do not match
        """
```

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

Used for targeted distribution to a specific downstream Stage.

#### put_channel

```python
def put_channel(self, item: TaskEnvelope | TerminationSignal, idx: int) -> None:
    """
    Enqueue to the output channel at the specified index.

    :param idx: Output channel index
    """
```

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
Upstream node → out_queue.put(TerminationSignal) → Queue
                                                        ↓
                                                in_queue.get()
                                                        ↓
                                            termination_dict[source] = id
                                                        ↓
                                            All sources gathered? → Yes → merge → TerminationIdPool
                                            Input directly terminated? → Yes → return immediately
                                            Otherwise → continue waiting
```

### Merging Rules

`TaskInQueue` waits for termination signals from all `source_names`, merging them into a single `TerminationIdPool`:

1. In `_record_termination`, validate source legitimacy (must be in `source_names ∪ {"input"}`)
2. If `"input"` exists → immediately return `TerminationIdPool(ids=[...])`
3. If `_can_merge_termination()` is True → call `_merge_termination()`
4. Otherwise continue waiting (`_deal_get_item` returns `None`, outer `get` loop continues)

---

## Usage Examples

The following examples demonstrate basic usage of `TaskInQueue` and `TaskOutQueue`, including task put/get, termination signal merging, and dynamic channel addition.

```python
from queue import Queue as ThreadQueue
from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue
from celestialflow.runtime.util_types import TerminationSignal

# ===== TaskInQueue Usage =====

# Create input queue, aggregating tasks from two upstreams ("producer1", "producer2")
in_queue = TaskInQueue(
    queue=ThreadQueue(),
    source_names=["producer1", "producer2"],
    out_name="processor",
)

# Upstream producers put tasks
env1 = TaskEnvelope(task=100, id=1, source="producer1")
env2 = TaskEnvelope(task=200, id=2, source="producer2")
in_queue.put(env1)
in_queue.put(env2)

# Downstream consumer gets tasks
task1 = in_queue.get()
print(f"Received task: {task1.get_task()}, source: {task1.source}")

# Dynamically add a new upstream source
in_queue.add_source_name("producer3")
print(f"Upstream source count: {len(in_queue.source_names)}")

# ===== TaskOutQueue Usage =====

# Create output queue, broadcasting to two downstreams
consumer_q1 = ThreadQueue()
consumer_q2 = ThreadQueue()

out_queue = TaskOutQueue(
    queue_list=[consumer_q1, consumer_q2],
    target_names=["consumer1", "consumer2"],
    in_name="processor",
)

# Broadcast task to all downstreams
env3 = TaskEnvelope(task="broadcast_msg", id=3, source="processor")
out_queue.put(env3)

# Verify both consumers received
print(f"consumer1 received: {consumer_q1.get().get_task()}")
print(f"consumer2 received: {consumer_q2.get().get_task()}")

# Targeted send to specific downstream
consumer_q3 = ThreadQueue()
out_queue.add_queue(consumer_q3, "consumer3")

env4 = TaskEnvelope(task="targeted_msg", id=4, source="processor")
out_queue.put_target(env4, "consumer3")
print(f"consumer3 received: {consumer_q3.get().get_task()}")

# ===== Termination Signal Merging =====

# Both upstreams send termination signals
in_queue.put(TerminationSignal(_id=1, source="producer1"))
in_queue.put(TerminationSignal(_id=2, source="producer2"))

# get() automatically merges all upstream termination signals and returns TerminationIdPool
result = in_queue.get()
from celestialflow.runtime.util_types import TerminationIdPool
if isinstance(result, TerminationIdPool):
    print(f"Received merged termination signal with IDs: {result.ids}")

# ===== drain to clear queue =====
# Create a new queue and put residual tasks
residual_q = TaskInQueue(
    queue=ThreadQueue(),
    source_names=["src"],
    out_name="drain_test",
)
residual_q.put(TaskEnvelope(task="leftover", id=5, source="src"))

# drain clears all remaining tasks
leftovers = residual_q.drain()
print(f"Residual task count: {len(leftovers)}")
```

## Notes

1. **Multi-Channel**: `TaskOutQueue` manages multiple downstream queues
2. **Logging**: All put/get operations are logged; exceptions log `put_item_error`
3. **Source Management**: `add_source_name` and `add_queue` both prevent duplicates (`DuplicateNodeError`)
4. **Termination Merging**: `_merge_termination` checks for missing sources, raising `TerminationMergeError` if any are missing
5. **drain Characteristics**: Only used in sync environments (`_finalize_nodes`) for collecting unconsumed tasks
