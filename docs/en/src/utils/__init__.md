# Utils Module

> 📅 Last Updated: 2026/06/11

The Utils module provides general utility functions and helper classes for CelestialFlow, including performance benchmarking, data cloning, collection operations, and formatting utilities. These utilities are widely used by other modules, improving code reusability and maintainability.

## File List

| File | Description |
|------|-------------|
| `util_benchmark.py` | Executor and task graph performance benchmarking |
| `util_clone.py` | Executor and task graph deep cloning utilities |
| `util_collections.py` | Collection operation utilities, providing `cluster_by_value_sorted()` |
| `util_format.py` | Data formatting and display utilities (`format_repr`, `format_table`, `format_duration`, `format_timestamp`, `format_avg_time`) |

> **Note**: `util_debug.py` no longer exists in the source code. Do not depend on this file.

## File Descriptions

### Performance Utilities

1. **util_benchmark.py**
   - **Purpose**: Executor and task graph performance benchmarking tool, used to compare performance differences across execution modes
   - **Key Functions**:
     - `benchmark_executor()`: Benchmarks sync/async `TaskExecutor`, comparing elapsed time across serial/thread/async modes
     - `benchmark_graph()`: Benchmarks `TaskGraph`, comparing different `stage_mode × execution_mode` combinations
   - **Dependencies**: `util_clone` (clone executor/task graph), `util_format` (output time tables)
   - **Use Cases**: Optimize task execution mode selection, discover performance bottlenecks, validate parallelization effects

### Data Processing Utilities

2. **util_clone.py**
   - **Purpose**: Executor, node, and task graph cloning utilities, used to isolate state in benchmarking
   - **Key Functions**: `clone_executor()`, `clone_stage()`, `clone_graph()`
   - **Design**: Creates independent copies by constructing new instances and copying key parameters, avoiding state contamination
   - **Supported Types**: `TaskExecutor`, `TaskStage`, `TaskGraph`
   - **Use Cases**: Benchmark testing, state isolation testing

3. **util_collections.py**
   - **Purpose**: Collection operation utilities, providing specific data processing functionality
   - **Key Function**: `cluster_by_value_sorted()`: Clusters and sorts dictionaries by value
   - **Key Features**:
     - Groups dictionary entries by value
     - Sorts the grouping results
     - Returns clustering results sorted by value
   - **Use Cases**: Data analysis, result grouping, statistical summaries, performance metric clustering

4. **util_format.py**
   - **Purpose**: Data formatting and display utilities, improving readability
   - **Key Functions**:
     - `format_repr()`: Formats an object's string representation, limiting maximum length
     - `format_table()`: Formats tabular data, supporting alignment and borders
     - `format_duration()`: Formats time intervals (seconds converted to readable format)
     - `format_timestamp()`: Formats timestamps
     - `format_avg_time()`: Formats average processing time
   - **Key Features**: Data beautification, table generation, time formatting, performance metric display
   - **Use Cases**: Log output, performance reports, benchmark result display, debug info formatting

## Module Relationships

### Internal Dependencies
- `util_benchmark` depends on `util_clone` (clone executor/task graph) and `util_format` (output tables)
- The remaining utilities are independent of each other and can be used individually

### External Dependencies
- **With Runtime Module**: Performance testing tools for testing executor performance
- **With Stage Module**: Cloning utilities for generating executor copies
- **With Graph Module**: Cloning utilities for generating task graph copies, collection utilities for graph data operations
- **With Persistence Module**: Formatting utilities for data serialization display

## Design Principles

### Single Responsibility
- Each utility file solves only one category of problems
- Functions are designed small and specialized, avoiding feature bloat
- Clear interfaces and well-defined responsibilities

### Pure Function Design
- Utility functions are stateless whenever possible
- Avoid global variables and side effects
- Support concurrent-safe usage

## Usage Patterns

### Benchmarking
```python
import asyncio
from celestialflow import TaskExecutor
from celestialflow.utils.util_benchmark import benchmark_executor

executor = TaskExecutor("Bench", my_func)
asyncio.run(benchmark_executor(executor, async_executor, range(100)))
```

### Cloning
```python
from celestialflow.utils.util_clone import clone_executor, clone_graph

executor_copy = clone_executor(original_executor)
graph_copy = clone_graph(original_graph)
```

### Collection Operations
```python
from celestialflow.utils.util_collections import cluster_by_value_sorted

grouped = cluster_by_value_sorted({"a": 1, "b": 2, "c": 1})
# {"1": ["a", "c"], "2": ["b"]}
```

### Formatting
```python
from celestialflow.utils.util_format import format_table, format_duration

print(format_table([[2.34, 0.89]], ["serial", "thread"], ["Time"]))
print(format_duration(123))  # "02:03"
```

## Usage Examples

### Batch Import and Use All Utility Functions

The following example demonstrates how to import all utility modules at once and use each function:

```python
import asyncio
from celestialflow import TaskExecutor, format_table
from celestialflow.utils.util_benchmark import benchmark_executor
from celestialflow.utils.util_clone import clone_executor, clone_stage, clone_graph
from celestialflow.utils.util_collections import cluster_by_value_sorted
from celestialflow.utils.util_format import (
    format_repr,
    format_duration,
    format_timestamp,
    format_avg_time,
)

# 1. Formatting utilities ----
print("=" * 40)
print("Formatting utility examples")
print("=" * 40)

# format_duration: seconds -> readable time
print(f"format_duration(75): {format_duration(75)}")     # 01:15
print(f"format_duration(3661): {format_duration(3661)}") # 01:01:01

# format_timestamp: timestamp -> date string
import time
print(f"format_timestamp(now): {format_timestamp(time.time())}")

# format_avg_time: average processing time
print(f"format_avg_time(12.5, 100): {format_avg_time(12.5, 100)}")  # 0.12s/it
print(f"format_avg_time(2.0, 1): {format_avg_time(2.0, 1)}")       # 2.00s/it

# format_repr: safe truncation
print(f"format_repr('hello'*10, 15): {format_repr('hello'*10, 15)}")

# 2. Collection operations ----
print("\n" + "=" * 40)
print("Collection operation examples")
print("=" * 40)

task_results = {
    "stage_a": 100,
    "stage_b": 50,
    "stage_c": 100,
    "stage_d": 50,
    "stage_e": 200,
}
clustered = cluster_by_value_sorted(task_results)
for value, stages in clustered.items():
    print(f"Throughput {value}: {stages}")
# Output:
#   Throughput 50: ['stage_b', 'stage_d']
#   Throughput 100: ['stage_a', 'stage_c']
#   Throughput 200: ['stage_e']

# 3. Cloning utilities (with benchmarking) ----
print("\n" + "=" * 40)
print("Cloning and benchmarking examples")
print("=" * 40)


def simple_task(x: int) -> int:
    return x * x


async def run_benchmark():
    executor = TaskExecutor(
        "Bench",
        simple_task,
        execution_mode="thread",
        max_workers=4,
    )

    # Clone executor for isolated state testing
    cloned = clone_executor(executor)
    print(f"Original executor: {executor.get_name()}")
    print(f"Cloned executor: {cloned.get_name()}")
    print(f"Modes match: {executor.execution_mode == cloned.execution_mode}")

    # Use format_table to display a table
    table = format_table(
        [[100, 0.12], [50, 0.08]],
        row_names=["thread", "serial"],
        column_names=["Task Count", "Avg Time (s)"],
    )
    print(f"\nBenchmark table:\n{table}")

    # Run the original executor
    await executor.start(range(100))


asyncio.run(run_benchmark())
```
