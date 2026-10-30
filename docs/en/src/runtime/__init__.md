# src/celestialflow/runtime/__init__.py

> 📅 Last Updated: 2026/10/30

The Runtime module provides the core infrastructure of the CelestialFlow task runtime, including runtime configuration (`ReportConfig`), task envelopes (Envelope), queues (Queue), and other components.

## Module Overview

The Runtime module is responsible for managing data packaging, queue communication, and runtime configuration types during task execution. It is not responsible for task scheduling itself (scheduling is handled by the Graph module), but rather provides fundamental runtime components for upper layers.

### Publicly Exported Symbols (`__all__`)

```python
from celestialflow.runtime import (
    DEFAULT_REPORT_URL,  # Default report URL constant
    ReportConfig,  # Remote report configuration (frozen configuration object)
    TaskEnvelope,  # Task envelope
    TaskInQueue,  # Task input queue
    TaskOutQueue,  # Task output queue
)
```

`__all__ = ["DEFAULT_REPORT_URL", "ReportConfig", "TaskEnvelope", "TaskInQueue", "TaskOutQueue"]`

> **Note**: Only symbols from `core_*` files are exported. Symbols from `util_*` modules such as `util_constant`, `util_errors`, `util_event`, `util_format`, `util_log_level`, `util_types` are **not** in `runtime/__init__.py`'s `__all__` and must be imported via their full paths (e.g., `from celestialflow.runtime.util_errors import ConfigurationError`, `from celestialflow.runtime.util_log_level import normalize_log_level`).

## File Descriptions

### Core Runtime Components

1. **core_config.py** (`DEFAULT_REPORT_URL`, `ReportConfig`)
   - **Purpose**: Defines the report configuration explicitly passed to the run entry; `report=ReportConfig(...)` enables reporting, `report=None` disables it
   - **Key Features**: Default URL constant, construction-time URL validation (`http`/`https`), normalization that strips trailing `/`
   - See `core_config.md` for details

2. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **Purpose**: Task input/output queues, implementing data transfer between nodes and termination signal merging
   - **Queue types**:
     - `TaskInQueue`: Task input queue, aggregating tasks and termination signals from multiple upstream sources
     - `TaskOutQueue`: Task output queue, broadcasting results to one or more downstream queue channels
   - **Key Features**: Termination signal merging, source name management, dynamic queue channel addition

3. **core_envelope.py** (`TaskEnvelope`)
   - **Purpose**: Task data wrapper, encapsulating the raw task and its ID
   - **Contained Information**: Task data (`_task`), task ID (`_id`)
   - **Key Features**: Data encapsulation and access

### Utility Modules (not exported)

4. **util_errors.py**
   - **Purpose**: Complete exception definition system
   - **Coverage**: Configuration errors, graph structure errors, runtime errors, external service errors, task logic errors
   - See `util_errors.md` for detailed exception list

5. **util_types.py**
   - **Purpose**: Runtime type definitions and data structures
   - **Contained types**: `TerminationSignal`, `TERMINATION_SIGNAL`, `TerminationIdPool`, `NoOpContext`, `ValueWrapper`, `NodeStatus`, `CTreeEvent`, `NodeMetrics`, `MetricsView`

6. **util_event.py**
   - **Purpose**: Event client abstract interface and local implementation
   - **Key Classes**: `EventClient` (Protocol), `LocalEventClient`, `clone_event_client()`

7. **util_constant.py**
   - **Purpose**: Runtime constant definitions (log level mapping table `LEVEL_DICT`)

8. **util_log_level.py**
   - **Purpose**: Log level default value `DEFAULT_LOG_LEVEL` and normalization validation `normalize_log_level()` (for internal use by the run entry points only)

9. **util_format.py**
   - **Purpose**: General formatting utilities (string truncation, table rendering, clustering by value)

> Note: The metrics (Metrics) and reporter (Reporter) related implementations live in the `observer` / `reporter` areas; Runtime only retains the read-only metric snapshot type (`NodeMetrics`) and the view protocol (`MetricsView`) defined in `util_types`, plus the reporting **configuration object** in `core_config` (which contains no reporting execution logic).

## Module Relationships

### Internal Relationships
- `core_queue` uses `TerminationSignal`/`TerminationIdPool` from `util_types`
- `core_queue` uses `DuplicateNodeError`, `UnknownNodeError`, and `TerminationMergeError` from `util_errors`
- `core_config` uses `ConfigurationError` from `util_errors`
- `util_log_level` uses `LEVEL_DICT` from `util_constant` and `ConfigurationError` / `InvalidOptionError` from `util_errors`
- All errors are uniformly handled via `CelestialFlowError` and its subclasses

### External Relationships
- **With Graph Module**: The `report` argument of `TaskGraph.run()` / `run_async()` / `restore_db()` is typed as `ReportConfig`; `TaskGraph` uses `TaskInQueue`/`TaskOutQueue` as inter-node communication pipes
- **With Assembly Module**: `run_graph_resources()` decides whether to assemble remote reporting resources based on whether `report` is `None`
- **With Node Module**: Node objects read and send data using `TaskEnvelope`, `TaskInQueue`/`TaskOutQueue`, and read the read-only metric view via `MetricsView` from `util_types`
- **With Package Root**: `celestialflow/__init__.py` re-exports `ReportConfig` (`from celestialflow import ReportConfig`)

## Usage Examples

The following examples demonstrate the usage of the basic components in the runtime module.

```python
from celestialflow.runtime import (
    DEFAULT_REPORT_URL,
    ReportConfig,
    TaskEnvelope,
    TaskInQueue,
    TaskOutQueue,
)

# 1. ReportConfig: report configuration
config = ReportConfig()  # Use the default URL
print(f"Report URL: {config.url}")  # http://127.0.0.1:5005
print(f"Default URL constant: {DEFAULT_REPORT_URL}")

custom = ReportConfig("https://flow.example.com/api/")
print(f"Normalized: {custom.url}")  # https://flow.example.com/api

# 2. TaskEnvelope: create and access a task envelope
envelope = TaskEnvelope(task={"data": 42}, id=1)
print(f"Task data: {envelope.get_task()}")
print(f"Task ID: {envelope.get_id()}")
```

```python
# 3. TaskInQueue / TaskOutQueue: queue communication
from queue import Queue as ThreadQueue

from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue

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
print(f"Downstream received: {consumer_queue.get().get_task()}")
```

```python
# 4. Pass ReportConfig to a graph run entry
from celestialflow import TaskExecutor, TaskGraph

from celestialflow.runtime import ReportConfig

graph = TaskGraph(name="RuntimeDemo")
graph.set_nodes([TaskExecutor("worker", lambda x: x * 2)])
graph.run({"worker": [1, 2, 3]}, report=ReportConfig())
```

## Best Practices

1. **Reporting switch**: To enable reporting, construct a `ReportConfig` and pass it as `report=`; to disable it, keep the default `None`. There is no implicit reading from `pyproject.toml`
2. **Queue communication**: Properly set `maxsize` to avoid memory overflow
3. **Multiple-source management**: Use `add_source_name()` / `add_queue()` to register upstream/downstream channels without duplication
4. **Termination merging**: `TaskInQueue` merges into a `TerminationIdPool` after collecting all upstream termination signals
