# TaskStage

> 📅 Last updated: 2026/04/24

`TaskStage` is the basic building block for constructing a `TaskGraph`. It inherits from `TaskExecutor` and adds graph-structure-related connection capabilities.

## Inheritance Hierarchy

`TaskExecutor` -> `TaskStage`

`TaskStage` retains all execution capabilities of `TaskExecutor` (execution modes, retries, caching, etc.) and adds inter-node connection logic.

## Key Concepts

- **Stage Mode**: The node's execution mode within the graph.
  - `serial`: Serial mode, runs in the main process.
  - `thread`: Thread mode, runs as an independent thread in the main process.
  - `process`: Parallel mode, runs in a separate subprocess.
- **Topological Relationships**: Upstream and downstream connections between nodes are managed by `TaskGraph` (via `graph.out_edges` / `graph.in_edges`), not stored on the nodes themselves.

## Initialization

```python
class TaskStage(TaskExecutor):
    def __init__(
        self,
        name,
        func,
        execution_mode="serial",
        max_workers=20,
        max_retries=1,
        max_info=50,
        unpack_task_args=False,
        enable_duplicate_check=True,
        stage_mode="serial",
    ):
        ...
```

Parameters are the same as `TaskExecutor`, with the additional `stage_mode` parameter. `TaskStage`'s `execution_mode` can be `serial`, `thread`, or `async` (`process` mode is controlled by `stage_mode`).

## Graph Construction Methods

### graph.connect

Establish connections between nodes via `graph.connect(from_stages, to_stages)`. `stage_mode` and `name` are passed through `TaskStage.__init__()` constructor arguments.

```python
def connect(
    self,
    from_stages: list[TaskStage],
    to_stages: list[TaskStage],
):
    """
    Connect upstream nodes to downstream nodes.

    :param from_stages: List of upstream nodes
    :param to_stages: List of downstream nodes
    """
```

Example:
```python
stage_a = TaskStage("StageA", func=process_a, execution_mode="thread", stage_mode="process")
stage_b = TaskStage("StageB", func=process_b, execution_mode="serial", stage_mode="process")

# Create graph and connect nodes
graph = TaskGraph()
graph.set_stages(root_stages=[stage_a], stages=[stage_b])
graph.connect([stage_a], [stage_b])
```

### Mode Setting

```python
# Set node execution mode
def set_stage_mode(self, stage_mode: str):
    """
    Set the current node's execution mode within the graph.
    :param stage_mode: 'serial', 'thread', or 'process'
    """

# Get node execution mode
def get_stage_mode(self) -> str:
    """
    Get the current node's execution mode within the graph.
    """
```

### Name Setting

```python
def set_name(self, name: str):
    """
    Set the current node's name.
    Note: After a name change, the tag will be invalidated and regenerated.
    """
```

## Status Management

`TaskStage` uses the `StageStatus` enum to manage its running state:

- `NOT_STARTED` (0): Not started
- `RUNNING` (1): Running
- `STOPPED` (2): Stopped

### Status Methods

```python
# Mark as running
def mark_running(self) -> None:
    """Mark: stage is running."""

# Mark as stopped
def mark_stopped(self) -> None:
    """Mark: stage has stopped (called in finally upon normal completion)."""

# Get status
def get_status(self) -> StageStatus:
    """Read the current status (returns a StageStatus enum)."""
```

## Execution Mechanism

When `TaskGraph` starts, each `TaskStage` determines its execution method based on `stage_mode`:

- **process mode**: The node is wrapped in a separate `Process` and launched in isolation from other nodes.
- **serial mode**: The node runs in the main process (typically used for debugging).

### start_stage

```python
def start_stage(
    self,
    input_queues: TaskInQueue,
    output_queues: TaskOutQueue,
    fail_queue: MPQueue,
    log_queue: MPQueue,
):
    """
    Start node execution.

    :param input_queues: Input queues
    :param output_queues: Output queues
    :param fail_queue: Failure queue
    :param log_queue: Log queue
    """
```

The node continuously retrieves tasks from `input_queues`, executes them (using `TaskExecutor`'s logic), and places results into `output_queues`.

## Status Snapshot

```python
def get_summary(self) -> dict:
    """
    Get the current node's status snapshot.
    Includes: name, func_name, class_name, execution_mode, stage_mode
    """
```

## Execution Mode Restrictions

In `TaskStage`, the available values for `execution_mode` are restricted:

```python
# Valid modes
valid_modes = ("serial", "thread", "async")

# Note: process mode is controlled by stage_mode, not execution_mode
```

## Inheritance and Extension

When creating a custom Stage, you can override the following methods:

```python
class MyStage(TaskStage):
    def get_args(self, task):
        """Custom argument extraction"""
        return (task.data,)

    def process_result(self, task, result):
        """Custom result processing"""
        return {"data": result, "metadata": task.metadata}
```

## Notes

1. **Process mode**: When `stage_mode="process"`, ensure the function is picklable (avoid lambdas, nested functions, etc.).
2. **Counter cascading**: When the upstream is a `TaskSplitter` or `TaskRouter`, counters cascade automatically.
3. **State sharing**: Implemented using `multiprocessing.Value`, supporting cross-process state queries.
4. **Tag uniqueness**: Tags are composed of `name[func_name]`, used for log tracing and graph topology identification.
