# Clone

`utils/clone.py` 提供了克隆执行器、节点和任务图的功能，用于性能测试和配置复用。

## 设计目的

在性能测试中，需要多次运行相同的任务图配置，但每次运行会修改内部状态。克隆功能可以创建完全独立的副本，避免状态污染。

## 主要函数

### clone_executor

克隆 `TaskExecutor` 实例。

```python
def clone_executor(executor: TaskExecutor) -> TaskExecutor:
    """
    克隆执行器。

    :param executor: 要克隆的执行器
    :return: 新的执行器实例
    """
```

复制的属性：
- `func`: 任务函数
- `execution_mode`: 执行模式
- `worker_limit`: 并发限制
- `max_retries`: 最大重试次数
- `max_info`: 日志信息最大长度
- `unpack_task_args`: 是否解包参数
- `enable_success_cache`: 成功缓存开关
- `enable_error_cache`: 错误缓存开关
- `enable_duplicate_check`: 重复检查开关
- `show_progress`: 进度条开关
- `progress_desc`: 进度条描述
- `log_level`: 日志级别
- `retry_exceptions`: 可重试异常列表

### clone_stage

克隆 `TaskStage` 实例。

```python
def clone_stage(stage: TaskStage) -> TaskStage:
    """
    克隆节点。

    :param stage: 要克隆的节点
    :return: 新的节点实例
    """
```

除了 `TaskExecutor` 的属性外，还会复制：
- `stage_mode`: 节点模式
- `_name`: 节点名称

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
1. 遍历原图所有节点（BFS）
2. 克隆每个节点并建立映射
3. 重建节点间的连接关系
4. 复制图配置（schedule_mode, log_level）
5. 复制 CelestialTree 和 Reporter 配置

## 使用示例

### 克隆执行器

```python
from celestialflow import TaskExecutor
from celestialflow.utils.clone import clone_executor

# 创建原始执行器
executor = TaskExecutor(
    func=process,
    execution_mode="thread",
    worker_limit=10,
    max_retries=3,
)

# 克隆执行器
cloned = clone_executor(executor)
cloned.set_execution_mode("process")  # 修改克隆的配置

# 两个执行器独立运行
executor.start(range(100))
cloned.start(range(100))
```

### 克隆任务图

```python
from celestialflow import TaskGraph
from celestialflow.utils.clone import clone_graph

# 创建原始图
graph = TaskGraph([stage_a, stage_b], schedule_mode="eager")

# 克隆图用于测试
cloned_graph = clone_graph(graph)
cloned_graph.set_graph_mode("process", "thread")

# 运行克隆的图
cloned_graph.start_graph(init_tasks)
```

### 在基准测试中使用

```python
from celestialflow.utils.benchmark import benchmark_graph

# 对同一图配置进行多次测试
# benchmark_graph 内部使用 clone_graph
results = benchmark_graph(
    graph,
    init_tasks_dict={stage_a.get_tag(): range(100)},
    stage_modes=["serial", "process"],
    execution_modes=["serial", "thread"],
)
```

## 注意事项

1. **状态独立**: 克隆后的对象与原对象完全独立，修改不会互相影响
2. **连接重建**: 克隆图时会重建节点间的连接关系
3. **函数引用**: 克隆只复制函数引用，不复制函数本身
4. **性能开销**: 克隆大型图有一定开销，但比重新构建更快