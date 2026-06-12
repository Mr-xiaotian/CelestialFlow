# TaskGraph

> 📅 Last Updated: 2026/06/11

`TaskGraph` is CelestialFlow's core scheduler, responsible for managing a set of `TaskStage` nodes' dependencies, execution flow, resource allocation, and lifecycle.

> Note: `TaskGraph` is a single-use object. After a single `start_graph()` completes, the current instance is not guaranteed to be safely reset and restarted. If you need to re-execute the same workflow, create a new `TaskGraph` and associated `TaskStage` instances.

## Key Data Structures

`TaskGraph` internally uses `stage_dict: dict[str, TaskStage]` to maintain a Stage mapping for all nodes. Each Stage automatically creates corresponding `TaskInQueue` and `TaskOutQueue` instances during initialization; queues are connected during the `_build_resources()` phase.

## Initialization

```python
class TaskGraph:
    def __init__(self, name: str, schedule_mode: str = "eager", log_level: str = "INFO"):
        ...
```

### Parameters

- **name**: Task graph name (required)
- **schedule_mode**: Scheduling mode
  - `eager` (default): All nodes launched concurrently at once; dependencies flow automatically through queues
  - `staged`: Layer-by-layer execution (DAG only). Launches layers sequentially in topological order, starting the next layer only after all nodes in the current layer have completed
- **log_level**: Log level

## Graph Construction

### set_stages

```python
def set_stages(self, stages: list[TaskStage]) -> None:
    """
    Add nodes to the task graph. Creates TaskInQueue and TaskOutQueue for each node.

    :param stages: List of nodes
    :raises DuplicateNodeError: If node names are duplicated
    """
```

### connect

```python
def connect(self, from_stages: list[TaskStage], to_stages: list[TaskStage]) -> None:
    """
    Establish a hyperedge: every node in from_stages connects to every node in to_stages.
    Operates on the out_edges / in_edges dictionaries; actual queue connections are made in _build_resources().
    """
```

## Configuration Methods

### set_reporter

```python
def set_reporter(self, is_report: bool = False, host: str = "127.0.0.1", port: int = 5000) -> None:
    """Configure the reporter (上报器) for pushing status to Web UI."""
```

### set_ctree

```python
def set_ctree(self, use_ctree: bool = False, host: str = "127.0.0.1",
              http_port: int = 7777, grpc_port: int = 7778,
              transport: str = "grpc") -> None:
    """
    Configure the CelestialTree client. Validates connection health when enabled.
    :raises CelestialTreeConnectionError: If connection fails
    """
```

### set_graph_mode

```python
def set_graph_mode(self, stage_mode: str, execution_mode: str) -> None:
    """
    Batch-set stage_mode and execution_mode for all nodes.
    Triggers _build_analysis() to rebuild analysis data.
    """
```

## Starting Execution

### start_graph

```python
def start_graph(self, init_tasks_dict: Mapping[str, Iterable[Any]],
                put_termination_signal: bool = True) -> None:
    """
    Start the task graph. Flow:
    1. _build_resources() — build queue connections and counter bindings
    2. _build_analysis() — analyze graph structure (source nodes, levels, DAG detection)
    3. Start spout, inlet, reporter
    4. put_stage_queue() — inject initial tasks and termination signals
    5. _execute_stages() — execute all nodes
    6. _finalize_nodes() — finalize (ensure threads end, collect unconsumed tasks)
    7. Release resources
    """
```

Lifecycle constraints:

- `TaskGraph` internally establishes runtime queue connections, predecessor bindings, thread references, and state snapshots during the startup process.
- These runtime resources are designed to serve a single complete execution and are not guaranteed to be safely cleared and reused after the run ends.
- If you need to rerun the same topology, it is recommended to re-instantiate the graph object and node objects, rather than calling `start_graph()` again on the same instance.

```python
graph = TaskGraph(name="MyGraph", schedule_mode="eager")
graph.set_stages(stages=[stage_a, stage_b])
graph.connect([stage_a], [stage_b])
graph.start_graph({stage_a.get_name(): [1, 2, 3, 4, 5]})
```

### _execute_stages

```python
def _execute_stages(self) -> None:
    """Eager mode: launch all nodes at once; staged mode: launch layer by layer."""
```

### _execute_stage

```python
def _execute_stage(self, stage: TaskStage) -> None:
    """
    Execute a single node:
    - thread mode: call stage.start_stage() in a new thread
    - serial mode: call stage.start_stage() synchronously in the current thread
    """
```

## Dynamic Task Injection

### put_stage_queue

```python
def put_stage_queue(self, tasks_dict: Mapping[str, Iterable[Any]],
                    put_termination_signal: bool = True) -> None:
    """
    Dynamically inject tasks into nodes. Supports:
    - Regular tasks → auto-wrapped as TaskEnvelope
    - TerminationSignal objects → directly injected as termination signals
    - put_termination_signal=True → auto-inject termination signals to all source nodes
    """
```

## Runtime Monitoring

