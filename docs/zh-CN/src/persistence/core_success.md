# SuccessSpout

> 📅 最后更新日期: 2026/06/11

`SuccessSpout` 继承自 `BaseSpout`，用于持续监听成功结果队列并缓存 task-result 对。

## 架构设计

```mermaid
flowchart LR
    Queue[queue.Queue] -->|守护线程轮询| Spout[SuccessSpout._handle_record]
    Spout --> IsEnvelope{record 是<br/>TaskEnvelope?}
    IsEnvelope -->|否| Drop[丢弃]
    IsEnvelope -->|是| Extract[提取 result = record.task<br/>task = record.prev]
    Extract --> Append[追加到<br/>success_pairs 列表]
    Append --> Get[get_success_pairs<br/>返回 list[(task, result)]]
```

## 初始化

```python
class SuccessSpout[T, R](BaseSpout):
    def __init__(self):
        super().__init__()
        self.success_pairs: list[tuple[T, R]] = []
```

## 核心方法

### get_success_pairs

```python
def get_success_pairs(self) -> list[tuple[T, R]]:
    """
    获取成功任务与结果的 pair 列表

    :return: [(task, result), ...]
    """
```

## 内部实现

### _handle_record

从队列中接收 `TaskEnvelope`，检查类型后提取原始任务（`record.prev`）和结果（`record.task`），追加到 `success_pairs`。非 `TaskEnvelope` 类型的记录直接丢弃。

### _before_start

启动前清空 `success_pairs`，确保每次运行结果干净。

## 使用场景

成功结果会被发送到 `SuccessSpout` 的队列，执行结束后可通过 `get_success_pairs()` 获取所有成功的 (task, result) 对。`TaskExecutor` 的 `get_success_pairs()` 即委托给内部的 `SuccessSpout`。

## 使用示例

### SuccessSpout 与 TaskExecutor 配合获取成功结果

```python
from celestialflow import TaskExecutor


def double(x: int) -> int:
    """简单的处理函数：对输入值加倍"""
    if x < 0:
        raise ValueError(f"负数无法处理: {x}")
    return x * 2


# 1. 创建执行器
executor = TaskExecutor(
    "加倍处理",
    double,
    execution_mode="thread",
    max_workers=4,
)

# 2. 启动执行器处理 0~9 的数字
#    SuccessSpout 在后台自动监听成功结果队列
executor.start(range(10))

# 3. 获取所有成功的 (task, result) 对
pairs = executor.get_success_pairs()

print(f"成功处理了 {len(pairs)} 个任务:")
for task, result in pairs:
    print(f"  输入: {task:>3}  ->  输出: {result}")
```

### 从 TaskGraph 获取所有节点的成功结果

当使用 `TaskGraph` 多阶段任务图时，可以从每个阶段的执行器获取成功结果：

```python
from celestialflow import TaskGraph, TaskStage


def stage_a(x: int) -> str:
    return f"processed-{x}"


def stage_b(s: str) -> dict:
    return {"key": s.upper()}


# 创建多阶段任务图
graph = TaskGraph(schedule_mode="staged")
sa = TaskStage("StageA", stage_a, execution_mode="thread")
sb = TaskStage("StageB", stage_b, execution_mode="thread")
graph.set_stages([sa, sb])
graph.connect([sa], [sb])

# 启动任务图
graph.start_graph({sa.get_name(): ["apple", "banana", "cherry"]})

# 获取每个阶段执行器的成功结果
for stage in [sa, sb]:
    pairs = stage.get_success_pairs()
    print(f"节点 {stage.get_name()}: 成功 {len(pairs)} 个任务")
    for task, result in pairs[:2]:
        print(f"  输入: {task} -> 输出: {result}")
```

> **已变更**：此前示例使用 `stage.get_tag()` 和 `await graph.start_graph()`，当前源码中 Stage 使用 `get_name()` 作为唯一标识，`start_graph()` 为同步方法。
