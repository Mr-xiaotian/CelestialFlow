# Benchmark

> 📅 Last updated: 2026/05/11

`utils/benchmark.py` provides performance benchmarking functionality for executors and task graphs, used to compare performance differences across execution modes.

## Design Purpose

In real-world projects, choosing the right execution mode is critical for performance. The benchmarking tool can:
- Compare execution times across different modes
- Verify parallelization effectiveness
- Identify performance bottlenecks

## Main Functions

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
    Benchmark an executor.

    :param sync_executor: Synchronous executor template
    :param async_executor: Asynchronous executor template
    :param task_source: Task source
    :param sync_modes: Synchronous mode list, defaults to ["serial", "thread"]
    :param async_modes: Asynchronous mode list, defaults to ["async"]
    :return: Test results dictionary
    """
```

Output example:
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
    Benchmark a task graph.

    :param sync_graph: Synchronous task graph template (for serial/thread modes)
    :param async_graph: Asynchronous task graph template (for async mode)
    :param init_tasks_dict: Initial tasks dictionary
    :param stage_modes: Stage mode list, defaults to ["serial", "thread"]
    :param execution_sync_modes: Synchronous execution mode list, defaults to ["serial", "thread"]
    :param execution_async_modes: Asynchronous execution mode list, defaults to ["async"]
    :return: Test results dictionary
    """
```

Output example:
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
from celestialflow.utils.benchmark import benchmark_executor

# Define a synchronous task
def sync_task(x):
    return x * 2

# Define an asynchronous task
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
from celestialflow.utils.benchmark import benchmark_graph

# Create sync stages
stage_a = TaskStage("A", process_a)
stage_b = TaskStage("B", process_b)

# Create async stages
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
| `serial` | Single-threaded serial execution |
| `thread` | Thread pool concurrent execution |
| `async` | Coroutine asynchronous execution |

### Task Graph Test Dimensions

**Stage Mode**:
- `serial`: Stage runs in the main thread
- `thread`: Stage runs in a separate thread

**Execution Mode**:
- `serial`: Serial execution within a stage
- `thread`: Thread pool execution within a stage
- `async`: Coroutine async execution within a stage

Combination example:
| Stage \ Execution | serial | thread | async |
|-------------------|--------|--------|-------|
| serial | S-S | S-T | S-A |
| thread | T-S | T-T | T-A |

## Output Information

### Time Table

Displays execution time for each configuration.

### Failure Statistics

If any tasks fail, the following is output:
- `Fail stage dict`: Failed tasks grouped by stage
- `Fail error dict`: Failed tasks grouped by error type

## Notes

1. **Cloning Mechanism**: Each test clones the original object to avoid state contamination
2. **Fixed Tasks**: All tests use the same task list to ensure fairness
3. **Resource Contention**: Thread mode may be affected by resource contention; multiple test runs are recommended
4. **Async Requirement**: `benchmark_executor` is an async function and requires `await` or `asyncio.run`
5. **Separate Graphs**: `benchmark_graph` requires separate sync and async graphs because async execution mode needs async functions
