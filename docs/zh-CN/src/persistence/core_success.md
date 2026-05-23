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

```python
executor = TaskExecutor("Processor", process)
executor.start(tasks)
pairs = executor.get_success_pairs()
```
