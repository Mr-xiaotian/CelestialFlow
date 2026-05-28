# Runtime Module

> 📅 Last Updated: 2026/05/28

The Runtime module provides the task execution runtime environment for CelestialFlow, including core functionalities such as task scheduling, queue management, error handling, and performance monitoring. It serves as the infrastructure layer for actual task execution.

## Module Overview

The Runtime module manages the lifecycle of task execution, from task submission to result retrieval. It provides three execution modes (serial `serial`, thread `thread`, async `async`), robust error handling mechanisms, performance monitoring, and resource management features.

## File Description

### Core Runtime Components

1. **core_dispatch.py** (`TaskDispatch`)
   - **Purpose**: Task scheduler that executes individual tasks in serial, thread, or async modes
   - **Execution Modes**:
     - `dispatch_serial`: Executes tasks sequentially
     - `dispatch_thread`: Concurrent execution based on `ThreadPoolExecutor`
     - `dispatch_async`: Async tasks based on `asyncio` (semaphore-controlled concurrency)
   - **Key Features**: Task retry, duplicate checking, termination signal merging, thread pool lifecycle management

2. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **Purpose**: Task input/output queues for data transfer and termination signal merging between nodes
   - **Queue Types**:
     - `TaskInQueue`: Task input queue, aggregates tasks and termination signals from multiple upstream sources
     - `TaskOutQueue`: Task output queue, broadcasts results to one or more downstream queue channels
   - **Key Features**: Termination signal merging, source name management, logging, dynamic queue channel addition

3. **core_envelope.py** (`TaskEnvelope`)
   - **Purpose**: Task data wrapper encapsulating the original task along with its hash, ID, source, and other metadata
   - **Contents**: Task data, SHA1 hash value (lazy computation), task ID, source identifier, predecessor task reference
   - **Key Features**: Data encapsulation, lazy hash computation, task ID mutation (retry scenarios)

### Monitoring and Metrics

4. **core_metrics.py** (`TaskMetrics`)
   - **Purpose**: Task execution metrics, managing success/failure/duplicate counts and deduplication logic
   - **Key Features**: Thread-safe counters, duplicate task checking, retryable exception configuration, task completion detection

### Tools and Utilities

5. **util_errors.py** (Exception Class Hierarchy)
   - **Purpose**: Complete exception definition system
   - **Coverage**: Configuration exceptions, graph structure exceptions, runtime exceptions, external service exceptions, task logic exceptions
   - See `util_errors.md` for detailed exception list

6. **util_types.py**
   - **Purpose**: Runtime type definitions and data structures
   - **Included Types**:
     - **Core Signals**: `TerminationSignal` / `TERMINATION_SIGNAL` — sentinel objects; `TerminationIdPool` — termination signal ID pool
     - **Counters**: `ValueWrapper` — integer wrapper with optional thread lock; `SumCounter` — cascading accumulation from multiple `ValueWrapper` instances
     - **Context Manager**: `NoOpContext` — empty context manager for disabling `with` logic
     - **Lifecycle**: `StageStatus` — IntEnum (NOT_STARTED / RUNNING / STOPPED)
     - **Event Constants**: `CTreeEvent` — task/termination event name constants (TASK_INPUT / TASK_SUCCESS / TASK_ERROR / TASK_RETRY_PREFIX / TASK_DUPLICATE / TERMINATION_INPUT / TERMINATION_MERGE)
     - **Error Record**: `PersistedErrorRecord` — persistent error record frozen dataclass (supports grouping)
     - **Visualization**: `STAGE_STYLE` — CelestialTree node label style

7. **util_hash.py**
   - **Purpose**: Object hash computation for task deduplication
   - **Key Functions**:
     - `make_hashable()`: Recursively converts list/dict/set to stable hashable structures
     - `object_to_hash()`: Pickles then computes SHA1, returns `bytes`

8. **util_estimators.py**
   - **Purpose**: Execution time estimation and progress calculation
   - **Key Functions**:
     - `calc_remaining()`: Estimates remaining time based on averages
     - `calc_elapsed()`: Accumulates elapsed time by status
     - `calc_global_remain_equal_pred()`: Global remaining time estimation based on DAG topology (conservative)

## Module Relationships

### Internal Relationships
- `TaskDispatch` uses `TaskInQueue`/`TaskOutQueue` to get tasks and send results
- `TaskEnvelope` is passed through queues, carrying task hash and source information
- `TaskMetrics` monitors the execution state of `TaskDispatch`
- All errors are handled uniformly through `CelestialFlowError` and its subclasses

### External Relationships
- **With Stage Module**: `TaskDispatch` executes `TaskExecutor` and `TaskStage`
- **With Graph Module**: Provides execution engine and communication mechanism for `TaskGraph`
- **With Persistence Module**: Supports persistence of execution state and logging
- **With Observability Module**: Provides monitoring data and performance metrics

## Architecture Features

### Three-Mode Execution
- `serial`: Sequential execution, suitable for lightweight tasks and debugging
- `thread`: Thread pool concurrency, suitable for I/O-intensive tasks
- `async`: Async coroutines, suitable for network I/O scenarios

### Robustness Design
- Complete error handling chain (retryable / non-retryable)
- Thread-safe counters
- Resource leak prevention (automatic thread pool release)

### Observability
- Comprehensive metrics collection (success, failure, duplicate, pending)
- DAG-based global remaining time estimation
- Detailed execution logs

## Usage Examples

The following examples demonstrate collaborative usage of runtime module components, covering task envelopes, metrics, and queue communication.

```python
from queue import Queue as ThreadQueue
from celestialflow.runtime import TaskEnvelope, TaskMetrics, TaskInQueue, TaskOutQueue
from celestialflow.persistence import LogInlet

# 1. TaskEnvelope: Create and operate on task envelopes
envelope = TaskEnvelope(task={"data": 42}, id=1, source="input")
print(f"Task data: {envelope.get_task()}")
print(f"Task hash: {envelope.get_hash().hex()[:8]}...")
print(f"Task ID: {envelope.get_id()}")

# Change ID on retry
envelope.change_id(100)
print(f"Changed ID: {envelope.get_id()}")
```

```python
# 2. TaskMetrics: Metrics statistics
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
print(f"All finished: {metrics.is_tasks_finished()}")

# Get snapshot dict
counts = metrics.get_counts()
print(f"Pending: {counts['tasks_pending']}")
```

```python
# 3. TaskInQueue / TaskOutQueue: Queue communication

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

1. **I/O-Intensive Tasks**: Use `thread` mode
2. **Async Tasks**: Use `async` mode (function must be a coroutine)
3. **Debugging**: Use `serial` mode for easier single-execution tracing
4. **Critical Tasks**: Configure appropriate `max_retries` and `add_retry_exceptions`
5. **Duplicate-Sensitive Scenarios**: Enable `enable_duplicate_check=True`
