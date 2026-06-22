# TaskEnvelope

> 📅 最后更新日期: 2026/06/22

任务数据的包装类，在各个 Stage 之间传递。它封装了原始任务数据、任务哈希和任务 ID。


## 属性

```python
class TaskEnvelope:
    __slots__ = ("hash", "id", "task")

    def __init__(self, task: T, id: int):
        self.task: T = task   # 原始任务数据
        self.hash: bytes | None = None  # 哈希值（惰性计算）
        self.id: int = id     # 任务唯一 ID
```

## Getter 方法

```python
def get_task(self) -> T:
    """获取原始任务数据。"""

def get_hash(self) -> bytes:
    """获取任务哈希值。首次调用时惰性计算并缓存。"""

def get_id(self) -> int:
    """获取任务 ID。"""
```

## 惰性哈希

`hash` 在构造时为 `None`，首次调用 `get_hash()` 时才计算。这避免了在不需要去重检查的场景下浪费计算资源。

- 对于可正常序列化的任务，`get_hash()` 会使用 `object_to_hash()` 生成稳定的 SHA1 字节串。
- 如果任务对象无法被 pickle / hash，`get_hash()` 不再把异常直接抛给调用方，而是退化为一个仅当前 `TaskEnvelope` 唯一的兜底字节串。
- 该兜底值带有专用前缀，语义上表示“不可 hash 任务的唯一占位”，避免影响其他任务的正常去重与调度。

```python
envelope = TaskEnvelope(task="data", id=1)
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

### 不可 hash 任务的兜底行为

```python
from celestialflow.runtime import TaskEnvelope

class UnpicklableTask:
    def __getstate__(self):
        raise TypeError("cannot pickle")

env1 = TaskEnvelope(task=UnpicklableTask(), id=101)
env2 = TaskEnvelope(task=UnpicklableTask(), id=102)

h1 = env1.get_hash()
h2 = env2.get_hash()

assert h1.startswith(b"__unhashable_task__:")
assert h2.startswith(b"__unhashable_task__:")
assert h1 != h2
```

这个行为的目标不是让不可 hash 任务参与“按内容去重”，而是保证：

- 单个不可 hash 任务不会中断整条调度链路
- 不会误与正常任务哈希冲突
- 不同不可 hash 任务 envelope 之间仍有唯一标识
