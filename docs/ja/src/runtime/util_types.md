# TaskTypes

> 📅 最終更新日: 2026/06/18

> ⚠️ **非推奨**：旧版ドキュメントに記載されていた `PersistedErrorRecord` データクラスは現在のソースコードには存在しません。

TaskTypes モジュールはフレームワークで使用される基本データ型、列挙型、補助クラスを定義します。

## StageStatus

`TaskStage` の実行状態を表す列挙型です。

```python
class StageStatus(IntEnum):
    NOT_STARTED = 0  # 未起動
    RUNNING = 1      # 実行中
    STOPPED = 2      # 停止済み
```

## TerminationSignal

タスクキュー終了をマークするセンチネルオブジェクト。Stage がこのシグナルを受信すると、上流にタスクがもう存在しないことを示し、停止準備に入るべきです。

```python
class TerminationSignal:
    def __init__(self, _id: int = -1, source: str = "input"):
        self.id = _id        # イベント ID
        self.source = source  # ソース

# グローバルシングルトン
TERMINATION_SIGNAL = TerminationSignal()
```

## TerminationIdPool

受信済みの全終了シグナル ID を格納する終了シグナル ID プール。

```python
class TerminationIdPool:
    def __init__(self, ids: list[int]):
        self.ids = ids
```

## NoOpContext

空のコンテキストマネージャ。`with` ロジックを無効化するために使用します（例: ロックが不要な場合）。

```python
class NoOpContext:
    def __enter__(self) -> "NoOpContext": ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

## ValueWrapper

スレッド内/単一プロセス用のカウンターラッパー。オプションでロックを設定可能。

```python
class ValueWrapper:
    def __init__(self, value: int, lock: Lock | NoOpContext | None = None):
        self.value = value
        self._lock = lock or NoOpContext()

    def get_lock(self) -> Lock | NoOpContext:
        """ロックオブジェクトまたは NoOpContext（ロックなしの場合）を返します。"""
```

## SumCounter

複数のカウンター（ValueWrapper）を累算する合計カウンター。

```python
class SumCounter:
    def __init__(self, lock: Lock | NoOpContext | None = None):
        """
        :param lock: オプションのスレッドロック。デフォルト None（NoOpContext を使用）
        """
        self.init_value = ValueWrapper(value=0, lock=self.lock)
        self.counters = []
```

### メソッド

| メソッド | 説明 |
|------|------|
| `add(value)` | 初期カウント値を増加（`init_value` に加算） |
| `append_counter(counter)` | 外部カウンターを追加 |
| `reset()` | 全カウンターをゼロにリセット |
| `get()` | 全カウンターの累算値を取得 |
| `value`（プロパティ） | 全カウンターの合計値を累算 |

### 使用例

```python
from celestialflow.runtime.util_types import SumCounter, ValueWrapper

counter = SumCounter()
counter.add(10)

sub_counter = ValueWrapper(value=5)
counter.append_counter(sub_counter)

print(counter.get())  # 15
```

## CTreeEvent

CelestialTree イベント名定数。タスクトレーシングと可視化に使用されます。

| 定数 | 値 | 発生タイミング |
|------|-----|---------|
| `TASK_INPUT` | `"task.input"` | タスクがシステムに入力 |
| `TASK_SUCCESS` | `"task.success"` | タスク実行成功 |
| `TASK_ERROR` | `"task.error"` | タスク実行失敗 |
| `TASK_RETRY_PREFIX` | `"task.retry."` | リトライプレフィックス（リトライ回数を連結） |
| `TASK_DUPLICATE` | `"task.duplicate"` | 重複タスク検出 |
| `TERMINATION_INPUT` | `"termination.input"` | 終了シグナル注入 |
| `TERMINATION_MERGE` | `"termination.merge"` | 終了シグナルマージ |

## 使用例

以下の例は `util_types` モジュールの各データクラスとユーティリティクラスの典型的な使用方法を示します。

### TerminationSignal と TerminationIdPool

```python
from celestialflow.runtime.util_types import TerminationSignal, TERMINATION_SIGNAL, TerminationIdPool

# カスタム終了シグナルの作成
signal = TerminationSignal(_id=42, source="my_source")
print(f"シグナル ID: {signal.id}, ソース: {signal.source}")

# グローバルシングルトンの使用
print(f"デフォルト終了シグナル ID: {TERMINATION_SIGNAL.id}")      # -1
print(f"デフォルトソース: {TERMINATION_SIGNAL.source}")         # "input"
print(f"同一インスタンスか: {TERMINATION_SIGNAL is TerminationSignal()}")  # False（毎回新規インスタンス）

# 終了シグナル ID プールの作成
pool = TerminationIdPool(ids=[1, 2, 3])
print(f"ID プール: {pool.ids}")  # [1, 2, 3]
```

### StageStatus 列挙型

```python
from celestialflow.runtime.util_types import StageStatus

# 列挙値
print(f"NOT_STARTED = {StageStatus.NOT_STARTED.value}")  # 0
print(f"RUNNING = {StageStatus.RUNNING.value}")          # 1
print(f"STOPPED = {StageStatus.STOPPED.value}")          # 2

# 状態遷移
status = StageStatus.NOT_STARTED
print(f"初期状態: {status.name}")
```

### ValueWrapper と SumCounter

```python
from celestialflow.runtime.util_types import ValueWrapper, SumCounter

# ValueWrapper：オプションロック付きカウンター
counter = ValueWrapper(value=10)
print(f"初期値: {counter.value}")  # 10
with counter.get_lock():
    counter.value += 5
print(f"ロック付きインクリメント後: {counter.value}")  # 15

# SumCounter：複数カウンターの累算
sum_counter = SumCounter()
sum_counter.add(100)

sub1 = ValueWrapper(value=20)
sub2 = ValueWrapper(value=30)
sum_counter.append_counter(sub1)
sum_counter.append_counter(sub2)

print(f"合計 (100 + 20 + 30): {sum_counter.value}")  # 150

# リセット
sum_counter.reset()
print(f"リセット後: {sum_counter.value}")  # 0
```

### NoOpContext

```python
from celestialflow.runtime.util_types import NoOpContext

# 空のコンテキストマネージャ。with ロジックの無効化に使用
ctx = NoOpContext()
with ctx:
    print("これはノーオペレーションコンテキストです")
```

### CTreeEvent 定数

```python
from celestialflow.runtime.util_types import CTreeEvent

# イベント名定数
print(f"タスク入力イベント: {CTreeEvent.TASK_INPUT}")           # "task.input"
print(f"タスク成功イベント: {CTreeEvent.TASK_SUCCESS}")         # "task.success"
print(f"タスク失敗イベント: {CTreeEvent.TASK_ERROR}")           # "task.error"
print(f"リトライプレフィックス: {CTreeEvent.TASK_RETRY_PREFIX}")        # "task.retry."
print(f"重複タスクイベント: {CTreeEvent.TASK_DUPLICATE}")       # "task.duplicate"
print(f"終了注入イベント: {CTreeEvent.TERMINATION_INPUT}")    # "termination.input"
print(f"終了マージイベント: {CTreeEvent.TERMINATION_MERGE}")    # "termination.merge"
```

## 注意事項

- `ValueWrapper` と `SumCounter` のスレッドセーフ性は、呼び出し元が正しい `Lock` オブジェクトを渡すことに依存します。
- `NoOpContext` は `serial`/`async` モードで実際のロックの代わりに使用され、不要なロックオーバーヘッドを回避します。
- `PersistedErrorRecord` は frozen dataclass であり、作成後は不変です。
