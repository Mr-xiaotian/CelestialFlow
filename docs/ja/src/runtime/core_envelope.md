# src/celestialflow/runtime/core_envelope.py

> 📅 最終更新日: 2026/09/24

タスクデータのラッパークラスであり、タスクグラフノード間で転送されます。元のタスクデータとタスク ID をカプセル化します。

## 属性

```python
class TaskEnvelope[T]:
    __slots__ = ("_id", "_task")

    def __init__(self, task: T, id: int):
        self._task: T = task  # 原始任务数据
        self._id: int = id  # 任务唯一 ID
```

`TaskEnvelope` はジェネリッククラス（PEP 695 構文 `class TaskEnvelope[T]`）であり、`__slots__` でインスタンスフィールドを制限し、`_task` と `_id` の 2 項目のみを保持します。

## Getter メソッド

```python
def get_task(self) -> T:
    """获取原始任务。"""


def get_id(self) -> int:
    """获取任务 ID。"""
```

| メソッド | 戻り値の型 | 説明 |
|------|---------|------|
| `get_task()` | `T` | 構築時に渡された元のタスクを返します |
| `get_id()` | `int` | 構築時に渡されたタスク ID を返します |

## 使用例

以下の例は `TaskEnvelope` の作成とデータアクセスを示します。

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

### 多様なデータ型

```python
from celestialflow.runtime import TaskEnvelope

# 不同类型的任务数据
env_str = TaskEnvelope(task="hello world", id=2)
env_list = TaskEnvelope(task=[1, 2, 3], id=3)
env_dict = TaskEnvelope(task={"key": "value"}, id=4)
env_none = TaskEnvelope(task=None, id=5)
```

## 注意事項

- `TaskEnvelope` はタスクの重複排除に関与しなくなりました：タスクハッシュを保持せず、重複排除に関連するハッシュ計算とチェックは runtime 層では実装されていません。
- `__slots__` を使用しているため、インスタンスに `_task` / `_id` 以外の属性を動的に追加することはできません。
