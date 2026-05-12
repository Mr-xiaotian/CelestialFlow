# Clone

> 📅 Last updated: 2026/05/08

`utils/util_clone.py` provides functionality for cloning executors, stages, and task graphs, used for performance testing and configuration reuse.

## Design Purpose

In performance testing, the same task graph configuration needs to be run multiple times, but each run modifies internal state. The cloning functionality creates fully independent copies, avoiding state contamination.

## Main Functions

### clone_executor

Clones a `TaskExecutor` instance.

```python
def clone_executor(executor: TaskExecutor) -> TaskExecutor:
    """
    Clone an executor.

    :param executor: The executor to clone
    :return: A new executor instance
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
- `enable_duplicate_check`: Duplicate check toggle
- `log_level`: Log level
- `retry_exceptions`: List of retryable exceptions

### clone_stage

Clones a `TaskStage` instance.

```python
def clone_stage(stage: TaskStage) -> TaskStage:
    """
    Clone a stage.

    :param stage: The stage to clone
    :return: A new stage instance
    """
```

In addition to `TaskExecutor` attributes, the following is also copied:
- `stage_mode`: Stage mode

### clone_graph

Clones a `TaskGraph` instance.

```python
def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    Clone a task graph.

    :param graph: The task graph to clone
    :return: A new task graph instance
    """
```

Cloning process:
1. Traverse all stages in the original graph (BFS)
2. Clone each stage and establish a mapping
3. Rebuild connections between stages
4. Copy graph configuration (schedule_mode, log_level)
5. Copy CelestialTree and Reporter configuration

## Usage Examples

### Cloning an Executor

```python
from celestialflow import TaskExecutor
from celestialflow.utils.util_clone import clone_executor

# Create the original executor
executor = TaskExecutor(
    "Processor",
    process,
    execution_mode="thread",
    max_workers=10,
    max_retries=3,
)

# Clone the executor
cloned = clone_executor(executor)

# Both executors run independently
executor.start(range(100))
cloned.start(range(100))
```

### Cloning a Task Graph

```python
from celestialflow import TaskGraph
from celestialflow.utils.util_clone import clone_graph

# Create the original graph
graph = TaskGraph(schedule_mode="eager")
graph.set_stages(stages=[stage_a, stage_b])

# Clone the graph for testing
cloned_graph = clone_graph(graph)

# Run the cloned graph
cloned_graph.start_graph(init_tasks)
```

### Usage in Benchmarks

```python
from celestialflow.utils.util_benchmark import benchmark_graph

# benchmark_graph internally uses clone_graph
results = benchmark_graph(
    graph,
    init_tasks_dict={stage_a.get_tag(): range(100)},
    stage_modes=["serial", "thread", "process"],
    execution_modes=["serial", "thread"],
)
```

## Notes

1. **State Independence**: Cloned objects are fully independent from the originals; modifications do not affect each other
2. **Connection Rebuilding**: Connections between stages are rebuilt when cloning a graph
3. **Function References**: Cloning copies function references, not the functions themselves
4. **Performance Overhead**: Cloning large graphs has some overhead, but is faster than rebuilding from scratch
