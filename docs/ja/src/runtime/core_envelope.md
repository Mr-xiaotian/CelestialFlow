# TaskEnvelope

> 📅 最終更新日: 2026/06/11

タスクデータのラッパークラスであり、各 Stage 間で転送されます。元のタスクデータ、タスクハッシュ、タスク ID、ソース情報をカプセル化します。

## 属性

```python
class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source", "prev")

    def __init__(self, task: Any, id: int, source: str, prev: Any = None):
        self.task = task      # 元のタスクデータ
        self.hash = None      # ハッシュ値（遅延計算）
        self.id = id          # タスク一意識別子
        self.source = source  # タスクソース識別子
        self.prev = prev      # 先行タスク（結果キャッシュの遡及用）
```

## Getter メソッド

```python
def get_task(self) -> Any:
    """元のタスクデータを取得します。"""

def get_hash(self) -> bytes:
    """タスクハッシュ値を取得します。初回呼び出し時に遅延計算されキャッシュされます。"""

def get_id(self) -> int:
    """タスク ID を取得します。"""

def get_prev(self) -> Any | None:
    """先行タスクを取得します（結果キャッシュの遡及用）。"""
```

## 遅延ハッシュ

`hash` は構築時には `None` であり、初回の `get_hash()` 呼び出し時に初めて計算されます。これにより、重複排除チェックが不要なシナリオでの計算リソース浪費を防ぎます。

- 正常にシリアライズ可能なタスクの場合、`get_hash()` は `object_to_hash()` を使用して安定した SHA1 バイト列を生成します。
- タスクオブジェクトが pickle / hash 不可能な場合、`get_hash()` は例外を呼び出し元に直接送出せず、現在の `TaskEnvelope` に固有のフォールバックバイト列にフォールバックします。
- このフォールバック値は専用のプレフィックスを持ち、「hash 不可能タスクの一意なプレースホルダ」を意味し、他のタスクの通常の重複排除やスケジューリングに影響を与えません。

```python
envelope = TaskEnvelope("data", id=1, source="input")
assert envelope.hash is None         # 未計算
h = envelope.get_hash()              # 初回呼び出し、計算してキャッシュ
assert envelope.hash is not None     # キャッシュ済み
assert envelope.get_hash() == h      # 後続呼び出しはキャッシュ値を直接返す
```

## 使用例

以下の例は `TaskEnvelope` の作成、データアクセス、遅延ハッシュ計算、ID 変更などのコア操作を示します。

```python
from celestialflow.runtime import TaskEnvelope

# 1. タスクエンベロープの作成
envelope = TaskEnvelope(
    task={"user": "alice", "score": 95},
    id=1,
    source="input",
)

# 2. 元のタスクデータの取得
task = envelope.get_task()
print(f"タスクデータ: {task}")  # {"user": "alice", "score": 95}

# 3. 初期状態の確認（hash は未計算 — 遅延評価）
print(f"初期 hash: {envelope.hash}")  # None

# 4. タスク ID の取得
print(f"タスク ID: {envelope.get_id()}")  # 1

# 5. get_hash() 初回呼び出し時に SHA1 を計算しキャッシュ
h = envelope.get_hash()
print(f"SHA1 ハッシュ: {h.hex()[:16]}...")
print(f"呼出後 hash はキャッシュ済み: {envelope.hash is not None}")  # True
print(f"再呼出はキャッシュ値を返す: {envelope.get_hash() == h}")    # True

# 6. 先行タスクの取得（結果キャッシュ遡及用）
print(f"先行タスク: {envelope.get_prev()}")  # None（prev 未設定）
```

### 様々なデータ型

```python
from celestialflow.runtime import TaskEnvelope

# 異なる型のタスクデータ
env_str = TaskEnvelope(task="hello world", id=2, source="producer")
env_list = TaskEnvelope(task=[1, 2, 3], id=3, source="producer")
env_dict = TaskEnvelope(task={"key": "value"}, id=4, source="producer")
env_none = TaskEnvelope(task=None, id=5, source="producer")

# prev パラメータ: 先行タスクを記録（結果キャッシュ遡及用）
env_with_prev = TaskEnvelope(task="data", id=6, source="producer", prev=env_str)
print(f"先行タスクデータ: {env_with_prev.prev.get_task()}")
```

### hash 不可能タスクのフォールバック動作

```python
from celestialflow.runtime import TaskEnvelope

class UnpicklableTask:
    def __getstate__(self):
        raise TypeError("cannot pickle")

env1 = TaskEnvelope(task=UnpicklableTask(), id=101, source="input")
env2 = TaskEnvelope(task=UnpicklableTask(), id=102, source="input")

h1 = env1.get_hash()
h2 = env2.get_hash()

assert h1.startswith(b"__unhashable_task__:")
assert h2.startswith(b"__unhashable_task__:")
assert h1 != h2
```

この動作の目的は、hash 不可能タスクを「内容に基づく重複排除」に参加させることではなく、以下を保証することです:

- 単一の hash 不可能タスクがスケジューリングチェーン全体を中断しないこと
- 通常のタスクハッシュと誤って衝突しないこと
- 異なる hash 不可能タスクエンベロープ間で一意な識別子を維持すること
