# benchmark/util_clone.py

> 📅 Last Updated: 2026/09/09

`benchmark/util_clone.py` provides functionality for cloning executors and task graphs, used for performance testing and configuration reuse.

> ⚠️ This file defines internal benchmark utility functions, **not public API**. `clone_executor` / `clone_graph` are not exported from the top-level `celestialflow` package entry point; if needed, access them directly via `from celestialflow.benchmark.util_clone import ...`.

## Design Purpose

In performance testing, the same task graph configuration needs to be run multiple times, but each run modifies internal state. The cloning functionality creates completely independent copies, avoiding state contamination.

## Main Functions

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

### clone_graph

Clones a `TaskGraph` instance.

```python
def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    Clone a task graph.

    This tool is intended only for benchmark scenarios, so it only supports task
    graphs composed of ``TaskExecutor``, and directly reuses
    :func:`clone_executor` to clone all nodes.

    :param graph: The task graph to clone
    :return: The cloned task graph
    :raises ConfigurationError: Raised when the graph contains non-``TaskExecutor`` nodes
    """
```

Cloning flow:
1. Starting from the source node, traverse the original graph via BFS (breadth-first) in the out-edge order of `graph.order_graph.out_edges` to collect all nodes
2. Assert that every node is a `TaskExecutor`; if specialized nodes such as `TaskSplitter` / `TaskRouter` are encountered, immediately raise `ConfigurationError`
3. Clone each node and build a mapping from the original node name to the cloned node
4. Register all cloned nodes via `set_nodes()` and rebuild the connection relationships between nodes with `connect()`
5. Copy graph configuration (`name`, `graph_mode`)
6. Copy the CelestialTree (`clone_event_client`) and Reporter configuration (`NullTaskReporter` / `TaskReporter` can be cloned; other types raise `ConfigurationError`)

> ⚠️ **`clone_graph` does not guarantee preservation of all node types**: only `TaskExecutor` nodes will be cloned as the same type; specialized nodes such as `TaskSplitter` / `TaskRouter` will neither be cloned as the same subclass, nor will their split / route behavior be preserved. This tool is an internal benchmark utility, and only applies to task graphs that "consist entirely of `TaskExecutor` and are used for benchmarking".

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

### Cloning a Task Graph

```python
from celestialflow import TaskGraph, TaskExecutor
from celestialflow.benchmark.util_clone import clone_graph


def process_a(x: int) -> int:
    return x * 2


def process_b(x: int) -> int:
    return x + 1


# Create the original graph
graph = TaskGraph(name="CloneDemo", graph_mode="thread")
node_a = TaskExecutor("A", process_a)
node_b = TaskExecutor("B", process_b)
graph.set_nodes(nodes=[node_a, node_b])
graph.connect([node_a], [node_b])

# Clone the graph for testing
cloned_graph = clone_graph(graph)

# Run the cloned graph
init_tasks = {node_a.get_name(): [1, 2, 3]}
cloned_graph.run(init_tasks)
```

## Comprehensive Example

The following example demonstrates a complete scenario using `clone_executor` and `clone_graph` together:

```python
import asyncio
from celestialflow import TaskExecutor, TaskGraph
from celestialflow.benchmark.util_clone import clone_executor, clone_graph


def square(x: int) -> int:
    return x * x


def add_one(x: int) -> int:
    return x + 1


async def main():
    # 1. clone_executor ----
    executor = TaskExecutor("Square", square, execution_mode="thread", max_workers=4)
    cloned_exe = clone_executor(executor)
    print(f"clone_executor: mode={cloned_exe.execution_mode}")

    # 2. clone_graph ----
    graph = TaskGraph(name="CloneDemo", graph_mode="thread")
    a = TaskExecutor("A", square, execution_mode="thread")
    b = TaskExecutor("B", add_one, execution_mode="thread")
    graph.set_nodes([a, b])
    graph.connect([a], [b])

    cloned_grp = clone_graph(graph)
    print(f"clone_graph: graph mode={cloned_grp.graph_mode}")
    print(
        f"Connection consistency: {graph.order_graph.out_edges == cloned_grp.order_graph.out_edges}"
    )

    # Run original and cloned graphs separately; states are completely independent
    graph.run({a.get_name(): [1, 2, 3]})
    cloned_grp.run({list(cloned_grp.node_dict.keys())[0]: [10, 20]})


asyncio.run(main())
```

### Using in Benchmarking

```python
import asyncio
from celestialflow import TaskGraph, TaskExecutor
from celestialflow.benchmark.util_benchmark import benchmark_graph


def task(x: int) -> int:
    return x * 2


async def async_task(x: int) -> int:
    return x * 2


async def main():
    node_a = TaskExecutor("A", task)
    node_b = TaskExecutor("B", task)
    async_node_a = TaskExecutor("A", async_task)
    async_node_b = TaskExecutor("B", async_task)

    sync_graph = TaskGraph(name="BenchSync")
    sync_graph.set_nodes(nodes=[node_a, node_b])
    async_graph = TaskGraph(name="BenchAsync")
    async_graph.set_nodes(nodes=[async_node_a, async_node_b])

    # benchmark_graph internally uses clone_graph and returns a result dictionary
    results = await benchmark_graph(
        sync_graph=sync_graph,
        async_graph=async_graph,
        init_tasks_dict={node_a.get_name(): range(100)},
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
5. **Internal tool**: `clone_executor` / `clone_graph` are internal benchmark utilities, not in the top-level package entry's `__all__`; their signatures / semantics may change as the internal benchmark implementation evolves
6. **Node type limitation**: `clone_graph` only supports `TaskExecutor` nodes; encountering specialized nodes such as `TaskSplitter` / `TaskRouter` will raise `ConfigurationError`, and **does not** preserve the type or behavior of those subclasses
