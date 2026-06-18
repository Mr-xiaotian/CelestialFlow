# Runtime Module

> 📅 Last Updated: 2026/06/18

The Runtime module provides the task execution runtime environment for CelestialFlow, including task scheduling, queue management, error handling, performance monitoring, and other core capabilities. It serves as the infrastructure layer for actual task execution.

## Module Overview

The Runtime module is responsible for managing the lifecycle of task execution, from task submission to result return. It provides three execution modes (serial `serial`, thread `thread`, async `async`), robust error handling mechanisms, performance monitoring, and resource management capabilities.

### Publicly Exported Symbols (`__all__`)

```python
from celestialflow.runtime import (
    TaskDispatch,    # Task dispatcher
    TaskEnvelope,    # Task envelope
    TaskInQueue,     # Task input queue
    TaskMetrics,     # Task metrics
    TaskOutQueue,    # Task output queue
)
```

> **Note**: Symbols from utility modules such as `util_constant`, `util_errors`, `util_estimators`, `util_event`, `util_hash`, `util_types` are **not** in `runtime/__init__.py`'s `__all__` and must be imported via their full paths (e.g., `from celestialflow.runtime.util_errors import ConfigurationError`).

## File Descriptions

### Core Runtime Components

1. **core_dispatch.py** (`TaskDispatch`)
   - **Purpose**: Task dispatcher, executing individual tasks in serial, thread, or async mode
   - **Execution modes**:
     - `dispatch_serial`: Execute tasks sequentially
     - `dispatch_thread`: Concurrent task execution based on `ThreadPoolExecutor`
     - `dispatch_async`: Async tasks based on `asyncio` (semaphore-controlled concurrency)
   - **Key Features**: Task retry, duplicate checking, termination signal merging, thread pool lifecycle management

2. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **Purpose**: Task input/output queues, implementing data transfer between nodes and termination signal merging
   - **Queue types**:
     - `TaskInQueue`: Task input queue, aggregating tasks and termination signals from multiple upstream sources
     - `TaskOutQueue`: Task output queue, broadcasting results to one or more downstream queue channels
   - **Key Features**: Termination signal merging, source name management, dynamic queue channel addition

3. **core_envelope.py** (`TaskEnvelope`)
   - **Purpose**: Task data wrapper, encapsulating raw tasks with their hash, ID, and other metadata
   - **Contained Information**: Task data, SHA1 hash value (lazy computation), task ID
   - **Key Features**: Data encapsulation, lazy hash computation

### Monitoring and Metrics

4. **core_metrics.py** (`TaskMetrics`)
   - **Purpose**: Task execution metrics, managing success/failure/duplicate counts and deduplication logic
   - **Key Features**: Thread-safe counters, duplicate task checking, retryable exception configuration, task completion determination

### Utilities and Helper Classes

5. **util_errors.py** (Exception Class Hierarchy)
   - **Purpose**: Complete exception definition system
   - **Coverage**: Configuration errors, graph structure errors, runtime errors, external service errors, task logic errors
   - See `util_errors.md` for detailed exception list

6. **util_types.py**
   - **Purpose**: Runtime type definitions and data structures
   - **Contained types**:
     - **Core Signals**: `TerminationSignal` / `TERMINATION_SIGNAL` — sentinel objects; `TerminationIdPool` — termination signal ID pool
     - **Counters**: `ValueWrapper` — optional-lock integer wrapper; `SumCounter` — multi-`ValueWrapper` cascading sum
     - **Context Manager**: `NoOpContext` — empty context manager for disabling `with` logic
     - **Lifecycle**: `StageStatus` — IntEnum (NOT_STARTED / RUNNING / STOPPED)
     - **Event Constants**: `CTreeEvent` — task/termination event name constants (TASK_INPUT / TASK_SUCCESS / TASK_ERROR / TASK_RETRY_PREFIX / TASK_DUPLICATE / TERMINATION_INPUT / TERMINATION_MERGE)

7. **util_hash.py**
   - **Purpose**: Object hash computation for task deduplication
   - **Key Functions**:
     - `make_hashable()`: Recursively convert list/dict/set to stable hashable structures
     - `object_to_hash()`: Pickle then compute SHA1, return `bytes`

