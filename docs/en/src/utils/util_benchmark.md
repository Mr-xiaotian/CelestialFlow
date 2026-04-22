# Benchmark

> 📅 Last updated: 2026/04/22

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
    :param sync_modes: Synchronous mode list, defaults to ["serial", "thread", "process"]
    :param async_modes: Asynchronous mode list, defaults to ["async"]
    :return: Test results dictionary
    """
```

Output example:
```
           Time
serial     2.34s
thread     0.89s
process    0.45s
async      0.67s
```

### benchmark_graph

Benchmarks a `TaskGraph`.

```python
def benchmark_graph(
    graph: TaskGraph,
    init_tasks_dict: dict[str, Iterable],
    stage_modes: list[str] | None = None,
    execution_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    Benchmark a task graph.

    :param graph: Task graph template
    :param init_tasks_dict: Initial tasks dictionary
    :param stage_modes: Stage mode list, defaults to ["serial", "thread", "process"]
    :param execution_modes: Execution mode list, defaults to ["serial", "thread"]
    :return: Test results dictionary
    """
```

Output example:
```
Time table:
          serial    thread
serial    5.23s     3.45s
process   2.12s     1.89s

Fail stage dict: {}
Fail error dict: {}
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
sync_executor = TaskExecutor(func=sync_task)
async_executor = TaskExecutor(func=async_task)

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

# Create stages
stage_a = TaskStage(func=process_a, execution_mode="thread", stage_mode="process", stage_name="A")
stage_b = TaskStage(func=process_b, execution_mode="thread", stage_mode="process", stage_name="B")

# Build graph
graph = TaskGraph()
graph.set_stages(root_stages=[stage_a], stages=[stage_b])
graph.connect([stage_a], [stage_b])

# Run benchmark
benchmark_graph(
    graph=graph,
    init_tasks_dict={stage_a.get_tag(): range(100)},
    stage_modes=["serial", "thread", "process"],
    execution_modes=["serial", "thread"],
)
```

## Test Matrix

### Executor Test Dimensions

| Dimension | Description |
|-----------|-------------|
| `serial` | Single-threaded serial execution |
| `thread` | Thread pool concurrent execution |
| `process` | Process pool parallel execution |
| `async` | Coroutine asynchronous execution |

### Task Graph Test Dimensions

**Stage Mode**:
- `serial`: Stage runs in the main process
- `process`: Stage runs in a separate process

**Execution Mode**:
- `serial`: Serial execution within a stage
- `thread`: Thread pool execution within a stage

Combination example:
| Stage \ Execution | serial | thread |
|-------------------|--------|--------|
| serial | S-S | S-T |
| process | P-S | P-T |

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
3. **Resource Contention**: Process mode may be affected by resource contention; multiple test runs are recommended
4. **Async Requirement**: `benchmark_executor` is an async function and requires `await` or `asyncio.run`
