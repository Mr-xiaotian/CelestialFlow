# Benchmark

> 📅 最后更新日期: 2026/08/17

`benchmark/util_benchmark.py` 提供了执行器和任务图的性能基准测试功能，用于对比不同执行模式的性能差异。

## 设计目的

在实际项目中，选择合适的执行模式对性能至关重要。基准测试工具可以：
- 对比不同执行模式的耗时
- 验证并行化效果
- 发现性能瓶颈

## 主要函数

### benchmark_executor

对 `TaskExecutor` 进行基准测试。

```python
async def benchmark_executor(
    sync_executor: TaskExecutor[Any, Any],
    async_executor: TaskExecutor[Any, Any],
    task_source: Iterable[Any],
    execution_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对执行器进行基准测试。

    :param sync_executor: 同步执行器模板（用于 serial/thread execution_mode）
    :param async_executor: 异步执行器模板（用于 async execution_mode）
    :param task_source: 任务源，用于生成任务列表
    :param execution_modes: 执行模式列表，默认 ["serial", "thread", "async"]
    :return: 测试结果字典（含 use_time, execution_modes, table）
    """
```

测试流程：
1. 克隆执行器（避免状态污染）
2. 遍历 `execution_modes`
3. `serial/thread` 使用 `sync_executor.start()`，`async` 使用 `async_executor.start_async()`
4. 输出时间表格

输出示例：
```
           Time
serial     2.34s
thread     0.89s
async      0.67s
```

### benchmark_graph

对 `TaskGraph` 进行基准测试。

```python
async def benchmark_graph(
    sync_graph: TaskGraph,
    async_graph: TaskGraph,
    init_tasks_dict: Mapping[str, Iterable[Any]],
    graph_modes: list[str] | None = None,
    execution_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对任务图进行基准测试。

    :param sync_graph: 同步任务图模板（用于 serial/thread execution_mode）
    :param async_graph: 异步任务图模板（用于 async execution_mode）
    :param init_tasks_dict: 初始任务字典，键为任务标签，值为任务列表
    :param graph_modes: 图执行模式列表，默认 ["serial", "thread", "async"]
    :param execution_modes: 执行模式列表，默认 ["serial", "thread", "async"]
    :return: 测试结果字典（含 use_time, table, graph_modes, execution_modes）
    """
```

测试流程：
1. 对每种 `graph_mode` × `execution_mode` 组合
2. 克隆任务图
3. 设置 `set_graph_mode(graph_mode)` 与 `set_stage_execution_mode(execution_mode)`
4. `graph_mode="async"` 时执行 `run_async()`；其余图模式执行 `run()`
5. `serial/thread + async` 组合在基准函数内部通过 `asyncio.to_thread(...)` 启动，避免与 `benchmark_graph()` 自身的事件循环冲突
5. 输出时间表格

输出示例：
```
Time table:
| graph/execution | serial | thread | async |
|-----------------|--------|--------|-------|
| serial          | 5.23s  | 3.45s  | 3.21s |
| thread          | 2.12s  | 1.89s  | 1.65s |
| async           | 2.05s  | 1.73s  | 1.42s |
```

## 使用示例

### 测试执行器

```python
import asyncio
from celestialflow import TaskExecutor
from celestialflow.benchmark.util_benchmark import benchmark_executor


# 定义同步任务
def sync_task(x):
    return x * 2


# 定义异步任务
async def async_task(x):
    await asyncio.sleep(0.01)
    return x * 2


# 创建执行器
sync_executor = TaskExecutor("SyncBench", sync_task)
async_executor = TaskExecutor("AsyncBench", async_task)

# 运行基准测试
asyncio.run(
    benchmark_executor(
        sync_executor=sync_executor,
        async_executor=async_executor,
        task_source=range(1000),
        execution_modes=["serial", "thread", "async"],
    )
)
```

### 测试任务图

```python
import asyncio
from celestialflow import TaskGraph, TaskStage
from celestialflow.benchmark.util_benchmark import benchmark_graph


def process_a(x: int) -> int:
    return x * 2


def process_b(x: int) -> int:
    return x + 1


async def async_process_a(x: int) -> int:
    return x * 2


async def async_process_b(x: int) -> int:
    return x + 1


# 创建同步节点
stage_a = TaskStage("A", process_a)
stage_b = TaskStage("B", process_b)

# 创建异步节点
async_stage_a = TaskStage("A", async_process_a)
async_stage_b = TaskStage("B", async_process_b)

# 构建同步图
sync_graph = TaskGraph(name="SyncGraph")
sync_graph.set_stages(stages=[stage_a, stage_b])
sync_graph.connect([stage_a], [stage_b])

# 构建异步图
async_graph = TaskGraph(name="AsyncGraph")
async_graph.set_stages(stages=[async_stage_a, async_stage_b])
async_graph.connect([async_stage_a], [async_stage_b])

# 运行基准测试（benchmark_graph 已改为 async 函数，需要 await）
asyncio.run(
    benchmark_graph(
        sync_graph=sync_graph,
        async_graph=async_graph,
        init_tasks_dict={stage_a.get_name(): range(100)},
    )
)
```

## 测试矩阵

### 执行器测试维度

| 维度 | 说明 |
|------|------|
| `serial` | 单线程串行执行 |
| `thread` | 线程池并发执行 |
| `async` | 协程异步执行 |

### 任务图测试维度

**Graph Mode (图模式)**：
- `serial`: 节点在主线程运行
- `thread`: 节点在独立线程运行
- `async`: 图在事件循环中统一调度；同步节点转入线程执行，异步节点直接协程执行

**Execution Mode (执行模式)**：
- `serial`: 节点内部串行执行
- `thread`: 节点内部线程池执行
- `async`: 节点内部协程异步执行

组合示例：
| Graph \ Execution | serial | thread | async |
|-------------------|--------|--------|-------|
| serial | S-S | S-T | S-A |
| thread | T-S | T-T | T-A |
| async  | A-S | A-T | A-A |

## 输出信息

### 时间表格

显示每种配置的执行时间。

### 返回值

`benchmark_executor` 返回包含以下内容的字典：
- `use_time`: 各模式的耗时列表
- `execution_modes`: 测试的执行模式列表
- `table`: 格式化后的时间表格字符串

`benchmark_graph` 返回包含以下内容的字典：
 - `use_time`: 3×3（或自定义维度）的耗时矩阵
- `table`: 格式化后的时间表格字符串
 - `graph_modes`: 测试的图模式列表
 - `execution_modes`: 时间表格的完整列顺序

## 注意事项

1. **克隆机制**: 每次测试都会克隆原始对象，避免状态污染
2. **任务固定**: 所有测试使用相同的任务列表，保证公平性
3. **资源竞争**: 线程模式可能因资源竞争影响结果，建议多次测试
4. **异步要求**: `benchmark_executor` 和 `benchmark_graph` 都是异步函数，需要 `await` 或 `asyncio.run`
5. **模板分离**: `benchmark_executor` 与 `benchmark_graph` 都需要分别提供同步/异步模板，因为 `execution_mode="async"` 需要 async 函数
6. **矩阵完整性**: `benchmark_graph` 当前实现默认覆盖 `serial/thread/async × serial/thread/async` 的 9 种组合
