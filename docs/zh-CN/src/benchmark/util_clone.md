# Clone

> 📅 最后更新日期: 2026/08/26

`benchmark/util_clone.py` 提供了克隆执行器、节点和任务图的功能，用于性能测试和配置复用。

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

### clone_stage

克隆 `TaskStage` 节点。

```python
def clone_stage[T, R](
    stage: TaskStage[T, R],
) -> TaskStage[T, R]:
    """
    克隆节点。

    :param stage: 要克隆的节点
    :return: 克隆节点
    """
```

克隆步骤：
1. 复用 executor 风格参数集合（`name` / `func` / `execution_mode` / `max_workers` / `max_retries` / `max_info` / `enable_duplicate_check`）
2. 通过 `inspect.signature` 检查节点类 `__init__` 的参数集合，只保留两者的交集，避免把节点类不接受的参数传入
3. 以过滤后的参数构造与原节点**同类型**的新实例
4. 复制 `retry_exceptions`

参数过滤的影响：
- 普通 `TaskStage` 的 `__init__` 为 `(name, func, **kwargs)`，过滤后只保留 `name` 与 `func`，`execution_mode` 等运行配置不会复制（克隆结果使用默认配置）。
- `TaskSplitter` 的 `__init__` 仅接受 `name` / `split_item`，克隆时只传入 `name`，拆分逻辑由类自身默认实现提供。
- `TaskRouter` 的 `__init__` 要求必填 `router`，而该参数不在可过滤集合内，直接克隆 `TaskRouter` 会抛出 `TypeError`。

### clone_graph

克隆 `TaskGraph` 实例。

```python
def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    克隆任务图。

    :param graph: 要克隆的任务图
    :return: 新的任务图实例
    """
```

克隆流程：
1. 从源节点出发按 BFS（广度优先）遍历原图（`graph.order_graph.out_edges` 的出边顺序）收集全部节点
2. 克隆每个节点并建立原节点名 → 克隆节点的映射
3. 通过 `set_stages()` 注册全部克隆节点，并用 `connect()` 重建节点间的连接关系
4. 复制图配置（`name`, `graph_mode`）
5. 复制 CelestialTree（`clone_event_client`）与 Reporter 配置（`NullTaskReporter` / `TaskReporter` 可克隆，其余类型抛出 `ConfigurationError`）

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

### 克隆节点（TaskStage）

```python
from celestialflow import TaskStage
from celestialflow.benchmark.util_clone import clone_stage


def process_func(x: int) -> int:
    return x + 1


# 创建原始节点
stage = TaskStage(
    "Processor",
    process_func,
    execution_mode="thread",
    max_workers=4,
)

# 克隆节点
cloned_stage = clone_stage(stage)

# 原始节点和克隆节点独立运行，互不影响
stage.run(range(10))
cloned_stage.run(range(10, 20))
```

### 克隆任务图

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.benchmark.util_clone import clone_graph


def process_a(x: int) -> int:
    return x * 2


def process_b(x: int) -> int:
    return x + 1


# 创建原始图
graph = TaskGraph(name="CloneDemo", graph_mode="thread")
stage_a = TaskStage("A", process_a)
stage_b = TaskStage("B", process_b)
graph.set_stages(stages=[stage_a, stage_b])
graph.connect([stage_a], [stage_b])

# 克隆图用于测试
cloned_graph = clone_graph(graph)

# 运行克隆的图
init_tasks = {stage_a.get_name(): [1, 2, 3]}
cloned_graph.run(init_tasks)
```

## 综合示例

以下示例展示 `clone_executor`、`clone_stage` 和 `clone_graph` 配合使用的完整场景：

```python
import asyncio
from celestialflow import TaskExecutor, TaskStage, TaskGraph
from celestialflow.benchmark.util_clone import clone_executor, clone_stage, clone_graph


def square(x: int) -> int:
    return x * x


def add_one(x: int) -> int:
    return x + 1


async def main():
    # 1. clone_executor ----
    executor = TaskExecutor("Square", square, execution_mode="thread", max_workers=4)
    cloned_exe = clone_executor(executor)
    print(f"clone_executor: 模式={cloned_exe.execution_mode}")

    # 2. clone_stage ----
    stage = TaskStage("AddOne", add_one, execution_mode="serial")
    cloned_stg = clone_stage(stage)
    print(
        f"clone_stage: 名称={cloned_stg.get_name()}, 模式={cloned_stg.execution_mode}"
    )

    # 3. clone_graph ----
    graph = TaskGraph(name="CloneDemo", graph_mode="thread")
    a = TaskStage("A", square, execution_mode="thread")
    b = TaskStage("B", add_one, execution_mode="thread")
    graph.set_stages([a, b])
    graph.connect([a], [b])

    cloned_grp = clone_graph(graph)
    print(f"clone_graph: 图模式={cloned_grp.graph_mode}")
    print(
        f"连接关系一致: {graph.order_graph.out_edges == cloned_grp.order_graph.out_edges}"
    )

    # 分别运行原始图和克隆图，状态完全独立
    graph.run({a.get_name(): [1, 2, 3]})
    cloned_grp.run({list(cloned_grp.stage_dict.keys())[0]: [10, 20]})


asyncio.run(main())
```

### 在基准测试中使用

```python
import asyncio
from celestialflow import TaskGraph, TaskStage
from celestialflow.benchmark.util_benchmark import benchmark_graph


def task(x: int) -> int:
    return x * 2


async def async_task(x: int) -> int:
    return x * 2


async def main():
    stage_a = TaskStage("A", task)
    stage_b = TaskStage("B", task)
    async_stage_a = TaskStage("A", async_task)
    async_stage_b = TaskStage("B", async_task)

    sync_graph = TaskGraph(name="BenchSync")
    sync_graph.set_stages(stages=[stage_a, stage_b])
    async_graph = TaskGraph(name="BenchAsync")
    async_graph.set_stages(stages=[async_stage_a, async_stage_b])

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
5. **配置回退**: `clone_stage` 只复制节点类 `__init__` 接受的参数，普通 `TaskStage` 的执行模式等运行配置会回退为默认值；`TaskRouter` 因 `router` 必填参数缺失而无法克隆
