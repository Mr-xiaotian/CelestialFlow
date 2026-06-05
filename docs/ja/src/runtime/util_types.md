# TaskTypes

> 📅 最終更新日: 2026/05/24

TaskTypes モジュールは、フレームワークで使用される基本データ型、列挙型、ヘルパークラスを定義します。

## StageStatus

`TaskStage` の実行状態を表す列挙型クラスです。

```python
class StageStatus(IntEnum):
    NOT_STARTED = 0  # 未起動
    RUNNING = 1      # 実行中
    STOPPED = 2      # 停止済み
```

## TerminationSignal

タスクキューの終了をマークするために使用されるセンチネルオブジェクトです。Stage がこのシグナルを受信すると、上流からのタスクがもう存在しないことを示し、停止の準備をすべきことを意味します。

```python
class TerminationSignal:
    def __init__(self, _id: int = -1, source: str = "input"):
        self.id = _id        # イベント ID
        self.source = source  # ソース

# グローバルシングルトン
TERMINATION_SIGNAL = TerminationSignal()
```

## TerminationIdPool

受信したすべての終了シグナル ID を格納するための終了シグナル ID プールです。

```python
class TerminationIdPool:
    def __init__(self, ids: list[int]):
        self.ids = ids
```

## NoOpContext

空のコンテキストマネージャーで、`with` ロジックを無効化するために使用します（ロックが不要な場合など）。

```python
class NoOpContext:
    def __enter__(self) -> "NoOpContext": ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

## ValueWrapper

シングルスレッド/シングルプロセス用のカウンターラッパーで、オプションでロックを付与できます。

```python
class ValueWrapper:
    def __init__(self, value: int = 0, lock: Lock | None = None):
        self.value = value
        self._lock = lock

    def get_lock(self) -> Lock | NoOpContext:
        """ロックオブジェクトまたは NoOpContext（ロックなし時）を返します。"""
```

## SumCounter

複数のカウンター（ValueWrapper）を累積する合計カウンターです。

```python
class SumCounter:
    def __init__(self, mode: str = "serial"):
        """
        :param mode: 実行モード、'serial'（ロックなし）または 'thread'（ロックあり）
        """
```

### メソッド

| メソッド | 説明 |
|------|------|
| `add_init_value(value)` | 初期値を追加します |
| `append_counter(counter)` | 外部カウンターを追加します |
| `reset()` | すべてのカウンターをゼロにリセットします |
| `value`（プロパティ） | すべてのカウンターの合計値を累積します |

### 使用例

```python
from celestialflow.runtime.util_types import SumCounter, ValueWrapper

counter = SumCounter(mode="thread")
counter.add_init_value(10)

sub_counter = ValueWrapper(value=5)
counter.append_counter(sub_counter)

print(counter.value)  # 15
```

## CTreeEvent

タスク追跡と可視化に使用される CelestialTree イベント名定数です。

| 定数 | 値 | トリガータイミング |
|------|-----|---------|
| `TASK_INPUT` | `"task.input"` | タスクがシステムに入力されたとき |
| `TASK_SUCCESS` | `"task.success"` | タスクが成功裏に実行されたとき |
| `TASK_ERROR` | `"task.error"` | タスクの実行が失敗したとき |
| `TASK_RETRY_PREFIX` | `"task.retry."` | リトライプレフィックス（リトライ回数を連結） |
| `TASK_DUPLICATE` | `"task.duplicate"` | 重複タスクが検出されたとき |
| `TERMINATION_INPUT` | `"termination.input"` | 終了シグナルが注入されたとき |
| `TERMINATION_MERGE` | `"termination.merge"` | 終了シグナルがマージされたとき |

## PersistedErrorRecord

永続化エラーレコードデータクラスです。

```python
@dataclass(frozen=True)
class PersistedErrorRecord:
    error_type: str          # エラータイプ名
    error_message: str       # エラーメッセージ
    error_repr: str          # エラーの完全な表示文字列
    stage: str               # エラーが属するノードラベル
    error_id: int | None     # エラーイベント ID
    timestamp: str           # エラータイムスタンプ文字列
    ts: float | None         # エラータイムスタンプ

    def __str__(self) -> str: ...
    def get_group_key(self) -> tuple[str, str]:
        """グループ化に使用する (error_type, error_message) を返します。"""
```

## 使用例

以下は `util_types` モジュール内の各データクラスとユーティリティクラスの典型的な使用方法を示します。

### TerminationSignal と TerminationIdPool

```python
from celestialflow.runtime.util_types import TerminationSignal, TERMINATION_SIGNAL, TerminationIdPool

# カスタム終了シグナルを作成
signal = TerminationSignal(_id=42, source="my_source")
print(f"シグナル ID: {signal.id}, ソース: {signal.source}")

# グローバルシングルトンを使用
print(f"デフォルト終了シグナル ID: {TERMINATION_SIGNAL.id}")      # -1
print(f"デフォルトソース: {TERMINATION_SIGNAL.source}")         # "input"
print(f"同一インスタンスか: {TERMINATION_SIGNAL is TerminationSignal()}")  # False（毎回新しいインスタンスを作成）

# 終了シグナル ID プールを作成
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

# ValueWrapper：オプションのロック付きカウンター
counter = ValueWrapper(value=10)
print(f"初期値: {counter.value}")  # 10
with counter.get_lock():
    counter.value += 5
print(f"ロック付きでインクリメント後: {counter.value}")  # 15

# SumCounter：複数カウンターの累積
sum_counter = SumCounter(mode="serial")
sum_counter.add_init_value(100)

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

# 空のコンテキストマネージャー、with ロジックを無効化するために使用
ctx = NoOpContext()
with ctx:
    print("これは操作なしのコンテキストです")
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

### PersistedErrorRecord

```python
from celestialflow.runtime.util_types import PersistedErrorRecord

# 永続化エラーレコードを作成
record = PersistedErrorRecord(
    error_type="ValueError",
    error_message="Invalid input: negative value",
    error_repr="ValueError: Invalid input: negative value",
    stage="StageA",
    error_id=123,
    timestamp="2026-05-24T10:30:00",
    ts=1716546600.0,
)

print(f"エラータイプ: {record.error_type}")
print(f"エラーメッセージ: {record.error_message}")
print(f"所属ノード: {record.stage}")
print(f"文字列表現: {record}")

# グループキーを取得（タイプ+メッセージ別グループ統計用）
group_key = record.get_group_key()
print(f"グループキー: {group_key}")  # ("ValueError", "Invalid input: negative value")
```

## STAGE_STYLE

CelestialTree 可視化用のノードラベルスタイル設定です。

```python
from celestialtree import NodeLabelStyle

STAGE_STYLE = NodeLabelStyle(
    template="{base}  {payload.name}  ‹{type}›",
    missing="-"
)
```
