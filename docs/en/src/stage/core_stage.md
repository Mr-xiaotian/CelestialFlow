# TaskStage

> 📅 Last Updated: 2026/05/15

`TaskStage` is the basic unit for building a `TaskGraph`. It inherits from `TaskExecutor` and adds graph structure connection capabilities.

## Inheritance Hierarchy

`TaskExecutor` -> `TaskStage`

`TaskStage` retains all execution capabilities of `TaskExecutor` (execution modes, retries, caching, etc.) and adds inter-node connection logic.

## Key Concepts

- **Stage Mode**: The running mode of a node in the graph.
  - `serial`: Serial mode, runs in the main process.
  - `thread`: Thread mode, runs in an independent thread within the main process.
- **Topology**: The upstream/downstream connection relationships between nodes are managed by `TaskGraph` (via `graph.out_edges` / `graph.in_edges`), not stored in the nodes themselves.

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
        log_level="SUCCESS",
        stage_mode="serial",
    ):
        ...
```

Parameters are the same as `TaskExecutor`, with the addition of the `stage_mode` parameter. `TaskStage`'s `execution_mode` can be `serial`, `thread`, or `async`.

## Graph Building Methods

### graph.connect

Establishes connections between nodes via `graph.connect(from_stages, to_stages)`. `stage_mode` and `name` are passed through `TaskStage.__init__()` constructor parameters.

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
stage_a = TaskStage("StageA", func=process_a, execution_mode="thread", stage_mode="thread")
stage_b = TaskStage("StageB", func=process_b, execution_mode="serial", stage_mode="thread")

# Create graph and connect nodes
graph = TaskGraph()
graph.set_stages(stages=[stage_a, stage_b])
graph.connect([stage_a], [stage_b])
```

### Mode Settings

```python
# Set node running mode
def set_stage_mode(self, stage_mode: str):
    """
    Set the current node's execution mode in the graph.
    :param stage_mode: 'serial' or 'thread'
    """

# Get node running mode
def get_stage_mode(self) -> str:
    """
    Get the current node's execution mode in the graph.
    """
```

### Name Settings

```python
def set_name(self, name: str):
    """
    Set the current node name.
    Note: After name change, the tag becomes invalid and will be regenerated.
    """
```

## State Management

`TaskStage` uses the `StageStatus` enum to manage running state:

- `NOT_STARTED` (0): Not started
- `RUNNING` (1): Running
- `STOPPED` (2): Stopped

### State Methods

```python
# Mark as running
def mark_running(self) -> None:
    """Mark: stage is running."""

# Mark as stopped
def mark_stopped(self) -> None:
    """Mark: stage has stopped (called in finally on normal completion)."""

# Get status
def get_status(self) -> StageStatus:
    """Read the current status (returns StageStatus enum)."""
```

## Running Mechanism

When `TaskGraph` starts, each `TaskStage` determines its running method based on `stage_mode`:

- **thread mode**: Node starts in an independent thread.
- **serial mode**: Node runs serially in the main process (typically used for debugging).

### start_stage

```python
def start_stage(
    self,
    input_queue: TaskInQueue,
    output_queue: TaskOutQueue,
    fail_queue: Queue,
    log_queue: Queue,
):
    """
    Start node execution.

    :param input_queue: Input queue
    :param output_queue: Output queue
    :param fail_queue: Failure queue
    :param log_queue: Log queue
    """
```

The node continuously fetches tasks from `input_queue`, executes them (using `TaskExecutor` logic), and places results into `output_queue`.

## State Snapshot

```python
def get_summary(self) -> dict:
    """
    Get the current node state snapshot.
    Includes: name, func_name, class_name, execution_mode, stage_mode
    """
```

## Execution Mode Restrictions

In `TaskStage`, the available values for `execution_mode` are restricted:

```python
# Valid modes
valid_modes = ("serial", "thread", "async")

# Note: stage_mode and execution_mode are independent configurations
```

## Inheritance Extension

When creating custom Stages, the following methods can be overridden:

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

1. **Counter Cascading**: When upstream is a `TaskSplitter` or `TaskRouter`, counters are automatically cascaded.
2. **Tag Uniqueness**: Tags are composed of `name[func_name]`, used for log tracing and graph topology identification.
