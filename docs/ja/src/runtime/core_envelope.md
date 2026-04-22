# TaskEnvelope

各 Stage 間で受け渡されるタスクデータのラッパークラスです。生のタスクデータ、タスクハッシュ、タスク ID、ソース情報をカプセル化します。

## 属性

```python
class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source")

    def __init__(self, task, hash: str, id: int, source: str = "input"):
        self.task = task      # 生のタスクデータ
        self.hash = hash      # タスク内容のハッシュ値
        self.id = id          # タスクの一意な ID
        self.source = source  # タスクのソース（デフォルト "input"）
```

## クラスメソッド

```python
@classmethod
def wrap(cls, task, task_id: int, source: str = "input"):
    """
    生のタスクを TaskEnvelope にラップします。

    :param task: 生のタスク
    :param task_id: タスク ID
    :param source: タスクのソース
    :return: TaskEnvelope インスタンス
    """
```

## インスタンスメソッド

```python
def unwrap(self) -> tuple:
    """
    TaskEnvelope をアンラップします。

    :return: (task, hash, id, source)
    """

def change_id(self, new_id: int):
    """
    タスク ID を変更します（リトライ時に使用）。

    :param new_id: 新しいタスク ID
    """
```

## 使用例

```python
from celestialflow.runtime import TaskEnvelope

# タスクをラップ
envelope = TaskEnvelope.wrap(task_data, task_id=123, source="input")

# アンラップ
task, hash, id, source = envelope.unwrap()

# ID を変更（リトライ時）
envelope.change_id(456)
```
