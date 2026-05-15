# Benchmark

> 📅 最后更新日期: 2026/05/15

`utils/benchmark.py` 提供了执行器和任务图的性能基准测试功能，用于对比不同执行模式的性能差异。

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
    sync_executor: TaskExecutor,
    async_executor: TaskExecutor,
    task_source: Iterable,
    sync_modes: list[str] | None = None,
    async_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对执行器进行基准测试。

    :param sync_executor: 同步执行器模板
    :param async_executor: 异步执行器模板
    :param task_source: 任务源
    :param sync_modes: 同步模式列表，默认 ["serial", "thread"]
    :param async_modes: 异步模式列表，默认 ["async"]
    :return: 测试结果字典
    """
```

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
def benchmark_graph(
    sync_graph: TaskGraph,
    async_graph: TaskGraph,
    init_tasks_dict: Mapping[str, Iterable],
    stage_modes: list[str] | None = None,
    execution_sync_modes: list[str] | None = None,
    execution_async_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对任务图进行基准测试。

    :param sync_graph: 同步任务图模板（用于 serial/thread 模式）
    :param async_graph: 异步任务图模板（用于 async 模式）
    :param init_tasks_dict: 初始任务字典
    :param stage_modes: 节点模式列表，默认 ["serial", "thread"]
    :param execution_sync_modes: 同步执行模式列表，默认 ["serial", "thread"]
    :param execution_async_modes: 异步执行模式列表，默认 ["async"]
    :return: 测试结果字典
    """
```

输出示例：
```
Time table:
          serial    thread    async
serial    5.23s     3.45s     3.21s
thread    2.12s     1.89s     1.65s
```

## 使用示例

### 测试执行器

```python
import asyncio
from celestialflow import TaskExecutor
from celestialflow.utils.util_benchmark import benchmark_executor

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
asyncio.run(benchmark_executor(
    sync_executor=sync_executor,
    async_executor=async_executor,
    task_source=range(1000),
))
```

### 测试任务图

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.utils.benchmark import benchmark_graph

# 创建同步节点
stage_a = TaskStage("A", process_a)
stage_b = TaskStage("B", process_b)

# 创建异步节点
async_stage_a = TaskStage("A", async_process_a)
async_stage_b = TaskStage("B", async_process_b)

# 构建同步图
sync_graph = TaskGraph()
sync_graph.set_stages(stages=[stage_a, stage_b])
sync_graph.connect([stage_a], [stage_b])

# 构建异步图
async_graph = TaskGraph()
async_graph.set_stages(stages=[async_stage_a, async_stage_b])
async_graph.connect([async_stage_a], [async_stage_b])

# 运行基准测试
benchmark_graph(
    sync_graph=sync_graph,
    async_graph=async_graph,
    init_tasks_dict={stage_a.get_tag(): range(100)},
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

**Stage Mode (节点模式)**：
- `serial`: 节点在主线程运行
- `thread`: 节点在独立线程运行

**Execution Mode (执行模式)**：
- `serial`: 节点内部串行执行
- `thread`: 节点内部线程池执行
- `async`: 节点内部协程异步执行

组合示例：
| Stage \ Execution | serial | thread | async |
|-------------------|--------|--------|-------|
| serial | S-S | S-T | S-A |
| thread | T-S | T-T | T-A |

## 输出信息

### 时间表格

显示每种配置的执行时间。

### 失败统计

如果有任务失败，会输出：
- `Fail stage dict`: 按节点分组的失败任务
- `Fail error dict`: 按错误类型分组的失败任务

## 注意事项

1. **克隆机制**: 每次测试都会克隆原始对象，避免状态污染
2. **任务固定**: 所有测试使用相同的任务列表，保证公平性
3. **资源竞争**: 线程模式可能因资源竞争影响结果，建议多次测试
4. **异步要求**: `benchmark_executor` 是异步函数，需要 `await` 或 `asyncio.run`
5. **图的分离**: `benchmark_graph` 需要分别提供 sync_graph 和 async_graph，因为 async 执行模式需要 async 函数