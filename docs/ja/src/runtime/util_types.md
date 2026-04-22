# TaskTypes

TaskTypes モジュールは、フレームワークで使用される基本的なデータ型、列挙型、ヘルパークラスを定義します。

## StageStatus

`TaskStage` の実行状態を表す列挙型クラスです。

```python
class StageStatus(IntEnum):
    NOT_STARTED = 0  # 未開始
    RUNNING = 1      # 実行中
    STOPPED = 2      # 停止済み
```

使用例:
```python
from celestialflow.runtime.util_types import StageStatus

status = stage.get_status()
if status == StageStatus.RUNNING:
    print("ノードは実行中です")
```

## TerminationSignal

タスクキューの終了を示すセンチネルオブジェクトです。Stage がこのシグナルを受信した場合、上流からのタスクがこれ以上ないことを示し、停止の準備をする必要があります。

```python
class TerminationSignal:
    def __init__(self, _id: int = -1, source: str = "input"):
        self.id = _id        # イベント ID
        self.source = source  # ソース

# シングルトン
TERMINATION_SIGNAL = TerminationSignal()
```

### 使用シーン

```python
from celestialflow.runtime import TerminationSignal

# 終了シグナルを注入
queue.put(TerminationSignal())

# 終了シグナルを検出
if isinstance(record, TerminationSignal):
    break  # 処理を停止
```

## TerminationIdPool

終了シグナル ID プール。受信したすべての終了シグナル ID を格納するために使用されます。

```python
class TerminationIdPool:
    def __init__(self, ids: list[int]):
        self.ids = ids
```

## NoOpContext

`with` ブロックのロジックを無効にするために使用できる、何もしないコンテキストマネージャーです。

```python
class NoOpContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
```

使用シーン:
```python
# ロックが不要な場合に NoOpContext を返す
def get_lock(self):
    return self._lock or NoOpContext()
```

## ValueWrapper

オプションのロックサポートを持つ、シングルスレッド/シングルプロセス用のカウンターラッパーです。

```python
class ValueWrapper:
    def __init__(self, value=0, lock=None):
        self.value = value
        self._lock = lock

    def get_lock(self):
        """ロックオブジェクトまたは NoOpContext を返します"""
        return self._lock or NoOpContext()
```

## SumCounter

複数のカウンターを累積します（ValueWrapper / MPValue をサポート）。

```python
class SumCounter:
    def __init__(self, mode: str = "serial"):
        """
        カウンターを初期化します。

        :param mode: モード ('serial', 'thread', 'process')
        """
```

### メソッド

```python
# 初期値を追加
def add_init_value(self, value: int) -> None

# カウンターを追加
def append_counter(self, counter: ValueWrapper) -> None

# すべてのカウンターをリセット
def reset(self) -> None

# 合計値を取得
@property
def value(self) -> int
```

### 使用例

```python
from celestialflow.runtime.util_types import SumCounter, ValueWrapper

# スレッドモード
counter = SumCounter(mode="thread")
counter.add_init_value(10)

# サブカウンターを追加
sub_counter = ValueWrapper(value=5)
counter.append_counter(sub_counter)

print(counter.value)  # 15
```

## STAGE_STYLE

CelestialTree 可視化のためのノードラベルスタイル設定です。

```python
from celestialtree import NodeLabelStyle

STAGE_STYLE = NodeLabelStyle(
    template="{base}  {payload.name}  ‹{type}›",
    missing="-"
)
```

## 例外クラス

例外クラスは `runtime/util_errors.py` で定義されています:

| 例外クラス | 説明 |
|-----------|------|
| `CelestialFlowError` | 基底例外クラス |
| `ConfigurationError` | 設定エラー |
| `InvalidOptionError` | 無効なオプションエラー |
| `ExecutionModeError` | 実行モードエラー |
| `StageModeError` | Stage モードエラー |
| `LogLevelError` | ログレベルエラー |
| `RemoteWorkerError` | リモートワーカーエラー |
| `UnconsumedError` | 未消費タスクエラー |
| `PickleError` | シリアライズエラー |
