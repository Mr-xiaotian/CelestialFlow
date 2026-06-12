# Runtime Module

> 📅 Last Updated: 2026/06/11

The Runtime module provides the task execution runtime environment for CelestialFlow, including task scheduling, queue management, error handling, performance monitoring, and other core capabilities. It serves as the infrastructure layer for actual task execution.

## Module Overview

The Runtime module manages the lifecycle of task execution, from task submission to result return. It provides three execution modes (serial `serial`, thread `thread`, async `async`), robust error handling mechanisms, performance monitoring, and resource management capabilities.

### Public Exports (`__all__`)

```python
from celestialflow.runtime import (
    TaskDispatch,    # Task dispatcher
    TaskEnvelope,    # Task envelope
    TaskInQueue,     # Task input queue
    TaskMetrics,     # Task metrics
    TaskOutQueue,    # Task output queue
)
```

> **Note**: Symbols from utility modules such as `util_constant`, `util_errors`, `util_estimators`, `util_hash`, `util_types` are **not** in `runtime/__init__.py`'s `__all__` and must be imported via their full path (e.g., `from celestialflow.runtime.util_errors import ConfigurationError`).

## File Descriptions

### Core Runtime Components

1. **core_dispatch.py** (`TaskDispatch`)
   - **Purpose**: Task dispatcher, executes individual tasks in serial, thread, or async mode
   - **Execution Modes**:
     - `dispatch_serial`: Execute tasks sequentially
     - `dispatch_thread`: Execute tasks concurrently via `ThreadPoolExecutor`
     - `dispatch_async`: Async tasks via `asyncio` (semaphore-controlled concurrency)
   - **Key Features**: Task retry, dedup check, termination signal merge, thread pool lifecycle management

2. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **Purpose**: Task input/output queues, enabling data transfer between nodes and termination signal merge
   - **Queue Types**:
     - `TaskInQueue`: Task input queue, aggregates tasks and termination signals from multiple upstream sources
     - `TaskOutQueue`: Task output queue, broadcasts results to one or more downstream queue channels
   - **Key Features**: Termination signal merge, source name management, dynamic queue channel addition

3. **core_envelope.py** (`TaskEnvelope`)
   - **Purpose**: Task data wrapper, encapsulates the original task along with its hash, ID, source, and other metadata
   - **Stored Information**: Task data, SHA1 hash (lazy evaluation), task ID, source identifier, predecessor task reference
   - **Key Features**: Data encapsulation, lazy hash evaluation, task ID and predecessor task reference

### Monitoring and Metrics

4. **core_metrics.py** (`TaskMetrics`)
   - **Purpose**: Task execution metrics, manages success/failure/duplicate counts and dedup logic
   - **Key Features**: Thread-safe counters, duplicate task checking, retry-exception configuration, task completion judgment

### Utilities

5. **util_errors.py** (Exception class hierarchy)
   - **Purpose**: Complete exception definition system
   - **Coverage**: Configuration errors, graph structure errors, runtime errors, external service errors, task logic errors
   - See `util_errors.md` for the detailed exception list

6. **util_types.py**
   - **Purpose**: Runtime type definitions and data structures
   - **Included Types**:
     - **Core Signals**: `TerminationSignal` / `TERMINATION_SIGNAL` — sentinel objects; `TerminationIdPool` — termination signal ID pool
     - **Counters**: `ValueWrapper` — integer wrapper with optional lock; `SumCounter` — multi-`ValueWrapper` cascade accumulator
     - **Context Managers**: `NoOpContext` — empty context manager, for disabling `with` logic
     - **Lifecycle**: `StageStatus` — IntEnum (NOT_STARTED / RUNNING / STOPPED)
     - **Event Constants**: `CTreeEvent` — task/termination event name constants (TASK_INPUT / TASK_SUCCESS / TASK_ERROR / TASK_RETRY_PREFIX / TASK_DUPLICATE / TERMINATION_INPUT / TERMINATION_MERGE)
     - **Error Records**: `PersistedErrorRecord` — persistent error record frozen dataclass (supports grouping)
     - **Visualization**: `STAGE_STYLE` — CelestialTree node label style

7. **util_hash.py**
   - **Purpose**: Object hash computation, used for task dedup
   - **Key Functions**:
     - `make_hashable()`: Recursively convert list/dict/set to stable hashable structures
     - `object_to_hash()`: Pickle then compute SHA1, returns `bytes`

