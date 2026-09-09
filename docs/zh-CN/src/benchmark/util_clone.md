# benchmark/util_clone.py

> 📅 最后更新日期: 2026/09/09

`benchmark/util_clone.py` 提供了克隆执行器与任务图的功能，用于性能测试和配置复用。

> ⚠️ 本文件定义的是 benchmark 内部工具函数，**不是公共 API**。`clone_executor` / `clone_graph` 不会从 `celestialflow` 顶层包入口导出；如有需要，请直接通过 `from celestialflow.benchmark.util_clone import ...` 访问。

## 设计目的

在性能测试中，需要多次运行相同的任务图配置，但每次运行会修改内部状态。克隆功能可以创建完全独立的副本，避免状态污染。

## 主要函数

### clone_executor

克隆 `TaskExecutor` 实例。

```python
def clone_executor[T, R](
    executor: TaskExecutor[T, R],
) -> TaskExecutor[T, R]:
    """
    克隆执行器。

    :param executor: 要克隆的执行器
    :return: 克隆执行器
    """
```

复制的属性：
- `name`: 执行器名称
- `func`: 任务函数
- `execution_mode`: 执行模式
- `max_workers`: 并发限制
- `max_retries`: 最大重试次数
- `max_info`: 日志信息最大长度
- `enable_duplicate_check`: 重复检查开关
- `retry_exceptions`: 可重试异常列表（通过 `set_retry_exceptions()` 设置）

### clone_graph

克隆 `TaskGraph` 实例。

```python
def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    克隆任务图。

    该工具仅用于 benchmark 场景，因此只支持由 ``TaskExecutor`` 组成的任务图，
    并直接复用 :func:`clone_executor` 克隆所有节点。

    :param graph: 要克隆的任务图
    :return: 克隆任务图
    :raises ConfigurationError: 图中包含非 ``TaskExecutor`` 节点时抛出
    """
```

克隆流程：
1. 从源节点出发按 BFS（广度优先）遍历原图（`graph.order_graph.out_edges` 的出边顺序）收集全部节点
2. 断言每个节点都是 `TaskExecutor`；若遇到 `TaskSplitter` / `TaskRouter` 等特化节点，立即抛出 `ConfigurationError`
3. 克隆每个节点并建立原节点名 → 克隆节点的映射
4. 通过 `set_nodes()` 注册全部克隆节点，并用 `connect()` 重建节点间的连接关系
5. 复制图配置（`name`, `graph_mode`）
6. 复制 CelestialTree（`clone_event_client`）与 Reporter 配置（`NullTaskReporter` / `TaskReporter` 可克隆，其余类型抛出 `ConfigurationError`）

> ⚠️ **`clone_graph` 不保证保留所有节点类型**：仅 `TaskExecutor` 节点会被克隆为相同类型；`TaskSplitter` / `TaskRouter` 等特化节点既不会被克隆为相同子类，其拆分 / 路由行为也不会被保留。该工具是 benchmark 内部工具，仅适用于"全由 `TaskExecutor` 构成、用于基准测试"的任务图。

## 使用示例

### 克隆执行器

```python
from celestialflow import TaskExecutor
from celestialflow.benchmark.util_clone import clone_executor


def process(x: int) -> int:
    return x * 2


# 创建原始执行器
executor = TaskExecutor(
    "Processor",
    process,
    execution_mode="thread",
    max_workers=10,
    max_retries=3,
)

# 克隆执行器
cloned = clone_executor(executor)

# 两个执行器独立运行
executor.run(range(100))
cloned.run(range(100))
```

### 克隆任务图

```python
from celestialflow import TaskGraph, TaskExecutor
from celestialflow.benchmark.util_clone import clone_graph


def process_a(x: int) -> int:
    return x * 2


def process_b(x: int) -> int:
    return x + 1


# 创建原始图
graph = TaskGraph(name="CloneDemo", graph_mode="thread")
stage_a = TaskExecutor("A", process_a)
stage_b = TaskExecutor("B", process_b)
graph.set_nodes(nodes=[stage_a, stage_b])
graph.connect([stage_a], [stage_b])

# 克隆图用于测试
cloned_graph = clone_graph(graph)

# 运行克隆的图
init_tasks = {stage_a.get_name(): [1, 2, 3]}
cloned_graph.run(init_tasks)
```

## 综合示例

以下示例展示 `clone_executor` 与 `clone_graph` 配合使用的完整场景：

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
    print(f"clone_executor: 模式={cloned_exe.execution_mode}")

    # 2. clone_graph ----
    graph = TaskGraph(name="CloneDemo", graph_mode="thread")
    a = TaskExecutor("A", square, execution_mode="thread")
    b = TaskExecutor("B", add_one, execution_mode="thread")
    graph.set_nodes([a, b])
    graph.connect([a], [b])

    cloned_grp = clone_graph(graph)
    print(f"clone_graph: 图模式={cloned_grp.graph_mode}")
    print(
        f"连接关系一致: {graph.order_graph.out_edges == cloned_grp.order_graph.out_edges}"
    )

    # 分别运行原始图和克隆图，状态完全独立
    graph.run({a.get_name(): [1, 2, 3]})
    cloned_grp.run({list(cloned_grp.node_dict.keys())[0]: [10, 20]})


asyncio.run(main())
```

### 在基准测试中使用

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

    # benchmark_graph 内部使用 clone_graph，返回结果字典
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

## 注意事项

1. **状态独立**: 克隆后的对象与原对象完全独立（通过构造新实例实现），修改不会互相影响
2. **连接重建**: 克隆图时会重建节点间的连接关系
3. **函数引用**: 克隆只复制函数引用，不复制函数本身
4. **性能开销**: 克隆大型图有一定开销，但比重新构建更快
5. **内部工具**: `clone_executor` / `clone_graph` 是 benchmark 内部工具，不在顶层包入口的 `__all__` 中，签名/语义可能随 benchmark 内部实现调整而变化
6. **节点类型限制**: `clone_graph` 仅支持 `TaskExecutor` 节点；遇到 `TaskSplitter` / `TaskRouter` 等特化节点会抛出 `ConfigurationError`，**不**保留这些子类的类型与行为
