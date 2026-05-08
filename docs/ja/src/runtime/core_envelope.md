# TaskEnvelope

> 📅 最終更新日: 2026/05/08

Stage 間で受け渡されるタスクデータのラッパークラス。元のタスクデータ、タスクハッシュ、タスク ID、ソース情報をカプセル化します。

## 属性

```python
class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source", "prev")

    def __init__(self, task: Any, id: int, source: str, prev: Any = None):
        self.task = task      # 元のタスクデータ
        self.hash = None      # ハッシュ値（遅延計算）
        self.id = id          # タスク固有 ID
        self.source = source  # タスクソース識別子
        self.prev = prev      # 前のタスク（結果キャッシュの遡及用）
```

## Getter メソッド

```python
def get_task(self) -> Any:
    """元のタスクデータを取得。"""

def get_hash(self) -> str:
    """タスクハッシュを取得。初回呼び出し時に遅延計算しキャッシュ。"""

def get_id(self) -> int:
    """タスク ID を取得。"""

def change_id(self, new_id: int) -> None:
    """タスク ID を変更（リトライシナリオで使用）。"""
```

## 遅延ハッシュ

`hash` は構築時に `None` で、`get_hash()` の初回呼び出し時にのみ計算されます。重複チェックが不要な場面での計算の無駄を回避します。

```python
envelope = TaskEnvelope("data", id=1, source="input")
assert envelope.hash is None         # 未計算
h = envelope.get_hash()              # 初回呼び出しで計算・キャッシュ
assert envelope.hash is not None     # キャッシュ済み
assert envelope.get_hash() == h      # 以降はキャッシュ値を返す
```

## 使用例

```python
from celestialflow.runtime import TaskEnvelope

# エンベロープを作成
envelope = TaskEnvelope(task_data, id=123, source="input")

# データを取得
task = envelope.get_task()
task_hash = envelope.get_hash()
task_id = envelope.get_id()

# ID を変更（リトライ時）
envelope.change_id(456)
```
