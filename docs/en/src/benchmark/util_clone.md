# Clone

> 📅 Last Updated: 2026/08/26

`benchmark/util_clone.py` provides functionality for cloning executors, nodes, and task graphs, used for performance testing and configuration reuse.

## Design Purpose

In performance testing, the same task graph configuration needs to be run multiple times, but each run modifies internal state. The cloning functionality creates completely independent copies, avoiding state contamination.

## Key Functions

### clone_executor

Clones a `TaskExecutor` instance.

```python
def clone_executor[T, R](
    executor: TaskExecutor[T, R],
) -> TaskExecutor[T, R]:
    """
    Clone an executor.

    :param executor: The executor to clone
    :return: The cloned executor
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
- `retry_exceptions`: List of retryable exceptions (set via `set_retry_exceptions()`)

### clone_stage

Clones a `TaskStage` node.

```python
def clone_stage[T, R](
    stage: TaskStage[T, R],
) -> TaskStage[T, R]:
    """
    Clone a node.

    :param stage: The node to clone
    :return: The cloned node
    """
```

Cloning steps:
1. Reuse the executor-style parameter set (`name` / `func` / `execution_mode` / `max_workers` / `max_retries` / `max_info` / `enable_duplicate_check`)
2. Inspect the node class `__init__` parameter set via `inspect.signature`, keeping only the intersection with the executor-style set to avoid passing parameters the node class does not accept
3. Construct a new instance of the **same type** as the original node using the filtered parameters
4. Copy `retry_exceptions`

Impact of parameter filtering:
- A regular `TaskStage`'s `__init__` is `(name, func, **kwargs)`, so after filtering only `name` and `func` are retained; runtime configurations such as `execution_mode` are not copied (the cloned result uses default configuration).
- `TaskSplitter`'s `__init__` only accepts `name` / `split_item`; during cloning only `name` is passed, and split logic is provided by the class's own default implementation.
- `TaskRouter`'s `__init__` requires the mandatory `router` argument, which is not in the filterable set, so cloning a `TaskRouter` directly will raise `TypeError`.

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

Cloning flow:
1. Starting from the source node, traverse the original graph via BFS (breadth-first) in the out-edge order of `graph.order_graph.out_edges` to collect all nodes
2. Clone each node and build a mapping from the original node name to the cloned node
3. Register all cloned nodes via `set_stages()` and rebuild the connection relationships between nodes with `connect()`
4. Copy graph configuration (`name`, `graph_mode`)
5. Copy the CelestialTree (`clone_event_client`) and Reporter configuration (`NullTaskReporter` / `TaskReporter` can be cloned; other types raise `ConfigurationError`)

## Usage Examples

### Cloning an Executor

```python
from celestialflow import TaskExecutor
from celestialflow.benchmark.util_clone import clone_executor


def process(x: int) -> int:
    return x * 2


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
executor.run(range(100))
cloned.run(range(100))
```

### Cloning a Node (TaskStage)

```python
from celestialflow import TaskStage
from celestialflow.benchmark.util_clone import clone_stage


def process_func(x: int) -> int:
    return x + 1


# Create the original node
stage = TaskStage(
    "Processor",
    process_func,
    execution_mode="thread",
    max_workers=4,
)

# Clone the node
cloned_stage = clone_stage(stage)

# Original and cloned nodes run independently, unaffected by each other
stage.run(range(10))
cloned_stage.run(range(10, 20))
```

### Cloning a Task Graph

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.benchmark.util_clone import clone_graph


def process_a(x: int) -> int:
    return x * 2


def process_b(x: int) -> int:
    return x + 1


# Create the original graph
graph = TaskGraph(name="CloneDemo", graph_mode="thread")
stage_a = TaskStage("A", process_a)
stage_b = TaskStage("B", process_b)
graph.set_stages(stages=[stage_a, stage_b])
graph.connect([stage_a], [stage_b])

# Clone the graph for testing
cloned_graph = clone_graph(graph)

# Run the cloned graph
init_tasks = {stage_a.get_name(): [1, 2, 3]}
cloned_graph.run(init_tasks)
```

## Comprehensive Example

The following example demonstrates a complete scenario using `clone_executor`, `clone_stage`, and `clone_graph` together:

```python
import asyncio
from celestialflow import TaskExecutor, TaskStage, TaskGraph
from celestialflow.benchmark.util_clone import clone_executor, clone_stage, clone_graph


def square(x: int) -> int:
    return x * x


def add_one(x: int) -> int:
    return x + 1


async def main():
    # 1. clone_executor ----
    executor = TaskExecutor("Square", square, execution_mode="thread", max_workers=4)
    cloned_exe = clone_executor(executor)
    print(f"clone_executor: mode={cloned_exe.execution_mode}")

    # 2. clone_stage ----
    stage = TaskStage("AddOne", add_one, execution_mode="serial")
    cloned_stg = clone_stage(stage)
    print(
        f"clone_stage: name={cloned_stg.get_name()}, mode={cloned_stg.execution_mode}"
    )

    # 3. clone_graph ----
    graph = TaskGraph(name="CloneDemo", graph_mode="thread")
    a = TaskStage("A", square, execution_mode="thread")
    b = TaskStage("B", add_one, execution_mode="thread")
    graph.set_stages([a, b])
    graph.connect([a], [b])

    cloned_grp = clone_graph(graph)
    print(f"clone_graph: graph mode={cloned_grp.graph_mode}")
    print(
        f"Connection consistency: {graph.order_graph.out_edges == cloned_grp.order_graph.out_edges}"
    )

    # Run original and cloned graphs separately; states are completely independent
    graph.run({a.get_name(): [1, 2, 3]})
    cloned_grp.run({list(cloned_grp.stage_dict.keys())[0]: [10, 20]})


asyncio.run(main())
```

### Using in Benchmarking

```python
import asyncio
from celestialflow import TaskGraph, TaskStage
from celestialflow.benchmark.util_benchmark import benchmark_graph


def task(x: int) -> int:
    return x * 2


async def async_task(x: int) -> int:
    return x * 2


async def main():
    stage_a = TaskStage("A", task)
    stage_b = TaskStage("B", task)
    async_stage_a = TaskStage("A", async_task)
    async_stage_b = TaskStage("B", async_task)

    sync_graph = TaskGraph(name="BenchSync")
    sync_graph.set_stages(stages=[stage_a, stage_b])
    async_graph = TaskGraph(name="BenchAsync")
    async_graph.set_stages(stages=[async_stage_a, async_stage_b])

    # benchmark_graph internally uses clone_graph and returns a result dictionary
    results = await benchmark_graph(
        sync_graph=sync_graph,
        async_graph=async_graph,
        init_tasks_dict={stage_a.get_name(): range(100)},
        graph_modes=["serial", "thread", "async"],
        execution_modes=["serial", "thread", "async"],
    )
    print(results["table"])


asyncio.run(main())
```

## Notes

1. **State independence**: Cloned objects are completely independent from the original (achieved by constructing new instances); modifications do not affect each other
2. **Connection reconstruction**: When cloning a graph, connection relationships between nodes are rebuilt
3. **Function references**: Cloning only copies function references, not the functions themselves
4. **Performance overhead**: Cloning large graphs has some overhead, but is faster than rebuilding from scratch
5. **Configuration fallback**: `clone_stage` only copies parameters accepted by the node class's `__init__`. For a regular `TaskStage`, runtime configurations such as the execution mode will fall back to default values; `TaskRouter` cannot be cloned because of the missing mandatory `router` argument
