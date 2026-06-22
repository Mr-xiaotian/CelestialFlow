# Clone

> 📅 最終更新日: 2026/06/22

`utils/util_clone.py` は実行器、ノード、タスクグラフのクローン機能を提供し、パフォーマンステストと設定再利用に使用します。

## 設計目的

パフォーマンステストでは、同じタスクグラフ設定を複数回実行する必要がありますが、各実行で内部状態が変更されます。クローン機能は完全に独立したコピーを作成し、状態汚染を防止します。

## 主要関数

### clone_executor

`TaskExecutor` インスタンスをクローンします。

```python
def clone_executor(executor: TaskExecutor) -> TaskExecutor:
    """
    克隆执行器。

    :param executor: 要克隆的执行器
    :return: 新的执行器实例
    """
```

コピーされる属性：
- `name`: 执行器名称
- `func`: 任务函数
- `execution_mode`: 执行模式
- `max_workers`: 并发限制
- `max_retries`: 最大重试次数
- `max_info`: 日志信息最大长度
- `enable_duplicate_check`: 重复检查开关
- `persist_result`: 结果持久化开关
- `log_level`: 日志级别
- `retry_exceptions`: 可重试异常列表

### clone_stage

`TaskStage` インスタンスをクローンします。

```python
def clone_stage(stage: TaskStage) -> TaskStage:
    """
    克隆节点。

    :param stage: 要克隆的节点
    :return: 新的节点实例
    """
```

`TaskExecutor` の属性に加えて、以下もコピーされます：
- `stage_mode`: 节点模式

### clone_graph

`TaskGraph` インスタンスをクローンします。

```python
def clone_graph(graph: TaskGraph) -> TaskGraph:
    """
    克隆任务图。

    :param graph: 要克隆的任务图
    :return: 新的任务图实例
    """
```

クローンフロー：
1. 遍历原图所有节点（BFS）
2. 克隆每个节点并建立映射
3. 重建节点间的连接关系
4. 复制图配置（schedule_mode, log_level）
5. 复制 CelestialTree と Reporter 設定

## 使用例

### 実行器のクローン

```python
from celestialflow import TaskExecutor
from celestialflow.utils.util_clone import clone_executor


# 定义处理函数
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
executor.start(range(100))
cloned.start(range(100))
```

### ノード（TaskStage）のクローン

```python
from celestialflow import TaskStage
from celestialflow.utils.util_clone import clone_stage


# 定义节点处理函数
def process_func(x: int) -> int:
    return x + 1


# 创建原始节点
stage = TaskStage(
    "Processor",
    process_func,
    stage_mode="thread",
    execution_mode="thread",
    max_workers=4,
)

# 克隆节点
cloned_stage = clone_stage(stage)

# 原始节点和克隆节点独立运行，互不影响
stage.start(range(10))
cloned_stage.start(range(10, 20))
```

### タスクグラフのクローン

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.utils.util_clone import clone_graph


# 定义处理函数
def process_a(x: int) -> int:
    return x * 2


def process_b(x: int) -> int:
    return x + 1


# 创建原始图
graph = TaskGraph(name="CloneDemo", schedule_mode="eager")
stage_a = TaskStage("A", process_a)
stage_b = TaskStage("B", process_b)
graph.set_stages(stages=[stage_a, stage_b])
graph.connect([stage_a], [stage_b])

# 克隆图用于测试
cloned_graph = clone_graph(graph)

# 运行克隆的图
init_tasks = {stage_a.get_name(): [1, 2, 3]}
cloned_graph.start_graph(init_tasks)
```

## 総合例

以下の例は `clone_executor`、`clone_stage`、`clone_graph` を組み合わせて使用する完全なシナリオを示します：

```python
import asyncio
from celestialflow import TaskExecutor, TaskStage, TaskGraph
from celestialflow.utils.util_clone import clone_executor, clone_stage, clone_graph


# 定义平方函数
def square(x: int) -> int:
    return x * x


# 定义加一函数
def add_one(x: int) -> int:
    return x + 1


async def main():
    # 1. clone_executor ----
    executor = TaskExecutor(
        "Square", square, execution_mode="thread", max_workers=4
    )
    cloned_exe = clone_executor(executor)
    print(f"clone_executor: 模式={cloned_exe.execution_mode}")

    # 2. clone_stage ----
    stage = TaskStage(
        "AddOne", add_one, stage_mode="serial", execution_mode="serial"
    )
    cloned_stg = clone_stage(stage)
    print(f"clone_stage: 名称={cloned_stg.get_name()}, mode={cloned_stg.get_stage_mode()}")

    # 3. clone_graph ----
    graph = TaskGraph(name="CloneDemo", schedule_mode="eager")
    a = TaskStage("A", square, execution_mode="thread")
    b = TaskStage("B", add_one, execution_mode="thread")
    graph.set_stages([a, b])
    graph.connect([a], [b])

    cloned_grp = clone_graph(graph)
    print(f"clone_graph: 调度模式={cloned_grp.schedule_mode}")
    print(f"连接关系一致: {graph.out_edges == cloned_grp.out_edges}")

    # 分别运行原始图和克隆图，状态完全独立
    graph.start_graph({a.get_name(): [1, 2, 3]})
    cloned_grp.start_graph(
        {list(cloned_grp.stage_dict.keys())[0]: [10, 20]}
    )


asyncio.run(main())
```

### ベンチマークテストでの使用

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.utils.util_benchmark import benchmark_graph


# 定义同步任务
def task(x: int) -> int:
    return x * 2


# 定义异步任务
async def async_task(x: int) -> int:
    return x * 2


# 创建同步节点
stage_a = TaskStage("A", task)
stage_b = TaskStage("B", task)

# 创建异步节点
async_stage_a = TaskStage("A", async_task)
async_stage_b = TaskStage("B", async_task)

# 构建同步图和异步图
sync_graph = TaskGraph(name="BenchSync")
sync_graph.set_stages(stages=[stage_a, stage_b])
async_graph = TaskGraph(name="BenchAsync")
async_graph.set_stages(stages=[async_stage_a, async_stage_b])

# benchmark_graph 内部使用 clone_graph
results = benchmark_graph(
    sync_graph=sync_graph,
    async_graph=async_graph,
    init_tasks_dict={stage_a.get_name(): range(100)},
    stage_modes=["serial", "thread"],
    execution_sync_modes=["serial", "thread"],
    execution_async_modes=["async"],
)
```

## 注意事項

1. **状態の独立性**: クローン後のオブジェクトは元のオブジェクトと完全に独立しています（新しいインスタンスの構築により実現）。変更は相互に影響しません
2. **接続の再構築**: グラフのクローン時にはノード間の接続関係が再構築されます
3. **関数参照**: クローンは関数参照のみをコピーし、関数自体はコピーしません
4. **パフォーマンスオーバーヘッド**: 大規模グラフのクローンにはある程度のオーバーヘッドがありますが、再構築より高速です
