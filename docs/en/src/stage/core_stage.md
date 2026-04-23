# TaskStage

> 📅 Last updated: 2026/04/23

`TaskStage` is the basic building unit for constructing a `TaskGraph`. It inherits from `TaskExecutor` and adds graph structure connection capabilities.

## Inheritance Hierarchy

`TaskExecutor` -> `TaskStage`

`TaskStage` retains all execution capabilities of `TaskExecutor` (execution modes, retry, caching, etc.) and adds inter-node connection logic.

## Key Concepts

- **Stage Mode**: The running mode of a node within a graph.
  - `serial`: Serial mode, runs in the main process.
  - `thread`: Thread mode, runs in an independent thread within the main process.
  - `process`: Parallel mode, runs in an independent subprocess.
- **Topological Relationships**: Upstream/downstream connections between nodes are managed by `TaskGraph` (via `graph.out_edges` / `graph.in_edges`), not stored within the node itself.

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
        enable_success_cache=False,
        enable_duplicate_check=True,
        stage_mode="serial",
    ):
        ...
```

Parameters are the same as `TaskExecutor`, with an additional `stage_mode` parameter. The main difference is that `TaskStage`'s `execution_mode` can only be `thread` or `serial` (`process` mode is controlled by `stage_mode`).

## Graph Construction Methods

### graph.connect

Establish connections between nodes using `graph.connect(from_stages, to_stages)`. `stage_mode` and `name` are passed through `TaskStage.__init__()` constructor parameters.

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

### Mode Configuration

```python
# Set the node's running mode
def set_stage_mode(self, stage_mode: str):
    """
    Set the execution mode of the current node within the graph.
    :param stage_mode: 'serial', 'thread', or 'process'
    """

# Get the node's running mode
def get_stage_mode(self) -> str:
    """
    Get the execution mode of the current node within the graph.
    """
```

### Name Configuration

```python
def set_name(self, name: str):
    """
    Set the name of the current node.
    Note: After a name change, the tag will be invalidated and regenerated.
    """
```

## State Management

`TaskStage` uses the `StageStatus` enum to manage running states:

- `NOT_STARTED` (0): Not started
- `RUNNING` (1): Running
- `STOPPED` (2): Stopped

### State Methods

```python
# Mark as running
def mark_running(self) -> None:
    """Mark: the stage is running."""

# Mark as stopped
def mark_stopped(self) -> None:
    """Mark: the stage has stopped (called in finally block upon normal completion)."""

# Get status
def get_status(self) -> StageStatus:
    """Read the current status (returns a StageStatus enum)."""
```

## Execution Mechanism

When a `TaskGraph` starts, each `TaskStage` determines its execution method based on `stage_mode`:

- **process mode**: The node is wrapped in an independent `Process` and launched in isolation from other nodes.
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

The node continuously fetches tasks from `input_queues`, executes them (using `TaskExecutor`'s logic), and places results into `output_queues`.

## Status Snapshot

```python
def get_summary(self) -> dict:
    """
    Get a status snapshot of the current node.
    Includes: name, func_name, class_name, execution_mode, stage_mode
    """
```

## Execution Mode Restrictions

In `TaskStage`, the available values for `execution_mode` are restricted:

```python
# Valid modes
valid_modes = ("thread", "serial")

# Note: process mode is controlled by stage_mode, not execution_mode
```

## Extending Through Inheritance

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

1. **Process Mode**: When `stage_mode="process"`, ensure the function is pickleable (avoid lambdas, nested functions, etc.).
2. **Counter Cascading**: When the upstream is a `TaskSplitter` or `TaskRouter`, counters are automatically cascaded.
3. **State Sharing**: Implemented using `multiprocessing.Value`, supporting cross-process state queries.
4. **Tag Uniqueness**: Tags are composed of `name[func_name]`, used for log tracing and graph topology identification.