### collect_runtime_snapshot

```python
def collect_runtime_snapshot(self) -> None:
    """
    Collect runtime snapshots for all nodes, updating status_dict.
    Computes per-node processed / pending / elapsed / remaining and global remaining time.
    """
```

### _snapshot_one_stage

Collects a snapshot for a single node, returning a dict with the following fields:

| Field | Type | Description |
|------|------|------|
| `name` | `str` | Node name |
| `func_name` | `str` | Function name |
| `execution_mode` | `str` | Execution mode |
| `stage_mode` | `str` | Node mode |
| `status` | `StageStatus` | Running state |
| `tasks_input` | `int` | Input task count |
| `tasks_succeeded` | `int` | Success count |
| `tasks_failed` | `int` | Failure count |
| `tasks_duplicated` | `int` | Duplicate count |
| `tasks_processed` | `int` | Processed count |
| `tasks_pending` | `int` | Pending count |
| `total_tasks_pending` | `int` | Global estimated pending count |
| `elapsed_time` | `float` | Elapsed time |
| `remaining_time` | `float` | Estimated remaining time |
| `total_remaining_time` | `float` | Global estimated remaining time |
| `task_avg_time` | `str` | Average time (formatted) |
| `start_time` | `float` | Start timestamp |

## Query Interface

| Method | Return Type | Description |
|------|---------|------|
| `get_status_snapshot()` | `dict` | Status snapshot with unified timestamp |
| `get_graph_analysis()` | `dict` | Graph analysis info (isDAG, scheduleMode, layersDict, className) |
| `get_structure_graph()` | `dict` | Graph structure in JSON format (nodes + edges + source_nodes) |
| `get_structure_list()` | `list[str]` | Formatted tree text with borders |
| `get_networkx_graph()` | `DiGraph` | networkx directed graph instance |
| `get_fail_by_stage_dict()` | `dict[str, list]` | Failed tasks grouped by node |
| `get_fail_by_error_dict()` | `dict[tuple, list]` | Failed tasks grouped by error type (key is `(error_type, error_message)` tuple) |
| `get_total_error_num()` | `int` | Total error count |
| `get_fallback_path()` | `str` | Absolute path to the failure task JSONL file |
| `get_source_stages()` | `list[TaskStage]` | List of source nodes |
| `get_stage_input_trace(stage_name)` | `str` | Node input dependency tree (requires ctree enabled) |

### get_fail_by_error_dict Description

```python
def get_fail_by_error_dict(self) -> dict[tuple[str, ...], list[Any]]:
    """Return grouped by (error_type, error_message)."""
```

## Lifecycle Diagram

```mermaid
flowchart TD
    INIT[__init__] -->|set_schedule_mode / set_ctree / set_reporter| ENV[_init_env]
    ENV --> STATE[_init_state]
    ENV --> SPOUT[_init_spout: LogSpout + FailSpout]
    ENV --> INLET[_init_inlet: LogInlet + FailInlet]
    STATE --> BUILD[set_stages + connect]
    BUILD --> START[start_graph]
    START --> RESOURCES[_build_resources: Queue connections & counter bindings]
    START --> ANALYSIS[_build_analysis: Graph analysis]
    START -->|Inject initial tasks| PUT[put_stage_queue]
    START --> EXEC[_execute_stages]
    EXEC -->|eager| ALL[Launch all nodes at once]
    EXEC -->|staged| LAYER[Launch layer by layer]
    ALL --> FINALIZE[_finalize_nodes: Collect unconsumed tasks]
    LAYER --> FINALIZE
    FINALIZE --> RELEASE[_release_resources]
    RELEASE --> END[Graph execution complete]

    START -->|Monitor| SNAPSHOT[collect_runtime_snapshot]
    SNAPSHOT --> SUMMARY[get_graph_summary]
    SNAPSHOT --> STATUS[get_status_snapshot]
```

## Scheduling Modes in Detail

### Eager Mode

```
All nodes start_stage simultaneously → data flows through queues → stop when termination signal arrives
```

- Maximizes parallelism
- Suitable for most scenarios
- Recommended for cyclic graphs

### Staged Mode

```
Layer 0: [Node A, Node B] → all join → Layer 1: [Node C, Node D] → ...
```

- Layer-by-layer execution; next layer starts only after current layer fully completes
- Only applicable to DAGs
- Suitable for debugging, performance profiling, resource control

## Notes for Non-DAG Graphs

For cyclic graphs, if `put_termination_signal=True`, `start_graph` will emit a `RuntimeWarning`. Termination signals may cause some nodes to exit prematurely before receiving upstream data; it is recommended to:

```python
graph.start_graph({"source": tasks}, put_termination_signal=False)
# Later manually inject TerminationSignal via Web UI or put_stage_queue
```

## Unconsumed Task Handling

In `_finalize_nodes()`, all remaining tasks are collected via `in_queue.drain()`, marked as `UnconsumedError`, and persisted to a JSONL file via `fail_inlet`.
