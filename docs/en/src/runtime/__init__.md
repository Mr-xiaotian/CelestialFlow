# src/celestialflow/runtime/__init__.py

> 📅 Last Updated: 2026/10/09

The Runtime module provides the core infrastructure for CelestialFlow task execution, including task envelopes (Envelope), queues (Queue), and other components.

## Module Overview

The Runtime module is responsible for managing data packaging and queue communication during task execution. It is not responsible for task scheduling itself (scheduling is handled by the Graph module), but rather provides fundamental runtime components for upper layers.

### Publicly Exported Symbols (`__all__`)

```python
from celestialflow.runtime import (
    TaskEnvelope,  # Task envelope
    TaskInQueue,  # Task input queue
    TaskOutQueue,  # Task output queue
)
```

`__all__ = ["TaskEnvelope", "TaskInQueue", "TaskOutQueue"]`

> **Note**: Symbols from utility modules such as `util_constant`, `util_errors`, `util_event`, `util_types`, `util_config`, `util_format` are **not** in `runtime/__init__.py`'s `__all__` and must be imported via their full paths (e.g., `from celestialflow.runtime.util_errors import ConfigurationError`).

## File Descriptions

### Core Runtime Components

1. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **Purpose**: Task input/output queues, implementing data transfer between nodes and termination signal merging
   - **Queue types**:
     - `TaskInQueue`: Task input queue, aggregating tasks and termination signals from multiple upstream sources
     - `TaskOutQueue`: Task output queue, broadcasting results to one or more downstream queue channels
   - **Key Features**: Termination signal merging, source name management, dynamic queue channel addition

2. **core_envelope.py** (`TaskEnvelope`)
   - **Purpose**: Task data wrapper, encapsulating the raw task and its ID
   - **Contained Information**: Task data (`_task`), task ID (`_id`)
   - **Key Features**: Data encapsulation and access

### Utility Modules

3. **util_errors.py**
   - **Purpose**: Complete exception definition system
   - **Coverage**: Configuration errors, graph structure errors, runtime errors, external service errors, task logic errors
   - See `util_errors.md` for detailed exception list

4. **util_types.py**
   - **Purpose**: Runtime type definitions and data structures
   - **Contained types**: `TerminationSignal`, `TERMINATION_SIGNAL`, `TerminationIdPool`, `NoOpContext`, `ValueWrapper`, `NodeStatus`, `CTreeEvent`, `NodeMetrics`, `MetricsView`

5. **util_event.py**
   - **Purpose**: Event client abstract interface and local implementation
   - **Key Classes**: `EventClient` (Protocol), `LocalEventClient`, `clone_event_client()`

6. **util_constant.py**
   - **Purpose**: Runtime constant definitions (e.g., log level mapping)

7. **util_config.py**
   - **Purpose**: Runtime configuration loading (e.g., reading log level, report URL, and report switch from `pyproject.toml`)

8. **util_format.py**
   - **Purpose**: General formatting utilities (string truncation, table rendering, clustering by value)

> Note: The metrics (Metrics) and reporter (Reporter) related implementations have been migrated from the Runtime module to the `observer` / `observability` areas; Runtime only retains the read-only metric snapshot types (`NodeMetrics`) and the view protocol (`MetricsView`) defined in `util_types`.

## Module Relationships

### Internal Relationships
- `TaskInQueue`/`TaskOutQueue` use `TerminationSignal`/`TerminationIdPool` from `util_types`
- `TaskInQueue` internally uses `DuplicateNodeError`, `UnknownNodeError`, and `TerminationMergeError` from `util_errors`
- All errors are uniformly handled via `CelestialFlowError` and its subclasses

### External Relationships
- **With Graph Module**: `TaskGraph` manages various task nodes, using `TaskInQueue`/`TaskOutQueue` as inter-node communication pipes
- **With Node Module**: Node objects read and send data using `TaskEnvelope`, `TaskInQueue`/`TaskOutQueue`, and read the read-only metric view via `MetricsView` from `util_types`

## Usage Examples

The following examples demonstrate the usage of basic components in the runtime module.

```python
from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue

# 1. TaskEnvelope: create and access a task envelope
envelope = TaskEnvelope(task={"data": 42}, id=1)
print(f"Task data: {envelope.get_task()}")
print(f"Task ID: {envelope.get_id()}")
```

```python
# 2. TaskInQueue / TaskOutQueue: queue communication
from queue import Queue as ThreadQueue

# Create an input queue
in_queue = TaskInQueue(out_name="processor")
in_queue.add_source_name("producer")

# Create an output queue
out_queue = TaskOutQueue(in_name="processor")
consumer_queue = ThreadQueue()
out_queue.add_queue("consumer", consumer_queue)

# Produce tasks
envelope_a = TaskEnvelope(task="hello", id=1)
in_queue.put(envelope_a)
out_queue.put(envelope_a)

# Consume tasks
retrieved = in_queue.get()
print(f"Dequeued task: {retrieved.get_task()}")
```

## Best Practices

1. **Queue communication**: Properly set `maxsize` to avoid memory overflow
2. **Multiple-source management**: Use `add_source_name()` / `add_queue()` to register upstream/downstream channels without duplication
3. **Termination merging**: `TaskInQueue` merges into a `TerminationIdPool` after collecting all upstream termination signals