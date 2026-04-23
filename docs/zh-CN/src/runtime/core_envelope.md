# TaskEnvelope

> 📅 最后更新日期: 2026/04/22

任务数据的包装类，在各个 Stage 之间传递。它封装了原始任务数据、任务哈希、任务 ID 和来源信息。

## 属性

```python
class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source", "prev")

    def __init__(self, task, hash: str, id: int, source: str, prev: Any):
        self.task = task      # 原始任务数据
        self.hash = hash      # 任务内容的哈希值
        self.id = id          # 任务唯一 ID
        self.source = source  # 任务来源标识
        self.prev = prev      # 前一个任务（用于结果缓存时回溯）
```

## 类方法

```python
@classmethod
def wrap(cls, task, task_id: int, source: str, prev: Any = None):
    """
    将原始 task 包装为 TaskEnvelope。

    :param task: 原始任务
    :param task_id: 任务 id
    :param source: 任务来源
    :param prev: 前一个任务的 envelope
    :return: TaskEnvelope 实例
    """
```

## 实例方法

```python
def unwrap(self) -> tuple:
    """
    解包装 TaskEnvelope。

    :return: (task, hash, id)
    """

def change_id(self, new_id: int):
    """
    修改任务 ID（用于重试场景）。

    :param new_id: 新的任务 id
    """
```

## 使用示例

```python
from celestialflow.runtime import TaskEnvelope

# 包装任务
envelope = TaskEnvelope.wrap(task_data, task_id=123, source="input")

# 解包装
task, hash, id = envelope.unwrap()

# 修改 ID（重试时）
envelope.change_id(456)
```
