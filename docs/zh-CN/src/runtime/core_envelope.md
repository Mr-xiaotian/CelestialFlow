# TaskEnvelope

> 📅 最后更新日期: 2026/05/15

任务数据的包装类，在各个 Stage 之间传递。它封装了原始任务数据、任务哈希、任务 ID 和来源信息。

## 属性

```python
class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source", "prev")

    def __init__(self, task: Any, id: int, source: str, prev: Any = None):
        self.task = task      # 原始任务数据
        self.hash = None      # 哈希值（惰性计算）
        self.id = id          # 任务唯一 ID
        self.source = source  # 任务来源标识
        self.prev = prev      # 前一个任务（用于结果缓存时回溯）
```

## Getter 方法

```python
def get_task(self) -> Any:
    """获取原始任务数据。"""

def get_hash(self) -> bytes:
    """获取任务哈希值。首次调用时惰性计算并缓存。"""

def get_id(self) -> int:
    """获取任务 ID。"""

def change_id(self, new_id: int) -> None:
    """修改任务 ID（用于重试场景）。"""
```

## 惰性哈希

`hash` 在构造时为 `None`，首次调用 `get_hash()` 时才计算。这避免了在不需要去重检查的场景下浪费计算资源。

```python
envelope = TaskEnvelope("data", id=1, source="input")
assert envelope.hash is None         # 未计算
h = envelope.get_hash()              # 首次调用，计算并缓存
assert envelope.hash is not None     # 已缓存
assert envelope.get_hash() == h      # 后续调用直接返回缓存值
```

## 使用示例

```python
from celestialflow.runtime import TaskEnvelope

# 创建信封
envelope = TaskEnvelope(task_data, id=123, source="input")

# 获取数据
task = envelope.get_task()
task_hash = envelope.get_hash()
task_id = envelope.get_id()

# 修改 ID（重试时）
envelope.change_id(456)
```
