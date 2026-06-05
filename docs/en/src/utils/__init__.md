# Utils Module

> 📅 Last Updated: 2026/05/24

The Utils module provides general-purpose utility functions and helper classes for CelestialFlow, including performance benchmarking, data cloning, collection operations, and formatting features. These tools are widely used by other modules, improving code reusability and maintainability.

## File List

| File | Description |
|------|-------------|
| `util_benchmark.py` | Executor and task graph performance benchmarking |
| `util_clone.py` | Executor and task graph deep cloning tools |
| `util_collections.py` | Collection operation tools, provides `cluster_by_value_sorted()` |
| `util_format.py` | Data formatting and display tools (`format_repr`, `format_table`, `format_duration`, `format_timestamp`, `format_avg_time`) |

> **Note**: `util_debug.py` no longer exists in the source code. Do not rely on this file.

## File Descriptions

### Performance Tools

1. **util_benchmark.py**
   - **Purpose**: Executor and task graph performance benchmarking tool, used to compare performance differences across execution modes
   - **Key Functions**:
     - `benchmark_executor()`: Benchmarks `TaskExecutor`, comparing elapsed time across serial/thread/async modes
     - `benchmark_graph()`: Benchmarks `TaskGraph`, comparing different stage_mode × execution_mode combinations
   - **Dependencies**: `util_clone` (clone executor/task graph), `util_format` (output time table)
   - **Use Cases**:
     - Optimizing task execution mode selection
     - Discovering performance bottlenecks
     - Validating parallelization effects

### Data Processing Tools

2. **util_clone.py**
   - **Purpose**: Executor and task graph cloning tool, used to isolate state during benchmarking
   - **Key Functions**: `clone_executor()`, `clone_graph()`
   - **Design**: Creates independent copies via `copy.deepcopy` to avoid state contamination
   - **Supported Types**: `TaskExecutor`, `TaskGraph`
   - **Use Cases**: Benchmarking, state isolation testing

3. **util_collections.py**
   - **Purpose**: Collection operation tools, providing specific data processing functionality
   - **Key Function**: `cluster_by_value_sorted()`: Clusters and sorts a dictionary by value
   - **Key Features**:
     - Group dictionaries by value
     - Sort grouped results
     - Return clustering results sorted by value
   - **Use Cases**: Data analysis, result grouping, statistical summaries, performance metric clustering

4. **util_format.py**
   - **Purpose**: Data formatting and display tools for improved readability
   - **Key Functions**:
     - `format_repr()`: Formats object string representation with maximum length limit
     - `format_table()`: Formats tabular data with alignment and borders
     - `format_duration()`: Formats time intervals (seconds to human-readable format)
     - `format_timestamp()`: Formats timestamps
     - `format_avg_time()`: Formats average processing time
   - **Key Features**: Data beautification, table generation, time formatting, performance metric display
   - **Use Cases**: Log output, performance reports, benchmark result display, debug information formatting

## Module Relationships

### Internal Relationships
- `util_benchmark` depends on `util_clone` (clone executor/task graph) and `util_format` (output tables)
- The remaining tools are independent and can be used standalone

### External Relationships
- **With Runtime Module**: Performance testing tools are used to test executor performance
- **With Stage Module**: Cloning tools are used for executor copy generation
- **With Graph Module**: Cloning tools are used for task graph copy generation; collection tools are used for graph data operations
- **With Persistence Module**: Formatting tools are used for data serialization display

## Design Principles

### Single Responsibility
- Each tool file solves only one category of problems
- Functions are designed to be small and focused, avoiding feature bloat
- Clear interfaces and well-defined responsibilities

### Pure Function Design
- Utility functions are stateless whenever possible
- Avoids global variables and side effects
- Supports concurrent safe usage

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
print(format_duration(123.456))  # "2m 3.46s"
```

## Usage Examples

### Batch Import and Use All Tool Functions

The following example demonstrates how to import all tool modules at once and use each function:

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

# 1. Formatting Tools ----
print("=" * 40)
print("格式化工具示例")
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

# 2. Collection Operations ----
print("\n" + "=" * 40)
print("集合操作示例")
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
    print(f"处理量 {value}: {stages}")
# Output:
#   处理量 50: ['stage_b', 'stage_d']
#   处理量 100: ['stage_a', 'stage_c']
#   处理量 200: ['stage_e']

# 3. Cloning Tools (with Benchmarking) ----
print("\n" + "=" * 40)
print("克隆与基准测试示例")
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
    print(f"原始执行器: {executor.get_name()}")
    print(f"克隆执行器: {cloned.get_name()}")
    print(f"模式一致: {executor.execution_mode == cloned.execution_mode}")

    # Use format_table to display a table
    table = format_table(
        [[100, 0.12], [50, 0.08]],
        row_names=["thread", "serial"],
        column_names=["任务数", "平均耗时(s)"],
    )
    print(f"\n基准测试表格:\n{table}")

    # Run the original executor
    await executor.start(range(100))


asyncio.run(run_benchmark())
```
