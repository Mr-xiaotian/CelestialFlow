# SuccessSpout

`SuccessSpout` 继承自 `BaseSpout`，用于持续监听成功结果队列并缓存 task-result 对。

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

当 `TaskExecutor` 启用 `enable_success_cache=True` 时，成功结果会被发送到 `SuccessSpout` 的队列，执行结束后可通过 `get_success_pairs()` 获取所有成功的 (task, result) 对。

```python
executor = TaskExecutor(func=process, enable_success_cache=True)
executor.start(tasks)
pairs = executor.success_spout.get_success_pairs()
```