8. **util_estimators.py**
   - **Purpose**: Execution time estimation and progress calculation
   - **Key Features**:
     - `calc_remaining()`: Estimate remaining time based on average
     - `calc_elapsed()`: Accumulate elapsed time by status
     - `calc_global_pending()`: Global pending task count estimation based on DAG topology (conservative)

## Module Relationships

### Internal Relationships
- `TaskDispatch` uses `TaskInQueue`/`TaskOutQueue` to receive tasks and send results
- `TaskEnvelope` is passed through queues, carrying task hash and source information
- `TaskMetrics` monitors `TaskDispatch` execution status
- All errors are uniformly handled via `CelestialFlowError` and its subclasses

### External Relationships
- **With Stage Module**: `TaskDispatch` executes `TaskExecutor` and `TaskStage`
- **With Graph Module**: Provides the execution engine and communication mechanism for `TaskGraph`
- **With Persistence Module**: Supports execution state persistence and logging
- **With Observability Module**: Provides monitoring data and performance metrics

## Architectural Characteristics

### Three-Mode Execution
- `serial`: Sequential execution, suitable for lightweight tasks and debugging
- `thread`: Thread pool concurrency, suitable for I/O-intensive tasks
- `async`: Async coroutines, suitable for network I/O scenarios

### Robustness Design
- Complete error handling chain (retryable / non-retryable)
- Thread-safe counters
- Resource leak prevention (automatic thread pool release)

### Observability
- Comprehensive metric collection (success, failure, duplicate, pending)
- DAG-based global remaining time estimation
- Detailed execution logging

## Usage Examples

The following examples demonstrate how the various runtime module components work together, covering task envelopes, metrics, and queue communication.

```python
from queue import Queue as ThreadQueue
from celestialflow.runtime import TaskEnvelope, TaskMetrics, TaskInQueue, TaskOutQueue

# 1. TaskEnvelope: create and manipulate task envelopes
envelope = TaskEnvelope(task={"data": 42}, id=1)
print(f"Task data: {envelope.get_task()}")
print(f"Task hash: {envelope.get_hash().hex()[:8]}...")
print(f"Task ID: {envelope.get_id()}")
```

```python
# 2. TaskMetrics: metrics tracking
import time

metrics = TaskMetrics(execution_mode="serial", enable_duplicate_check=True)

# Simulate task processing
metrics.add_task_count(5)
metrics.add_success_count(3)
metrics.add_error_count(1)
metrics.add_duplicate_count(1)

# Query counts
print(f"Input: {metrics.get_task_count()}")
print(f"Success: {metrics.get_success_count()}")
print(f"Failed: {metrics.get_error_count()}")
print(f"Duplicate: {metrics.get_duplicate_count()}")
print(f"All complete: {metrics.is_tasks_finished()}")

# Get snapshot dict
counts = metrics.get_counts()
print(f"Pending: {counts['tasks_pending']}")
```

```python
# 3. TaskInQueue / TaskOutQueue: queue communication

# Create input queue (aggregating upstream tasks)
in_queue = TaskInQueue(
    queue=ThreadQueue(),
    source_names=["producer"],
    out_name="processor",
)

# Create output queue (broadcasting to downstream)
out_queue = TaskOutQueue(
    queue_list=[ThreadQueue()],
    target_names=["consumer"],
    in_name="processor",
)

# Upstream produces tasks
envelope_a = TaskEnvelope(task="hello", id=1)
in_queue.put(envelope_a)

# Downstream consumes tasks
retrieved = in_queue.get()
print(f"Dequeued task: {retrieved.get_task()}")

# Output queue broadcasts tasks
out_queue.put(envelope_a)

# Dynamically add output channels
out_queue.add_queue(ThreadQueue(), "another_consumer")
print(f"Output channel count: {len(out_queue.queue_list)}")
```

## Best Practices

1. **I/O-intensive tasks**: Use `thread` mode
2. **Async tasks**: Use `async` mode (function must be a coroutine)
3. **Debugging**: Use `serial` mode for easier single-execution tracing
4. **Critical tasks**: Configure appropriate `max_retries` and `add_retry_exceptions`
5. **Duplicate-sensitive scenarios**: Enable `enable_duplicate_check=True`
