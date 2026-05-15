# Clone

> 📅 Last Updated: 2026/05/15

`utils/util_clone.py` provides functionality for cloning executors, nodes, and task graphs, used for performance testing and configuration reuse.

## Design Purpose

In performance testing, the same task graph configuration needs to be run multiple times, but each run modifies internal state. The cloning feature creates completely independent copies to avoid state pollution.

## Main Functions

### clone_executor

Clones a `TaskExecutor` instance.

```python
def clone_executor(executor: TaskExecutor) -> TaskExecutor:
    """
    Clone an executor.

    :param executor: Executor to clone
    :return: New executor instance
    """
```

Copied attributes:
- `name`: Executor name
- `func`: Task function
- `execution_mode`: Execution mode
- `max_workers`: Concurrency limit
- `max_retries`: Maximum retry count
- `max_info`: Maximum log message length
- `unpack_task_args`: Whether to unpack arguments
- `enable_duplicate_check`: Duplicate checking toggle
- `log_level`: Log level
- `retry_exceptions`: Retryable exception list

### clone_stage

Clones a `TaskStage` instance.

```python
def clone_stage(stage: TaskStage) -> TaskStage:
    """
    Clone a node.

    :param stage: Node to clone
    :return: New node instance
    """
```

In addition to `TaskExecutor` attributes, also copies:
- `stage_mode`: Node mode

### clone_graph

Clones a `TaskGraph` instance.

```python
def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    Clone a task graph.

    :param graph: Task graph to clone
    :return: New task graph instance
    """
```

Cloning process:
1. Traverse all nodes in the original graph (BFS)
2. Clone each node and build a mapping
3. Rebuild connections between nodes
4. Copy graph configuration (schedule_mode, log_level)
5. Copy CelestialTree and Reporter configuration

## Usage Examples

### Cloning an Executor

```python
from celestialflow import TaskExecutor
from celestialflow.utils.util_clone import clone_executor

# Create original executor
executor = TaskExecutor(
    "Processor",
    process,
    execution_mode="thread",
    max_workers=10,
    max_retries=3,
)

# Clone executor
cloned = clone_executor(executor)

# Two executors run independently
executor.start(range(100))
cloned.start(range(100))
```

### Cloning a Task Graph

```python
from celestialflow import TaskGraph
from celestialflow.utils.util_clone import clone_graph

# Create original graph
graph = TaskGraph(schedule_mode="eager")
graph.set_stages(stages=[stage_a, stage_b])

# Clone graph for testing
cloned_graph = clone_graph(graph)

# Run the cloned graph
cloned_graph.start_graph(init_tasks)
```

### Using in Benchmarks

```python
from celestialflow.utils.util_benchmark import benchmark_graph

# benchmark_graph internally uses clone_graph
results = benchmark_graph(
    graph,
    init_tasks_dict={stage_a.get_tag(): range(100)},
    stage_modes=["serial", "thread"],
    execution_sync_modes=["serial", "thread"],
    execution_async_modes=["async"],
)
```

## Notes

1. **State Independence**: Cloned objects are completely independent from originals; modifications do not affect each other
2. **Connection Rebuilding**: Cloning a graph rebuilds connections between nodes
3. **Function References**: Cloning only copies function references, not the functions themselves
4. **Performance Overhead**: Cloning large graphs has some overhead, but is faster than rebuilding
