# Benchmark

> 📅 Last Updated: 2026/05/24

`utils/util_benchmark.py` provides performance benchmarking functionality for executors and task graphs, used to compare performance differences across execution modes.

## Design Purpose

In real projects, choosing the right execution mode is critical for performance. The benchmarking tool can:
- Compare elapsed time across different execution modes
- Validate parallelization effects
- Discover performance bottlenecks

## Key Functions

### benchmark_executor

Benchmarks a `TaskExecutor`.

```python
async def benchmark_executor(
    sync_executor: TaskExecutor,
    async_executor: TaskExecutor,
    task_source: Iterable,
    sync_modes: list[str] | None = None,
    async_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    Benchmarks an executor.

    :param sync_executor: Sync executor template
    :param async_executor: Async executor template
    :param task_source: Task source
    :param sync_modes: List of sync modes, default ["serial", "thread"]
    :param async_modes: List of async modes, default ["async"]
    :return: Test result dict (contains use_time, sync_modes, async_modes, table)
    """
```

Test flow:
1. Clone the executor (avoid state contamination)
2. Set the execution mode for each mode
3. Execute tasks and measure time
4. Output time table and result table

Sample output:
```
           Time
serial     2.34s
thread     0.89s
async      0.67s
```

### benchmark_graph

Benchmarks a `TaskGraph`.

```python
def benchmark_graph(
    sync_graph: TaskGraph,
    async_graph: TaskGraph,
    init_tasks_dict: Mapping[str, Iterable],
    stage_modes: list[str] | None = None,
    execution_sync_modes: list[str] | None = None,
    execution_async_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    Benchmarks a task graph.

    :param sync_graph: Sync task graph template (for serial/thread modes)
    :param async_graph: Async task graph template (for async mode)
    :param init_tasks_dict: Initial task dictionary
    :param stage_modes: List of node modes, default ["serial", "thread"]
    :param execution_sync_modes: List of sync execution modes, default ["serial", "thread"]
    :param execution_async_modes: List of async execution modes, default ["async"]
    :return: Test result dict (contains table, stage_modes, sync_modes, async_modes)
    """
```

Test flow:
1. For each `stage_mode × execution_mode` combination
2. Clone the task graph
3. Set `set_graph_mode(stage_mode, execution_mode)`
4. Execute `start_graph()` and measure time
5. Output time table

Sample output:
```
Time table:
          serial    thread    async
serial    5.23s     3.45s     3.21s
thread    2.12s     1.89s     1.65s
```

## Usage Examples

### Testing an Executor

```python
import asyncio
from celestialflow import TaskExecutor
from celestialflow.utils.util_benchmark import benchmark_executor

# Define sync task
def sync_task(x):
    return x * 2

# Define async task
async def async_task(x):
    await asyncio.sleep(0.01)
    return x * 2

# Create executors
sync_executor = TaskExecutor("SyncBench", sync_task)
async_executor = TaskExecutor("AsyncBench", async_task)

# Run benchmark
asyncio.run(benchmark_executor(
    sync_executor=sync_executor,
    async_executor=async_executor,
    task_source=range(1000),
))
```

### Testing a Task Graph

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.utils.util_benchmark import benchmark_graph

# Create sync nodes
stage_a = TaskStage("A", process_a)
stage_b = TaskStage("B", process_b)

# Create async nodes
async_stage_a = TaskStage("A", async_process_a)
async_stage_b = TaskStage("B", async_process_b)

# Build sync graph
sync_graph = TaskGraph()
sync_graph.set_stages(stages=[stage_a, stage_b])
sync_graph.connect([stage_a], [stage_b])

# Build async graph
async_graph = TaskGraph()
async_graph.set_stages(stages=[async_stage_a, async_stage_b])
async_graph.connect([async_stage_a], [async_stage_b])

# Run benchmark
benchmark_graph(
    sync_graph=sync_graph,
    async_graph=async_graph,
    init_tasks_dict={stage_a.get_tag(): range(100)},
)
```

## Test Matrix

### Executor Test Dimensions

| Dimension | Description |
|-----------|-------------|
| `serial` | Single-threaded sequential execution |
| `thread` | Thread pool concurrent execution |
| `async` | Coroutine-based asynchronous execution |

### Task Graph Test Dimensions

**Stage Mode**:
- `serial`: Node runs on the main thread
- `thread`: Node runs on an independent thread

**Execution Mode**:
- `serial`: Sequential execution within the node
- `thread`: Thread pool execution within the node
- `async`: Coroutine-based async execution within the node

Combination examples:
| Stage \ Execution | serial | thread | async |
|-------------------|--------|--------|-------|
| serial | S-S | S-T | S-A |
| thread | T-S | T-T | T-A |

## Output Information

### Time Table

Displays the execution time for each configuration.

### Result Table

Displays the successful result pairs for each configuration.

### Return Value

`benchmark_executor` returns a dict containing:
- `use_time`: List of elapsed times for each mode
- `sync_modes`: List of sync modes tested
- `async_modes`: List of async modes tested
- `table`: Formatted time table string

`benchmark_graph` returns a dict containing:
- `table`: Formatted time table string
- `stage_modes`: List of node modes tested
- `sync_modes` / `async_modes`: List of execution modes tested

## Notes

1. **Cloning mechanism**: Each test clones the original object to avoid state contamination
2. **Fixed tasks**: All tests use the same task list to ensure fairness
3. **Resource contention**: Thread mode results may be affected by resource contention; multiple tests are recommended
4. **Async requirement**: `benchmark_executor` is an async function, requiring `await` or `asyncio.run`
5. **Graph separation**: `benchmark_graph` requires separate sync_graph and async_graph, since async execution mode requires async functions
