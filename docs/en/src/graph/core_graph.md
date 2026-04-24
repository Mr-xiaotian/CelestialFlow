# TaskGraph

> 📅 Last updated: 2026/04/24

`TaskGraph` is the core scheduler of CelestialFlow, responsible for managing the dependency relationships, execution flow, resource allocation, and lifecycle of a group of `TaskStage` nodes.

## Initialization

```python
class TaskGraph:
    def __init__(
        self,
        schedule_mode: str = "eager",
        log_level: str = "SUCCESS",
    ):
        ...
```

### Parameters

- **schedule_mode**: Scheduling mode.
  - `eager` (default): All nodes are started at once; dependencies are automatically controlled through data flow. Suitable for maximizing parallelism.
  - `staged`: Layer-by-layer execution. Only applicable to DAGs. Nodes are started layer by layer in order; the next layer starts only after the previous layer has fully completed.
- **log_level**: Global log level (TRACE/DEBUG/SUCCESS/INFO/WARNING/ERROR/CRITICAL).

### Setting Stages

```python
def set_stages(self, root_stages: list[TaskStage], stages: list[TaskStage]):
    """
    Set the task graph's nodes.
    
    :param root_stages: List of entry nodes (root nodes). Supports multiple root nodes (forest structure).
    :param stages: List of other non-root nodes (optional).
    """
```

## Core Features

### Graph Construction and Analysis

- **Automatic construction**: Based on `root_stages` and inter-node connections (`out_edges`), automatically traverses and builds the entire graph structure.
- **DAG detection**: Automatically detects whether the graph is a Directed Acyclic Graph (DAG).
- **Layer analysis**: If the graph is a DAG, automatically computes node layers for `staged` scheduling or visualization.

### Starting Execution

```python
def start_graph(self, init_tasks_dict: dict, put_termination_signal: bool = True):
    """
    Start the task graph.
    
    :param init_tasks_dict: Initial task data in the format {stage_tag: [task_data, ...]}
    :param put_termination_signal: Whether to automatically inject a termination signal after the initial tasks.
    """
```

Example:
```python
graph = TaskGraph(schedule_mode="eager")
graph.set_stages(root_stages=[stage_a, stage_b], stages=[])
graph.start_graph({
    stage_a.get_tag(): [1, 2, 3, 4, 5]
})
```

### Resource Management

- **Process management**: Automatically creates and manages subprocesses (for Stages in `process` mode).
- **Queue management**: Automatically creates inter-node communication queues (`TaskInQueue`, `TaskOutQueue`).
- **Graceful shutdown**: Ensures all subprocesses exit correctly after task completion, or are forcefully terminated in case of exceptions.

### Monitoring and Reporting

- **Runtime snapshots**: `collect_runtime_snapshot()` collects each node's running status (processed count, backlog, rate, etc.).
- **Error persistence**: Persists runtime error logs to local JSONL files (`fallback/` directory).
- **Web reporting**: Integrates `TaskReporter` to push status updates to the Web UI in real time.

## Configuration Methods

### set_reporter

```python
def set_reporter(self, is_report=False, host="127.0.0.1", port=5000):
    """
    Set up the reporter for pushing status to the Web UI.

    :param is_report: Whether to enable the reporter
    :param host: Web service host address
    :param port: Web service port
    """
```

### set_ctree

```python
def set_ctree(
    self,
    use_ctree=False,
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778,
    transport="grpc",
):
    """
    Set up the CelestialTree client for event tracing.

    :param use_ctree: Whether to use CelestialTree
    :param host: Service host address
    :param http_port: HTTP port
    :param grpc_port: gRPC port
    :param transport: Transport protocol
    """
```

### set_graph_mode

```python
def set_graph_mode(self, stage_mode: str, execution_mode: str):
    """
    Batch-set the execution mode for all nodes.

    :param stage_mode: Node execution mode ('serial', 'thread', or 'process')
    :param execution_mode: Node internal execution mode ('serial', 'thread', or 'async')
    """
```

