# TaskEnvelope

> 📅 最終更新日: 2026/06/05

タスクデータのラッパークラスで、各 Stage 間で受け渡されます。元のタスクデータ、タスクハッシュ、タスク ID、ソース情報をカプセル化しています。

## ハッシュ挙動

- 通常のタスクでは、`get_hash()` は `object_to_hash()` に委譲し、SHA1 の bytes 結果をキャッシュします。
- タスクが pickle / hash できない場合、例外をそのまま投げず、`__unhashable_task__:` プレフィックス付きの一意な bytes 値へフォールバックします。
- このフォールバックは envelope ごとに一意であり、1 件の不正タスクが他のディスパッチ処理を壊さないための仕組みです。

## 属性

```python
class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source", "prev")

    def __init__(self, task: Any, id: int, source: str, prev: Any = None):
        self.task = task      # 元のタスクデータ
        self.hash = None      # ハッシュ値（遅延計算）
        self.id = id          # タスク一意 ID
        self.source = source  # タスクソース識別子
        self.prev = prev      # 前のタスク（結果キャッシュの遡及用）
```

## ゲッターメソッド

```python
def get_task(self) -> Any:
    """元のタスクデータを取得します。"""

def get_hash(self) -> bytes:
    """タスクハッシュを取得します。初回呼び出し時に遅延計算してキャッシュします。"""

def get_id(self) -> int:
    """タスク ID を取得します。"""

def change_id(self, new_id: int) -> None:
    """タスク ID を変更します（リトライシナリオ用）。"""
```

## 遅延ハッシュ

`hash` はコンストラクション時に `None` で、`get_hash()` の初回呼び出し時にのみ計算されます。これにより、重複チェックが不要なシナリオでの計算リソースの浪費を回避します。

hash 計算に失敗した場合は、上記のフォールバック bytes がキャッシュされます。

```python
envelope = TaskEnvelope("data", id=1, source="input")
assert envelope.hash is None         # 未計算
h = envelope.get_hash()              # 初回呼び出し、計算してキャッシュ
assert envelope.hash is not None     # キャッシュ済み
assert envelope.get_hash() == h      # 以降の呼び出しはキャッシュ値を返却
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
