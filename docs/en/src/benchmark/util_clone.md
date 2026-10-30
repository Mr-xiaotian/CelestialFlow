# src/celestialflow/benchmark/util_clone.py

> 📅 Last Updated: 2026/10/30

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

Copied attributes (collected by the internal `_get_clone_init_kwargs()` and then passed to `TaskExecutor(**kwargs)`):
- `name`: Executor name
- `func`: Task function (only the reference is copied, no deep copy)
- `execution_mode`: Execution mode
- `max_workers`: Concurrency limit
- `max_retries`: Max retry count
- `max_info`: Max log info length
- `retry_exceptions`: List of retryable exceptions (copied after construction via `set_retry_exceptions(*executor.retry_exceptions)`)

**Configuration that is not copied** (the clone reverts to the constructor defaults):
- `max_queue_size` (default `0`, unlimited)
- `skip_func` (default `None`, skip no tasks)
- Already-registered observers (the `Observer` / `ObserverHub` registered via `add_observer()`)

### clone_graph

Clones a `TaskGraph` instance.

```python
def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    Clone a task graph.

    This tool is intended only for benchmark scenarios, so it only supports task
    graphs composed of ``TaskExecutor``, and directly reuses
    :func:`clone_executor` to clone all nodes.

    The clone does not carry the observers of the original graph / nodes:
    ``clone_executor`` creates brand-new instances, and sharing an observer with
    counters would cause duplicate counting.

    :param graph: The task graph to clone
    :return: The cloned task graph
    :raises ConfigurationError: Raised when the graph contains non-``TaskExecutor`` nodes
    """
```

Cloning flow:
1. Starting from the source nodes (`graph.get_source_nodes()`), traverse the original graph via BFS (breadth-first) in the out-edge order of `graph.order_graph.out_edges` to collect all nodes
2. Perform an `isinstance(node, TaskExecutor)` check on each node; if specialized nodes such as `TaskSplitter` / `TaskRouter` are encountered, immediately raise `ConfigurationError`
3. Clone each node and build a mapping from the original node name to the cloned node
4. Register all cloned nodes via `set_nodes()` and rebuild the connection relationships between nodes with `connect()`
5. Copy graph configuration (`name`, `graph_mode`)
6. Copy the CelestialTree event client (cloned via `clone_event_client(graph.ctree_client)`)

> ⚠️ After cloning, the key order of `node_dict` becomes BFS order (source nodes first), no longer the original graph's node registration order.

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
stage_a = TaskExecutor("A", process_a)
stage_b = TaskExecutor("B", process_b)
graph.set_nodes(nodes=[stage_a, stage_b])
graph.connect([stage_a], [stage_b])

# Clone the graph for testing
cloned_graph = clone_graph(graph)

# Run the cloned graph
init_tasks = {stage_a.get_name(): [1, 2, 3]}
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
    stage_a = TaskExecutor("A", task)
    stage_b = TaskExecutor("B", task)
    async_stage_a = TaskExecutor("A", async_task)
    async_stage_b = TaskExecutor("B", async_task)

    sync_graph = TaskGraph(name="BenchSync")
    sync_graph.set_nodes(nodes=[stage_a, stage_b])
    async_graph = TaskGraph(name="BenchAsync")
    async_graph.set_nodes(nodes=[async_stage_a, async_stage_b])

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
2. **Connection reconstruction**: When cloning a graph, connection relationships between nodes are rebuilt, but the key order of `node_dict` becomes BFS order
3. **Function references**: Cloning only copies function references, not the functions themselves
4. **Configuration loss**: `clone_executor` does not copy `max_queue_size`, `skip_func`, or already-registered observers; `clone_graph` reuses `clone_executor`, so nodes in the cloned graph likewise lose these configurations (losing observers also avoids duplicate counter accumulation)
5. **Performance overhead**: Cloning large graphs has some overhead, but is faster than rebuilding from scratch
6. **Internal tool**: `clone_executor` / `clone_graph` are internal benchmark utilities, not in the top-level package entry's `__all__`; their signatures / semantics may change as the internal benchmark implementation evolves
7. **Node type limitation**: `clone_graph` only supports `TaskExecutor` nodes; encountering specialized nodes such as `TaskSplitter` / `TaskRouter` will raise `ConfigurationError`, and **does not** preserve the type or behavior of those subclasses