### _set_log_level

```python
def _set_log_level(self, level="SUCCESS"):
    """
    Set the global log level.
    """
```

## Data Query Methods

### Status Queries

```python
# Get node status dictionary
def get_status_dict(self) -> dict[str, dict]:
    """Returns the real-time status of each node."""

# Get graph summary
def get_graph_summary(self) -> dict:
    """Returns global statistics (success count, failure count, backlog count, etc.)."""
```

### Analysis Queries

```python
# Get analysis information
def get_graph_analysis(self) -> dict:
    """Returns isDAG, schedule_mode, class_name, layers_dict, and other information."""

# Get structure JSON
def get_structure_json(self) -> list[dict]:
    """Returns a JSON representation of the graph structure."""

# Get structure list
def get_structure_list(self) -> list[str]:
    """Returns a formatted structure list."""
```

### NetworkX Graph

```python
def get_networkx_graph(self):
    """
    Get the task graph's networkx directed graph (DiGraph).
    Can be used for complex graph analysis.
    """
```

### Error Queries

```python
# Get failed tasks by stage
def get_fail_by_stage_dict(self):
    """Returns a dictionary in {stage_tag: [failed_tasks]} format."""

# Get failed tasks by error type
def get_fail_by_error_dict(self):
    """Returns a dictionary in {error_type: [failed_tasks]} format."""

# Get fallback file path
def get_fallback_path(self) -> str:
    """Returns the error log file path."""
```

### Trace Queries

```python
# Get input trace
def get_stage_input_trace(self, stage_tag: str) -> str:
    """Get the input event trace for the specified node (requires ctree to be enabled)."""

# Get error trace
def get_error_trace(self, error_id: int):
    """Get trace information for the specified error."""
```

## Task Injection

### put_stage_queue

```python
def put_stage_queue(self, tasks_dict: dict, put_termination_signal=True):
    """
    Dynamically inject tasks into node queues.

    :param tasks_dict: {stage_tag: [tasks]}
    :param put_termination_signal: Whether to inject a termination signal
    """
```

Example:
```python
# Dynamically inject tasks
graph.put_stage_queue({
    stage_a.get_tag(): [6, 7, 8]
})

# Inject termination signal
from celestialflow import TerminationSignal
graph.put_stage_queue({
    stage_a.get_tag(): [TerminationSignal()]
})
```

## Scheduling Mode Details

### Eager Mode

- All nodes start immediately
- Dependencies are automatically controlled through queue flow
- Maximizes parallelism
- Suitable for most scenarios

### Staged Mode

- Executes layer by layer in order
- The next layer starts only after the previous layer has fully completed
- Only applicable to DAGs
- Suitable for debugging, performance analysis, and resource control

## Notes

1. **Non-DAG graphs**: For cyclic graphs, automatic termination signal injection is not recommended; use the Web interface for manual control instead.
2. **Process cleanup**: In exceptional situations, the framework forcefully terminates subprocesses and logs the event.
3. **Unconsumed tasks**: Upon stopping, unconsumed tasks are collected and recorded as errors.
4. **Web monitoring**: The Web service must be started first, then `set_reporter(True)` should be configured.

## Example

```python
from celestialflow import TaskStage, TaskGraph

# Create nodes
stage_a = TaskStage("A", func=process_a, execution_mode="thread", stage_mode="process")
stage_b = TaskStage("B", func=process_b, execution_mode="serial", stage_mode="process")
stage_c = TaskStage("C", func=process_c, execution_mode="serial", stage_mode="process")

# Build graph
graph = TaskGraph(schedule_mode="eager", log_level="INFO")
graph.set_stages(root_stages=[stage_a], stages=[stage_b, stage_c])
graph.connect([stage_a], [stage_b, stage_c])

# Configure
graph.set_reporter(True, host="127.0.0.1", port=5005)

# Start
graph.start_graph({
    stage_a.get_tag(): range(100)
})
```
