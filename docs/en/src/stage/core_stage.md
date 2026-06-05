# TaskStage

> 📅 Last Updated: 2026/06/05

`TaskStage` is the basic unit for building a `TaskGraph`. It inherits from `TaskExecutor` and adds graph structure connection capabilities and `stage_mode` control logic.

> Note: `TaskStage` is also a one-shot object. Queue bindings, graph links, and runtime counters are designed for one execution lifecycle and should not be assumed reusable after completion.

## Inheritance Hierarchy

`TaskExecutor` -> `TaskStage`

`TaskStage` inherits all core capabilities of `TaskExecutor` (execution modes, retries, metrics monitoring, etc.) and adds inter-node connection logic.

## Key Concepts

- **Stage Mode**: The scheduling logic mode of a node in the task graph.
  - `serial`: Serial mode, runs in the main process.
  - `thread`: Thread mode, runs in an independent thread within the main process.
- **Execution Mode**: The concurrency mode for processing tasks internally within the node (`serial`, `thread`, `async`).
- **Topology**: The upstream/downstream connection relationships between nodes are managed by `TaskGraph`; `TaskStage` itself does not store adjacency tables.

## Initialization

```python
class TaskStage(TaskExecutor):
    def __init__(
        self,
        name: str,
        func: Callable[..., Any],
        stage_mode: str = "serial",
        **kwargs: Any,
    ):
        """
        :param name: Node name (unique identifier)
        :param func: Execution function
        :param stage_mode: Running mode in the graph ('serial' or 'thread')
        :param kwargs: Parameters forwarded to TaskExecutor (execution_mode, max_workers, max_retries, etc.)
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

## Configuration Methods

### set_stage_mode

```python
def set_stage_mode(self, stage_mode: str):
    """
    Set the node's execution mode in the task graph.
    :param stage_mode: 'serial' or 'thread'
    :raises StageModeError: If the mode is not supported
    """
```

### set_execution_mode

> ⚠️ This method is inherited from `TaskExecutor`; `TaskStage` does not override it.

```python
def set_execution_mode(self, execution_mode: str):
    """
    Set the node's internal task processing mode.

    :param execution_mode: 'serial', 'thread', or 'async'
    :raises ExecutionModeError: If the mode is not supported
    """
```

### set_name

> ⚠️ This method is inherited from `TaskExecutor`; `TaskStage` does not override it.

```python
def set_name(self, name: str):
    """
    Set the node name.
    """
```

## State Management

`TaskStage` uses the `StageStatus` enum to manage lifecycle:

- `NOT_STARTED` (0): Initial state.
- `RUNNING` (1): Started, listening on the queue.
- `STOPPED` (2): Normally stopped or abnormally exited.

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

When `TaskGraph` starts, it calls this method to start the node.

```python
def start_stage(self):
    """
    Start node execution, selecting a scheduler based on execution_mode.
    """
```

1. Calls `_init_state()` to initialize internal state.
2. Records start log.
3. Marks status as `RUNNING`.
4. Enters `TaskDispatch` loop to process tasks.
5. On completion, cleans up resources and marks `STOPPED`.

## State Snapshot

```python
def get_summary(self) -> dict[str, Any]:
    """
    Get the current node's status summary.
    Returns a dict containing class_name, name, func_name, execution_mode, stage_mode.
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

## Usage Examples

The following examples demonstrate the complete usage of `TaskStage`, including multiple execution modes, state management, and graph connections.

### Basic Usage (serial mode)

```python
from celestialflow import TaskGraph, TaskStage

# Create two stages using serial execution mode
def step1(x: int) -> int:
    return x + 5

def step2(x: int) -> int:
    return x * 3

stage1 = TaskStage(
    name="Step1",
    func=step1,
    execution_mode="serial",  # Single-threaded sequential execution
    stage_mode="serial",      # Run in main process
)
stage2 = TaskStage(
    name="Step2",
    func=step2,
    execution_mode="serial",
    stage_mode="serial",
)

# Build and execute the graph
chain = TaskGraph()
chain.set_stages([stage1, stage2])
chain.connect([stage1], [stage2])
chain.start_graph({stage1.get_name(): [1, 2, 3, 4, 5]})

print(f"Chain summary: {chain.get_graph_summary()}")
```

### Using thread Execution Mode (I/O-Intensive)

```python
import time
from celestialflow import TaskGraph, TaskStage

def io_task(x: int) -> int:
    time.sleep(0.05)  # Simulate network I/O
    return x * 10

stage_a = TaskStage(
    name="IOWorker",
    func=io_task,
    execution_mode="thread",  # Thread pool concurrency
    max_workers=4,            # 4 concurrent threads
    stage_mode="thread",      # Run in independent thread
)

# Standalone execution (outside graph structure)
stage_a.start_stage()
```

### Async Mode

```python
import asyncio
from celestialflow import TaskStage

async def async_process(x: int) -> int:
    await asyncio.sleep(0.01)  # Simulate async I/O
    return x ** 2

async_stage = TaskStage(
    name="AsyncProcessor",
    func=async_process,
    execution_mode="async",
    max_workers=4,
)
print(f"Async stage summary: {async_stage.get_summary()}")
```

### State Management

```python
from celestialflow import TaskStage
from celestialflow.runtime.util_types import StageStatus

stage = TaskStage("StatusDemo", func=lambda x: x)

print(f"Initial status: {stage.get_status().name}")  # NOT_STARTED

stage.mark_running()
print(f"Running: {stage.get_status().name}")   # RUNNING

stage.mark_stopped()
print(f"Stopped: {stage.get_status().name}")   # STOPPED
```

### Custom Subclass

```python
from celestialflow import TaskStage

class MyCustomStage(TaskStage):
    def get_args(self, task):
        """Custom argument extraction"""
        return (task["data"],)

    def process_result(self, task, result):
        """Custom result processing"""
        return {"original": task, "computed": result}

# Using the custom stage
stage = MyCustomStage("Custom", func=lambda x: x * 10)
print(f"Summary: {stage.get_summary()}")
```

## Notes

1. **Name Uniqueness**: Within the same `TaskGraph`, each `TaskStage`'s `name` must be unique; otherwise, a `DuplicateNodeError` will be raised.
2. **Async Support**: If `execution_mode` is set to `async`, `func` must be a coroutine function.
3. **Resource Cleanup**: When a node stops, client connections and closure resources are automatically released.
