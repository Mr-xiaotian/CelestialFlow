# TaskGraph

> 📅 Last Updated: 2026/05/15

`TaskGraph` is the core scheduler of CelestialFlow, responsible for managing dependency relationships, execution flow, resource allocation, and lifecycle of a set of `TaskStage` nodes.

## Initialization

```python
class TaskGraph:
    def __init__(
        self,
        schedule_mode: str = "eager",
        log_level: str = "INFO",
    ):
        ...
```

### Parameters

- **schedule_mode**: Scheduling mode.
  - `eager` (default): All nodes start at once; dependencies are automatically controlled through data flow. Suitable for maximizing parallelism.
  - `staged`: Layer-by-layer execution. Only applicable to DAGs. Starts layers in level order; the next layer starts only after the previous layer has fully completed.
- **log_level**: Global log level (TRACE/DEBUG/INFO/SUCCESS/WARNING/ERROR/CRITICAL), defaults to `"INFO"`.

### Setting Nodes

```python
def set_stages(self, stages: list[TaskStage]):
    """
    Set the nodes of the task graph. Source nodes are automatically computed via SCC condensation.
    
    :param stages: List of all nodes.
    """
```

## Core Features

### Graph Construction and Analysis

- **Automatic Construction**: Automatically traverses and builds the entire graph structure based on the node list and their connections (`out_edges`).
- **Automatic Source Node Detection**: Automatically identifies source nodes (nodes with no incoming edges) through SCC condensation.
- **DAG Detection**: Automatically detects whether the graph is a Directed Acyclic Graph (DAG).
- **Level Analysis**: If the graph is a DAG, node levels are automatically computed for `staged` scheduling or visualization.

### Starting Execution

```python
def start_graph(self, init_tasks_dict: dict, put_termination_signal: bool = True):
    """
    Start the task graph.
    
    :param init_tasks_dict: Initial task data in the format {stage_tag: [task_data, ...]}
    :param put_termination_signal: Whether to automatically inject a termination signal after initial tasks.
    """
```

Example:
```python
graph = TaskGraph(schedule_mode="eager")
graph.set_stages(stages=[stage_a, stage_b])
graph.start_graph({
    stage_a.get_tag(): [1, 2, 3, 4, 5]
})
```

### Resource Management

- **Queue Management**: Automatically creates communication queues (`TaskInQueue`, `TaskOutQueue`) between nodes.
- **Graceful Exit**: Ensures all nodes exit correctly after task completion.

### Monitoring and Reporting

- **Runtime Snapshot**: `collect_runtime_snapshot()` collects the runtime status of each node (processed count, backlog count, rate, etc.).
- **Error Persistence**: Persists runtime error logs to local JSONL files (`fallback/` directory).
- **Web Reporting**: Integrates `TaskReporter` to push status in real-time to the Web UI.

## Configuration Methods

### set_reporter

```python
def set_reporter(self, is_report=False, host="127.0.0.1", port=5000):
    """
    Configure the reporter for pushing status to the Web UI.

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
    Configure the CelestialTree client for event tracing.

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
    Set the execution mode for all nodes in batch.

    :param stage_mode: Node execution mode ('serial' or 'thread')
    :param execution_mode: Internal execution mode of nodes ('serial', 'thread', or 'async')
    """
```

### _set_log_level

```python
def _set_log_level(self, level="INFO"):
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
    """Returns isDAG, schedule_mode, class_name, layers_dict, etc."""

# Get structure JSON
def get_structure_json(self) -> list[dict]:
    """Returns the JSON representation of the graph structure."""

# Get structure list
def get_structure_list(self) -> list[str]:
    """Returns a formatted structure list."""
```

### NetworkX Graph

```python
def get_networkx_graph(self):
    """
    Get the networkx directed graph (DiGraph) of the task graph.
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
    """Get the input event trace for a specified node (requires ctree to be enabled)."""
```

### Other Queries

```python
# Get historical status of each node
def get_stage_history(self) -> dict[str, list[dict]]:
    """Returns a list of historical snapshots for each node."""

# Get total error count
def get_total_error_num(self) -> int:
    """Returns the total number of errors."""

# Get source node list
def get_source_stages(self) -> list[TaskStage]:
    """Returns the list of source nodes (automatically computed via SCC condensation)."""
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

## Scheduling Modes Explained

### Eager Mode

- All nodes start immediately
- Dependencies are automatically controlled through queue flow
- Maximizes parallelism
- Suitable for most scenarios

### Staged Mode

- Executes layer by layer in level order
- The next layer starts only after the previous layer has fully completed
- Only applicable to DAGs
- Suitable for debugging, performance analysis, and resource control

## Notes

1. **Non-DAG Graphs**: For cyclic graphs, automatic termination signal injection is not recommended; use the Web interface for manual control instead.
2. **Unconsumed Tasks**: Unconsumed tasks are collected and logged as errors when stopping.
4. **Web Monitoring**: The Web service must be started first, then enable with `set_reporter(True)`.

## Example

```python
from celestialflow import TaskStage, TaskGraph

# Create nodes
stage_a = TaskStage("A", func=process_a, execution_mode="thread", stage_mode="thread")
stage_b = TaskStage("B", func=process_b, execution_mode="serial", stage_mode="thread")
stage_c = TaskStage("C", func=process_c, execution_mode="serial", stage_mode="thread")

# Build graph
graph = TaskGraph(schedule_mode="eager", log_level="INFO")
graph.set_stages(stages=[stage_a, stage_b, stage_c])
graph.connect([stage_a], [stage_b, stage_c])

# Configure
graph.set_reporter(True, host="127.0.0.1", port=5005)

# Start
graph.start_graph({
    stage_a.get_tag(): range(100)
})
```
