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

以下示例展示 `TaskEnvelope` 的创建、数据访问、惰性哈希计算和 ID 变更等核心操作。

```python
from celestialflow.runtime import TaskEnvelope

# 1. 创建任务信封
envelope = TaskEnvelope(
    task={"user": "alice", "score": 95},
    id=1,
    source="input",
)

# 2. 获取原始任务数据
task = envelope.get_task()
print(f"任务数据: {task}")  # {"user": "alice", "score": 95}

# 3. 查看初始状态（hash 尚未计算 — 惰性求值）
print(f"初始 hash: {envelope.hash}")  # None

# 4. 获取任务 ID
print(f"任务 ID: {envelope.get_id()}")  # 1

# 5. 首次调用 get_hash() 时计算并缓存 SHA1
h = envelope.get_hash()
print(f"SHA1 哈希: {h.hex()[:16]}...")
print(f"调用后 hash 已缓存: {envelope.hash is not None}")  # True
print(f"重复调用返回缓存值: {envelope.get_hash() == h}")    # True

# 6. 重试场景：变更任务 ID
envelope.change_id(100)
print(f"重试后新 ID: {envelope.get_id()}")  # 100
print(f"重试不影响数据: {envelope.get_task()}")  # 数据不变
```

### 多种数据类型

```python
from celestialflow.runtime import TaskEnvelope

# 不同类型的任务数据
env_str = TaskEnvelope(task="hello world", id=2, source="producer")
env_list = TaskEnvelope(task=[1, 2, 3], id=3, source="producer")
env_dict = TaskEnvelope(task={"key": "value"}, id=4, source="producer")
env_none = TaskEnvelope(task=None, id=5, source="producer")

# prev 参数：记录前驱任务（用于结果缓存回溯）
env_with_prev = TaskEnvelope(task="data", id=6, source="producer", prev=env_str)
print(f"前驱任务数据: {env_with_prev.prev.get_task()}")
```
