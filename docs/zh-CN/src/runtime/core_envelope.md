# src/celestialflow/runtime/core_envelope.py

> 📅 最后更新日期: 2026/09/24

任务数据的包装类，在任务图节点之间传递。它封装了原始任务数据与任务 ID。

## 属性

```python
class TaskEnvelope[T]:
    __slots__ = ("_id", "_task")

    def __init__(self, task: T, id: int):
        self._task: T = task  # 原始任务数据
        self._id: int = id  # 任务唯一 ID
```

`TaskEnvelope` 是泛型类（PEP 695 语法 `class TaskEnvelope[T]`），使用 `__slots__` 限制实例字段，仅保存 `_task` 与 `_id` 两项。

## Getter 方法

```python
def get_task(self) -> T:
    """获取原始任务。"""


def get_id(self) -> int:
    """获取任务 ID。"""
```

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `get_task()` | `T` | 返回构造时传入的原始任务 |
| `get_id()` | `int` | 返回构造时传入的任务 ID |

## 使用示例

以下示例展示 `TaskEnvelope` 的创建与数据访问。

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

### 多种数据类型

```python
from celestialflow.runtime import TaskEnvelope

# 不同类型的任务数据
env_str = TaskEnvelope(task="hello world", id=2)
env_list = TaskEnvelope(task=[1, 2, 3], id=3)
env_dict = TaskEnvelope(task={"key": "value"}, id=4)
env_none = TaskEnvelope(task=None, id=5)
```

## 注意事项

- `TaskEnvelope` 不再参与任务去重：它不持有任务哈希，去重相关的哈希计算与检查已不在 runtime 层实现。
- 由于使用 `__slots__`，不能给实例动态添加 `_task` / `_id` 之外的属性。
