# Benchmark

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
    :param sync_modes: 同步模式列表，默认 ["serial", "thread", "process"]
    :param async_modes: 异步模式列表，默认 ["async"]
    :return: 测试结果字典
    """
```

输出示例：
```
           Time
serial     2.34s
thread     0.89s
process    0.45s
async      0.67s
```

### benchmark_graph

对 `TaskGraph` 进行基准测试。

```python
def benchmark_graph(
    graph: TaskGraph,
    init_tasks_dict: dict[str, Iterable],
    stage_modes: list[str] | None = None,
    execution_modes: list[str] | None = None,
) -> dict[str, Any]:
    """
    对任务图进行基准测试。

    :param graph: 任务图模板
    :param init_tasks_dict: 初始任务字典
    :param stage_modes: 节点模式列表，默认 ["serial", "process"]
    :param execution_modes: 执行模式列表，默认 ["serial", "thread"]
    :return: 测试结果字典
    """
```

输出示例：
```
Time table:
          serial    thread
serial    5.23s     3.45s
process   2.12s     1.89s

Fail stage dict: {}
Fail error dict: {}
```

## 使用示例

### 测试执行器

```python
import asyncio
from celestialflow import TaskExecutor
from celestialflow.utils.benchmark import benchmark_executor

# 定义同步任务
def sync_task(x):
    return x * 2

# 定义异步任务
async def async_task(x):
    await asyncio.sleep(0.01)
    return x * 2

# 创建执行器
sync_executor = TaskExecutor(func=sync_task)
async_executor = TaskExecutor(func=async_task)

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

# 创建节点
stage_a = TaskStage(func=process_a, execution_mode="thread")
stage_b = TaskStage(func=process_b, execution_mode="thread")

# 构建图
stage_a.set_graph_context([stage_b], stage_mode="process", stage_name="A")
stage_b.set_graph_context([], stage_mode="process", stage_name="B")

graph = TaskGraph([stage_a])

# 运行基准测试
benchmark_graph(
    graph=graph,
    init_tasks_dict={stage_a.get_tag(): range(100)},
    stage_modes=["serial", "process"],
    execution_modes=["serial", "thread"],
)
```

## 测试矩阵

### 执行器测试维度

| 维度 | 说明 |
|------|------|
| `serial` | 单线程串行执行 |
| `thread` | 线程池并发执行 |
| `process` | 进程池并行执行 |
| `async` | 协程异步执行 |

### 任务图测试维度

**Stage Mode (节点模式)**：
- `serial`: 节点在主进程运行
- `process`: 节点在独立进程运行

**Execution Mode (执行模式)**：
- `serial`: 节点内部串行执行
- `thread`: 节点内部线程池执行

组合示例：
| Stage \ Execution | serial | thread |
|-------------------|--------|--------|
| serial | S-S | S-T |
| process | P-S | P-T |

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
3. **资源竞争**: 进程模式可能因资源竞争影响结果，建议多次测试
4. **异步要求**: `benchmark_executor` 是异步函数，需要 `await` 或 `asyncio.run`