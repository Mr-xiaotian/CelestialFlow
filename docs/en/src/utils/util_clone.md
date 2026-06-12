# Clone

> 📅 Last Updated: 2026/06/11

`utils/util_clone.py` provides functionality for cloning executors, nodes, and task graphs, used for performance testing and configuration reuse.

## Design Purpose

In performance testing, the same task graph configuration needs to be run multiple times, but each run modifies internal state. Cloning functionality creates completely independent copies, avoiding state contamination.

## Key Functions

### clone_executor

Clones a `TaskExecutor` instance.

```python
def clone_executor(executor: TaskExecutor) -> TaskExecutor:
    """
    Clones an executor.

    :param executor: The executor to clone
    :return: A new executor instance
    """
```

Copied attributes:
- `name`: Executor name
- `func`: Task function
- `execution_mode`: Execution mode
- `max_workers`: Concurrency limit
- `max_retries`: Max retry count
- `max_info`: Max log info length
- `enable_duplicate_check`: Duplicate check toggle
- `log_level`: Log level
- `retry_exceptions`: List of retryable exceptions

### clone_stage

Clones a `TaskStage` instance.

```python
def clone_stage(stage: TaskStage) -> TaskStage:
    """
    Clones a node.

    :param stage: The node to clone
    :return: A new node instance
    """
```

In addition to `TaskExecutor` attributes, also copies:
- `stage_mode`: Node mode

### clone_graph

Clones a `TaskGraph` instance.

```python
def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    Clones a task graph.

    :param graph: The task graph to clone
    :return: A new task graph instance
    """
```

Cloning flow:
1. Traverse all nodes of the original graph (BFS)
2. Clone each node and build a mapping
3. Rebuild connection relationships between nodes
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

# Both executors run independently
executor.start(range(100))
cloned.start(range(100))
```

### Cloning a Node (TaskStage)

```python
from celestialflow import TaskStage
from celestialflow.utils.util_clone import clone_stage

# Create original node
stage = TaskStage(
    "Processor",
    process_func,
    stage_mode="thread",
    execution_mode="thread",
    max_workers=4,
)

# Clone node
cloned_stage = clone_stage(stage)

# Original and cloned nodes run independently, unaffected by each other
stage.start(range(10))
cloned_stage.start(range(10, 20))
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

## Comprehensive Example

The following example demonstrates a complete scenario using `clone_executor`, `clone_stage`, and `clone_graph` together:

```python
import asyncio
from celestialflow import TaskExecutor, TaskStage, TaskGraph
from celestialflow.utils.util_clone import clone_executor, clone_stage, clone_graph


def square(x: int) -> int:
    return x * x


def add_one(x: int) -> int:
    return x + 1


async def main():
    # 1. clone_executor ----
    executor = TaskExecutor(
        "Square", square, execution_mode="thread", max_workers=4
    )
    cloned_exe = clone_executor(executor)
    print(f"clone_executor: mode={cloned_exe.execution_mode}")

    # 2. clone_stage ----
    stage = TaskStage(
        "AddOne", add_one, stage_mode="serial", execution_mode="serial"
    )
    cloned_stg = clone_stage(stage)
    print(f"clone_stage: name={cloned_stg.get_name()}, mode={cloned_stg.get_stage_mode()}")

    # 3. clone_graph ----
    graph = TaskGraph(schedule_mode="eager")
    a = TaskStage("A", square, execution_mode="thread")
    b = TaskStage("B", add_one, execution_mode="thread")
    graph.set_stages([a, b])
    graph.connect([a], [b])

    cloned_grp = clone_graph(graph)
    print(f"clone_graph: schedule_mode={cloned_grp.schedule_mode}")
    print(f"Connection consistency: {graph.out_edges == cloned_grp.out_edges}")

    # Run original and cloned graphs separately; states are completely independent
    await graph.start_graph({a.get_tag(): [1, 2, 3]})
    await cloned_grp.start_graph(
        {list(cloned_grp.stage_runtime_dict.keys())[0]: [10, 20]}
    )


asyncio.run(main())
```

### Using in Benchmarking

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

1. **State independence**: Cloned objects are completely independent from the original (achieved by constructing new instances); modifications do not affect each other
2. **Connection reconstruction**: When cloning a graph, connection relationships between nodes are rebuilt
3. **Function references**: Cloning only copies function references, not the functions themselves
4. **Performance overhead**: Cloning large graphs has some overhead, but is faster than rebuilding from scratch