8. **util_estimators.py**
   - **Purpose**: Execution time estimation and progress calculation
   - **Key Functions**:
     - `calc_remaining()`: Estimate remaining time based on mean values
     - `calc_elapsed()`: Accumulate elapsed time by status
     - `calc_global_pending()`: Global pending task count estimation based on DAG topology (conservative)

## Module Relationships

### Internal Relationships
- `TaskDispatch` uses `TaskInQueue`/`TaskOutQueue` to fetch tasks and send results
- `TaskEnvelope` is passed through queues, carrying task hash and source information
- `TaskMetrics` monitors the execution status of `TaskDispatch`
- All errors are uniformly handled via `CelestialFlowError` and its subclasses

### External Relationships
- **With Stage Module**: `TaskDispatch` executes `TaskExecutor` and `TaskStage`
- **With Graph Module**: Provides execution engine and communication mechanisms for `TaskGraph`
- **With Persistence Module**: Supports execution state persistence and logging
- **With Observability Module**: Provides monitoring data and performance metrics

## Architecture Characteristics

### Three-Mode Execution
- `serial`: Sequential execution, suitable for lightweight tasks and debugging
- `thread`: Thread pool concurrency, suitable for I/O-bound tasks
- `async`: Async coroutines, suitable for network I/O scenarios

### Robustness Design
- Complete error handling chain (retry / non-retry)
- Thread-safe counters
- Resource leak prevention (auto-release of thread pool)

### Observability
- Comprehensive metric collection (success, failure, duplicate, pending)
- DAG-based global remaining time estimation
- Detailed execution logging

## Usage Examples

The following examples demonstrate how the Runtime module components work together, covering task envelopes, metrics, and queue communication.

```python
from queue import Queue as ThreadQueue
from celestialflow.runtime import TaskEnvelope, TaskMetrics, TaskInQueue, TaskOutQueue
from celestialflow.persistence import LogInlet

# 1. TaskEnvelope: Create and manipulate task envelopes
envelope = TaskEnvelope(task={"data": 42}, id=1, source="input")
print(f"Task data: {envelope.get_task()}")
print(f"Task hash: {envelope.get_hash().hex()[:8]}...")
print(f"Task ID: {envelope.get_id()}")

# Generate new envelope on retry via emit_retry_envelope
print(f"Task ID: {envelope.get_id()}")
```

```python
# 2. TaskMetrics: Metrics
import time

metrics = TaskMetrics(execution_mode="serial", enable_duplicate_check=True)

# Simulate task processing
metrics.add_task_count(5)
metrics.add_success_count(3)
metrics.add_error_count(1)
metrics.add_duplicate_count(1)

# Query individual counts
print(f"Input: {metrics.get_task_count()}")
print(f"Success: {metrics.get_success_count()}")
print(f"Failed: {metrics.get_error_count()}")
print(f"Duplicate: {metrics.get_duplicate_count()}")
print(f"All finished: {metrics.is_tasks_finished()}")

# Get snapshot dict
counts = metrics.get_counts()
print(f"Pending: {counts['tasks_pending']}")
```

```python
# 3. TaskInQueue / TaskOutQueue: Queue communication

# Create input queue (aggregates upstream tasks)
in_queue = TaskInQueue(
    queue=ThreadQueue(),
    source_names=["producer"],
    out_name="processor",
)

# Create output queue (broadcasts to downstream)
out_queue = TaskOutQueue(
    queue_list=[ThreadQueue()],
    target_names=["consumer"],
    in_name="processor",
)

# Upstream produces tasks
envelope_a = TaskEnvelope(task="hello", id=1, source="producer")
in_queue.put(envelope_a)

# Downstream consumes tasks
retrieved = in_queue.get()
print(f"Dequeued task: {retrieved.get_task()}")

# Output queue broadcasts tasks
out_queue.put(envelope_a)

# Dynamically add output channel
out_queue.add_queue(ThreadQueue(), "another_consumer")
print(f"Output channel count: {len(out_queue.queue_list)}")
```

## Best Practices

1. **I/O-bound Tasks**: Use `thread` mode
2. **Async Tasks**: Use `async` mode (functions must be coroutines)
3. **Debugging**: Use `serial` mode for easy single-execution tracing
4. **Critical Tasks**: Configure appropriate `max_retries` and `add_retry_exceptions`
5. **Dup-Sensitive Scenarios**: Enable `enable_duplicate_check=True`
