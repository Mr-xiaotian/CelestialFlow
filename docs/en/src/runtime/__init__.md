# Runtime Module

> 📅 Last Updated: 2026/08/12

The Runtime module provides the core infrastructure for CelestialFlow task execution, including task envelopes (`Envelope`), queues (`Queue`), and metrics (`Metrics`).

## Module Overview

The Runtime module is responsible for managing data packaging, queue communication, and metrics tracking during task execution. It is not responsible for task scheduling itself (scheduling is handled by the Stage module), but rather provides fundamental runtime components for upper layers.

### Publicly Exported Symbols (`__all__`)

```python
from celestialflow.runtime import (
    TaskEnvelope,  # Task envelope
    TaskInQueue,  # Task input queue
    TaskMetrics,  # Task metrics
    TaskOutQueue,  # Task output queue
)
```

> **Note**: Symbols from utility modules such as `util_constant`, `util_errors`, `util_estimators`, `util_event`, `util_hash`, `util_types`, `util_config`, `util_format` are **not** in `runtime/__init__.py`'s `__all__` and must be imported via their full paths (e.g., `from celestialflow.runtime.util_errors import ConfigurationError`).

## File Descriptions

### Core Runtime Components

1. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **Purpose**: Task input/output queues, implementing data transfer between nodes and termination signal merging
   - **Queue types**:
     - `TaskInQueue`: Task input queue, aggregating tasks and termination signals from multiple upstream sources
     - `TaskOutQueue`: Task output queue, broadcasting results to one or more downstream queue channels
   - **Key Features**: Termination signal merging, source name management, dynamic queue channel addition

2. **core_envelope.py** (`TaskEnvelope`)
   - **Purpose**: Task data wrapper, encapsulating raw tasks with their hash, ID, and other metadata
   - **Contained Information**: Task data, SHA1 hash value (lazy computation), task ID
   - **Key Features**: Data encapsulation, lazy hash computation, fallback for unhashable tasks

3. **core_metrics.py** (`TaskMetrics`)
   - **Purpose**: Task execution metrics, managing success/failure/duplicate counts and deduplication logic
   - **Key Features**: Thread-safe counters, duplicate task checking, retryable exception configuration, task completion determination

### Utility Modules

4. **util_errors.py**
   - **Purpose**: Complete exception definition system
   - **Coverage**: Configuration errors, graph structure errors, runtime errors, external service errors, task logic errors
   - See `util_errors.md` for detailed exception list

5. **util_types.py**
   - **Purpose**: Runtime type definitions and data structures
   - **Contained types**: `TerminationSignal`, `TerminationIdPool`, `ValueWrapper`, `SumCounter`, `NoOpContext`, `StageStatus`, `CTreeEvent`

6. **util_hash.py**
   - **Purpose**: Object hash computation for task deduplication
   - **Key Functions**: `make_hashable()`, `object_to_hash()`

7. **util_estimators.py**
   - **Purpose**: Execution time estimation and progress calculation
   - **Key Functions**: `calc_remaining()`, `calc_elapsed()`, `format_avg_time()`

8. **util_event.py**
   - **Purpose**: Event client abstract interface and local implementation
   - **Key Classes**: `EventClient` (Protocol), `LocalEventClient`, `clone_event_client()`

9. **util_constant.py**
   - **Purpose**: Runtime constant definitions (e.g., log level mapping)

10. **util_config.py**
    - **Purpose**: Runtime configuration loading (e.g., reading log level from `pyproject.toml`)

11. **util_format.py**
    - **Purpose**: General formatting utilities (string truncation, table rendering, time formatting, etc.)

## Module Relationships

### Internal Relationships
- `TaskEnvelope` uses `util_hash` to compute task hashes
- `TaskInQueue`/`TaskOutQueue` use `TerminationSignal`/`TerminationIdPool` from `util_types`
- `TaskMetrics` uses `ValueWrapper`/`SumCounter` from `util_types`
- All errors are uniformly handled via `CelestialFlowError` and its subclasses

### External Relationships
- **With Stage Module**: Stage uses `TaskInQueue`/`TaskOutQueue` as inter-node communication pipes
- **With Graph Module**: Provides queue and metrics infrastructure for `TaskGraph`

## Usage Examples

The following examples demonstrate the usage of basic components in the runtime module.

```python
from celestialflow.runtime import TaskEnvelope, TaskMetrics, TaskInQueue, TaskOutQueue

# 1. TaskEnvelope: create and manipulate task envelopes
envelope = TaskEnvelope(task={"data": 42}, id=1)
print(f"Task data: {envelope.get_task()}")
print(f"Task hash: {envelope.get_hash().hex()[:8]}...")
print(f"Task ID: {envelope.get_id()}")
```

```python
# 2. TaskMetrics: metrics tracking
metrics = TaskMetrics(enable_duplicate_check=True)

# Simulate task processing
metrics.add_task_count(5)
metrics.add_success_count(3)
metrics.add_fail_count(1)
metrics.add_duplicate_count(1)

# Query counts
print(f"Input: {metrics.get_task_count()}")
print(f"Success: {metrics.get_success_count()}")
print(f"Failed: {metrics.get_fail_count()}")
print(f"Duplicate: {metrics.get_duplicate_count()}")
print(f"All complete: {metrics.is_tasks_finished()}")

# Get snapshot dict
counts = metrics.get_counts()
print(f"Pending: {counts['tasks_pending']}")
```

```python
# 3. TaskInQueue / TaskOutQueue: queue communication
from queue import Queue as ThreadQueue

# Create input queue
in_queue = TaskInQueue(out_name="processor")
in_queue.add_source_name("producer")

# Create output queue
out_queue = TaskOutQueue(in_name="processor")
consumer_queue = ThreadQueue()
out_queue.add_queue(consumer_queue, "consumer")

# Produce tasks
envelope_a = TaskEnvelope(task="hello", id=1)
in_queue.put(envelope_a)
out_queue.put(envelope_a)

# Consume tasks
retrieved = in_queue.get()
print(f"Dequeued task: {retrieved.get_task()}")
```

## Best Practices

1. **Critical tasks**: Configure appropriate `set_retry_exceptions`
2. **Duplicate-sensitive scenarios**: Enable `enable_duplicate_check=True`
3. **Queue communication**: Properly set `maxsize` to avoid memory overflow
