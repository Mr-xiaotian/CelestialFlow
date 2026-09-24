# src/celestialflow/runtime/core_envelope.py

> 📅 Last Updated: 2026/09/24

A wrapper class for task data that is passed between task graph nodes. It encapsulates the original task data and the task ID.

## Attributes

```python
class TaskEnvelope[T]:
    __slots__ = ("_id", "_task")

    def __init__(self, task: T, id: int):
        self._task: T = task  # 原始任务数据
        self._id: int = id  # 任务唯一 ID
```

`TaskEnvelope` is a generic class (PEP 695 syntax `class TaskEnvelope[T]`), using `__slots__` to restrict instance fields, storing only `_task` and `_id`.

## Getter Methods

```python
def get_task(self) -> T:
    """获取原始任务。"""


def get_id(self) -> int:
    """获取任务 ID。"""
```

| Method | Return Type | Description |
|------|---------|------|
| `get_task()` | `T` | Returns the original task passed at construction |
| `get_id()` | `int` | Returns the task ID passed at construction |

## Usage Examples

The following examples demonstrate the creation of `TaskEnvelope` and data access.

```python
from celestialflow.runtime import TaskEnvelope

# 1. 创建任务信封
envelope = TaskEnvelope(
    task={"user": "alice", "score": 95},
    id=1,
)

# 2. 获取原始任务数据
task = envelope.get_task()
print(f"任务数据: {task}")  # {"user": "alice", "score": 95}

# 3. 获取任务 ID
print(f"任务 ID: {envelope.get_id()}")  # 1
```

### Multiple Data Types

```python
from celestialflow.runtime import TaskEnvelope

# 不同类型的任务数据
env_str = TaskEnvelope(task="hello world", id=2)
env_list = TaskEnvelope(task=[1, 2, 3], id=3)
env_dict = TaskEnvelope(task={"key": "value"}, id=4)
env_none = TaskEnvelope(task=None, id=5)
```

## Notes

- `TaskEnvelope` no longer participates in task deduplication: it does not hold a task hash, and the hash computation and checks related to deduplication are no longer implemented at the runtime layer.
- Because of `__slots__`, you cannot dynamically add attributes other than `_task` / `_id` to instances.
