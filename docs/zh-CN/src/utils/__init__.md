# Utils 模块

> 📅 最后更新日期: 2026/06/22

Utils 模块提供了 CelestialFlow 的通用工具函数和辅助类，包括性能基准测试、数据克隆、集合操作和格式化功能。这些工具被其他模块广泛使用，提高了代码的复用性和可维护性。

## 文件列表

| 文件 | 说明 |
|------|------|
| `util_benchmark.py` | 执行器与任务图性能基准测试 |
| `util_clone.py` | 执行器与任务图深度克隆工具 |
| `util_collections.py` | 集合操作工具，提供 `cluster_by_value_sorted()` |
| `util_format.py` | 数据格式化和展示工具（`format_repr`, `format_table`, `format_duration`, `format_timestamp`, `format_avg_time`） |

> **注意**: `util_debug.py` 已不存在于源码中，请不要依赖该文件。

## 文件说明

### 性能工具

1. **util_benchmark.py**
   - **作用**: 执行器与任务图性能基准测试工具，用于对比不同执行模式的性能差异
   - **关键函数**:
     - `benchmark_executor()`: 对同步/异步 `TaskExecutor` 进行基准测试，对比 serial/thread/async 模式的耗时
     - `benchmark_graph()`: 对 `TaskGraph` 进行基准测试，对比不同 stage_mode × execution_mode 组合
   - **依赖**: `util_clone`（克隆执行器/任务图）、`util_format`（输出时间表格）
   - **使用场景**: 优化任务执行模式选择、发现性能瓶颈、验证并行化效果

### 数据处理工具

2. **util_clone.py**
   - **作用**: 执行器、节点和任务图克隆工具，用于在基准测试中隔离状态
   - **关键函数**: `clone_executor()`, `clone_stage()`, `clone_graph()`
   - **设计**: 通过构造新实例并复制关键参数创建独立副本，避免状态污染
   - **支持类型**: `TaskExecutor`, `TaskStage`, `TaskGraph`
   - **使用场景**: 基准测试、状态隔离测试

3. **util_collections.py**
   - **作用**: 集合操作工具，提供特定的数据处理功能
   - **关键函数**: `cluster_by_value_sorted()`: 根据值对字典进行聚类和排序
   - **关键功能**:
     - 将字典按值分组
     - 对分组结果进行排序
     - 返回按值排序的聚类结果
   - **使用场景**: 数据分析、结果分组、统计汇总、性能指标聚类

4. **util_format.py**
   - **作用**: 数据格式化和展示工具，提高可读性
   - **关键函数**:
     - `format_repr()`: 格式化对象的字符串表示，限制最大长度
     - `format_table()`: 格式化表格数据，支持对齐和边框
     - `format_duration()`: 格式化时间间隔（秒转换为可读格式）
     - `format_timestamp()`: 格式化时间戳
     - `format_avg_time()`: 格式化平均处理时间
   - **关键功能**: 数据美化、表格生成、时间格式化、性能指标展示
   - **使用场景**: 日志输出、性能报告、基准测试结果展示、调试信息格式化

## 模块关联

### 内部关联
- `util_benchmark` 依赖 `util_clone`（克隆执行器/任务图）和 `util_format`（输出表格）
- 其余工具相互独立，可单独使用

### 外部关联
- **与 Runtime 模块**: 性能测试工具用于测试执行器性能
- **与 Stage 模块**: 克隆工具用于执行器副本生成
- **与 Graph 模块**: 克隆工具用于任务图副本生成，集合工具用于图数据操作
- **与 Persistence 模块**: 格式化工具用于数据序列化展示

## 设计原则

### 单一职责
- 每个工具文件只解决一类问题
- 函数设计小而专，避免功能膨胀
- 清晰的接口和明确的职责

### 纯函数设计
- 工具函数尽可能无状态
- 避免全局变量和副作用
- 支持并发安全使用

## 使用模式

### 基准测试
```python
import asyncio
from celestialflow import TaskExecutor
from celestialflow.utils.util_benchmark import benchmark_executor


def sync_task(x: int) -> int:
    return x * 2


async def async_task(x: int) -> int:
    await asyncio.sleep(0.001)
    return x * 2


sync_executor = TaskExecutor("SyncBench", sync_task)
async_executor = TaskExecutor("AsyncBench", async_task)
asyncio.run(benchmark_executor(sync_executor, async_executor, range(100)))
```

### 克隆
```python
from celestialflow.utils.util_clone import clone_executor, clone_graph

executor_copy = clone_executor(original_executor)
graph_copy = clone_graph(original_graph)
```

### 集合操作
```python
from celestialflow.utils.util_collections import cluster_by_value_sorted

grouped = cluster_by_value_sorted({"a": 1, "b": 2, "c": 1})
# {1: ["a", "c"], 2: ["b"]}
```

### 格式化
```python
from celestialflow.utils.util_format import format_table, format_duration

print(format_table([[2.34, 0.89]], ["serial", "thread"], ["Time"]))
print(format_duration(123))  # "02:03"
```

## 使用示例

### 批量导入并使用所有工具函数

以下示例展示如何一次性导入所有工具模块并使用各个函数：

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

# 1. 格式化工具 ----
print("=" * 40)
print("格式化工具示例")
print("=" * 40)

# format_duration: 秒 -> 可读时间
print(f"format_duration(75): {format_duration(75)}")     # 01:15
print(f"format_duration(3661): {format_duration(3661)}") # 01:01:01

# format_timestamp: 时间戳 -> 日期字符串
import time
print(f"format_timestamp(now): {format_timestamp(time.time())}")

# format_avg_time: 平均耗时
print(f"format_avg_time(12.5, 100): {format_avg_time(12.5, 100)}")  # 0.12s/it
print(f"format_avg_time(2.0, 1): {format_avg_time(2.0, 1)}")       # 2.00s/it

# format_repr: 安全截断
print(f"format_repr('hello'*10, 15): {format_repr('hello'*10, 15)}")

# 2. 集合操作 ----
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
# 输出：
#   处理量 50: ['stage_b', 'stage_d']
#   处理量 100: ['stage_a', 'stage_c']
#   处理量 200: ['stage_e']

# 3. 克隆工具（配合基准测试）----
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

    # 克隆执行器用于隔离的状态测试
    cloned = clone_executor(executor)
    print(f"原始执行器: {executor.get_name()}")
    print(f"克隆执行器: {cloned.get_name()}")
    print(f"模式一致: {executor.execution_mode == cloned.execution_mode}")

    # 使用 format_table 展示表格
    table = format_table(
        [[100, 0.12], [50, 0.08]],
        row_names=["thread", "serial"],
        column_names=["任务数", "平均耗时(s)"],
    )
    print(f"\n基准测试表格:\n{table}")

    # 运行原始执行器
    executor.start(range(100))


asyncio.run(run_benchmark())
```
