# SuccessSpout

> 📅 最后更新日期: 2026/05/24

`SuccessSpout` 继承自 `BaseSpout`，用于持续监听成功结果队列并缓存 task-result 对。

## 架构设计

```mermaid
flowchart LR
    Queue[queue.Queue] -->|守护线程轮询| Spout[SuccessSpout._handle_record]
    Spout --> IsEnvelope{record 是
TaskEnvelope?}
    IsEnvelope -->|否| Drop[丢弃]
    IsEnvelope -->|是| Extract[提取 result = record.task
task = record.prev]
    Extract --> Append[追加到
success_pairs 列表]
    Append --> Get[get_success_pairs
返回 list[(task, result)]]

    style Queue fill:#fff3e0
    style Spout fill:#e8f5e9
    style IsEnvelope fill:#fff9c4
    style Extract fill:#e3f2fd
    style Append fill:#c8e6c9
    style Get fill:#f3e5f5
```

## 初始化

```python
class SuccessSpout(BaseSpout):
    def __init__(self):
        super().__init__()
        self.success_pairs: list[tuple[Any, Any]] = []
```

## 核心方法

### get_success_pairs

```python
def get_success_pairs(self) -> list[tuple[Any, Any]]:
    """
    获取成功任务与结果的 pair 列表

    :return: [(task, result), ...]
    """
```

## 内部实现

### _handle_record

从队列中接收 `TaskEnvelope`，提取原始任务（`record.prev`）和结果（`record.task`），追加到 `success_pairs`。

### _before_start

启动前清空 `success_pairs`。

## 使用场景

成功结果会被发送到 `SuccessSpout` 的队列，执行结束后可通过 `get_success_pairs()` 获取所有成功的 (task, result) 对。

## 使用示例

### SuccessSpout 与 TaskExecutor 配合获取成功结果

以下完整示例展示如何使用 `SuccessSpout` 获取所有成功任务的 `(task, result)` 对：

```python
import asyncio
from celestialflow import TaskExecutor


def double(x: int) -> int:
    """简单的处理函数：对输入值加倍"""
    if x < 0:
        raise ValueError(f"负数无法处理: {x}")
    return x * 2


async def main():
    # 1. 创建执行器
    executor = TaskExecutor(
        "加倍处理",
        double,
        execution_mode="thread",
        max_workers=4,
    )

    # 2. 启动执行器处理 0~9 的数字
    #    SuccessSpout 在后台自动监听成功结果队列
    await executor.start(range(10))

    # 3. 获取所有成功的 (task, result) 对
    #    executor.get_success_pairs() 实际委托给 SuccessSpout
    pairs = executor.get_success_pairs()

    # 4. 输出结果
    print(f"成功处理了 {len(pairs)} 个任务:")
    for task, result in pairs:
        print(f"  输入: {task:>3}  ->  输出: {result}")

    # 预期输出：
    #   输入:   0  ->  输出: 0
    #   输入:   1  ->  输出: 2
    #   输入:   2  ->  输出: 4
    #   ...
    #   输入:   9  ->  输出: 18


asyncio.run(main())
```

### 从 TaskGraph 获取所有节点的成功结果

当使用 `TaskGraph` 多阶段任务图时，可以从每个阶段的执行器获取成功结果：

```python
import asyncio
from celestialflow import TaskGraph, TaskStage


def stage_a(x: int) -> str:
    return f"processed-{x}"


def stage_b(s: str) -> dict:
    return {"key": s.upper()}


async def main():
    # 创建多阶段任务图
    graph = TaskGraph(schedule_mode="staged")
    sa = TaskStage("StageA", stage_a, execution_mode="thread")
    sb = TaskStage("StageB", stage_b, execution_mode="thread")
    graph.set_stages([sa, sb])
    graph.connect([sa], [sb])

    # 启动任务图
    await graph.start_graph({sa.get_tag(): ["apple", "banana", "cherry"]})

    # 获取每个阶段执行器的成功结果
    # 注意：实际属性名可能为 _executor，请参考具体版本
    for stage in [sa, sb]:
        pairs = stage.get_success_pairs()
        print(f"节点 {stage.get_tag()}: 成功 {len(pairs)} 个任务")
        for task, result in pairs[:2]:  # 只打印前 2 个
            print(f"  输入: {task} -> 输出: {result}")


asyncio.run(main())
```
