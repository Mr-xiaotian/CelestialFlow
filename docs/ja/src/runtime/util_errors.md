# TaskErrors

> 📅 最終更新日: 2026/06/18

TaskErrors モジュールは CelestialFlow フレームワークで使用される完全な例外クラス体系を定義します。

## 例外階層

```
CelestialFlowError
├── ConfigurationError
│   └── InvalidOptionError
│       ├── ExecutionModeError      # ("serial", "thread", "async")
│       ├── StageModeError          # ("serial", "thread")
│       ├── LogLevelError           # (TRACE/DEBUG/SUCCESS/INFO/...)
│       ├── ScheduleModeError       # ("eager", "staged")
│       └── CallableParameterKindError  # 呼び出し可能オブジェクトのパラメータ kind が不正
├── GraphStructureError
│   ├── DuplicateNodeError          # 重複ノード名
│   └── UnknownNodeError            # 不明なノード名
├── RuntimeStateError
│   ├── InitializationError         # 初期化失敗
│   └── GraphManagedError           # グラフ管理エラー
├── PersistedError                  # 永続化エラーサマリ
├── RemoteWorkerError               # リモート Worker 実行失敗
├── ReporterError                   # レポーターエラー
├── CelestialTreeConnectionError    # CelestialTree 接続失敗
├── CelestialFlowTimeoutError       # タイムアウトエラー
├── UnconsumedError                 # 未消費タスクのマーク
├── TaskFormatError                 # タスクフォーマットエラー
└── TerminationMergeError           # 終了シグナルマージエラー
```

## 基底クラス

### CelestialFlowError

全カスタム例外の基底クラスです。

```python
class CelestialFlowError(Exception):
    """CelestialFlow 全カスタム例外の基底クラス"""
    pass
```

## 設定関連例外（ConfigurationError）

### ConfigurationError

設定エラー基底クラス（不正なパラメータ、サポートされない組み合わせなど）。

```python
class ConfigurationError(CelestialFlowError):
    """設定エラー（不正なパラメータ、サポートされない組み合わせなど）"""
    pass
```

### InvalidOptionError

特定の設定項目の値が不正です。

```python
class InvalidOptionError(ConfigurationError):
    def __init__(
        self,
        field: str,
        value: Any,
        allowed: Iterable[Any],
        *,
        prefix: str = "Invalid",
    ):
        """
        :param field: 設定項目名
        :param value: 実際に渡された値
        :param allowed: 許可される値の集合
        :param prefix: エラーメッセージのプレフィックス
        """
        # 例: "Invalid execution mode: xxx. Valid options are ('serial', 'thread', 'async')."
```

### ExecutionModeError

`execution_mode` 設定エラー。

```python
class ExecutionModeError(InvalidOptionError):
    """不正な execution_mode"""
    def __init__(self, execution_mode: str, valid_modes=None):
        # valid_modes のデフォルトは ("serial", "thread", "async")
```

### StageModeError

`stage_mode` 設定エラー。

```python
class StageModeError(InvalidOptionError):
    """不正な stage_mode"""
    def __init__(self, stage_mode: str, valid_modes=None):
        # valid_modes のデフォルトは ("serial", "thread")
```

### LogLevelError

`log_level` 設定エラー。

```python
class LogLevelError(InvalidOptionError):
    """不正な log_level"""
    def __init__(self, log_level: str, valid_levels=None):
        # valid_levels のデフォルトは ("TRACE", "DEBUG", "SUCCESS", "INFO", "WARNING", "ERROR", "CRITICAL")
```

### ScheduleModeError

`schedule_mode` 設定エラー。

```python
class ScheduleModeError(InvalidOptionError):
    """不正な schedule_mode"""
    def __init__(self, schedule_mode: str, valid_modes=None):
        # valid_modes のデフォルトは ("eager", "staged")
```

## グラフ構造例外（GraphStructureError）

### GraphStructureError

グラフ構造エラー基底クラス。

```python
class GraphStructureError(ConfigurationError):
    """グラフ構造エラー"""
    pass
```

### DuplicateNodeError

重複ノード名（`set_stages` または `add_source_name` / `add_queue` 時に発生）。

```python
class DuplicateNodeError(GraphStructureError):
    """重複ノード名"""
    pass
```

### UnknownNodeError

不明なノード名（終了シグナルソースの検証時に発生）。

```python
class UnknownNodeError(GraphStructureError):
    """不明なノード名"""
    pass
```

## 実行時例外（RuntimeStateError）

### RuntimeStateError

実行時状態エラー基底クラス（重複起動、未初期化など）。

```python
class RuntimeStateError(CelestialFlowError):
    """実行時状態エラー"""
    pass
```

### InitializationError

初期化エラー（スレッドプールが未初期化の状態で使用された場合など）。

```python
class InitializationError(RuntimeStateError):
    """初期化エラー"""
    pass
```

### GraphManagedError

Stage が既に TaskGraph によって管理されている場合に、スタンドアロン経路で直接 `start()` を呼び出そうとすると送出されます。

```python
class GraphManagedError(RuntimeStateError):
    """Stage は既に Graph に管理されています。スタンドアロン経路で起動すべきではありません。"""
    def __init__(self, message: str = "This stage is managed by a TaskGraph. ..."):
        ...
```

### CallableParameterKindError

呼び出し可能オブジェクトのパラメータ kind が不正です。

```python
class CallableParameterKindError(InvalidOptionError):
    def __init__(self, callable_name: str, parameter_kind: Any, valid_kinds: Iterable[Any]):
        """
        :param callable_name: 呼び出し可能オブジェクト名
        :param parameter_kind: 実際のパラメータ kind
        :param valid_kinds: 許可されるパラメータ kind の集合
        """
```

## 永続化例外

### PersistedError

永続化層から復元されたエラーサマリオブジェクト。

```python
class PersistedError(CelestialFlowError):
    def __init__(self, error_type: str, error_message: str) -> None:
        self.error_type = error_type
        self.error_message = error_message

    def __str__(self) -> str:
        """``ErrorType(message)`` 形式のコンパクトな表現を返します。"""
```

## 外部サービス例外

### RemoteWorkerError

リモート Worker（Go Worker など）の実行失敗時に送出されます。

```python
class RemoteWorkerError(CelestialFlowError):
    """リモート Worker 実行失敗"""
    pass
```

### ReporterError

レポーターエラー。

```python
class ReporterError(CelestialFlowError):
    """レポーターエラー"""
    pass
```

### CelestialTreeConnectionError

CelestialTree クライアント接続失敗。

```python
class CelestialTreeConnectionError(CelestialFlowError):
    def __init__(self, message: str = "CelestialTreeClient is not available"):
        ...
```

## その他の実行時例外

### CelestialFlowTimeoutError

タイムアウトエラー（組み込み `TimeoutError` を継承）。

```python
class CelestialFlowTimeoutError(CelestialFlowError, TimeoutError):
    """タイムアウトエラー"""
    pass
```

### UnconsumedError

未消費タスクをマークします。

```python
class UnconsumedError(CelestialFlowError):
    """タスク未消費をマークする例外クラス"""
    pass
```

`TaskGraph._finalize_nodes()` がキュー内に残存タスクを検出した場合、それらを `UnconsumedError` としてマークし永続化します。

### TaskFormatError

タスクフォーマットエラー。

```python
class TaskFormatError(CelestialFlowError):
    """タスクフォーマットエラー"""
    pass
```

### TerminationMergeError

終了シグナルマージエラー（上流の終了シグナルが不足している場合に発生）。

```python
class TerminationMergeError(CelestialFlowError):
    """終了シグナルマージエラー"""
    pass
```

## 使用シナリオ

### 1. リトライ可能例外の追加

```python
executor = TaskExecutor("Processor", process, max_retries=3)
executor.add_retry_exceptions(ConnectionError, TimeoutError)
```

### 2. 設定エラーの捕捉

```python
from celestialflow.runtime.util_errors import ExecutionModeError

try:
    stage.set_execution_mode("invalid_mode")
except ExecutionModeError as e:
    print(f"無効な実行モード: {e.execution_mode}")
    print(f"有効なオプション: {e.valid_modes}")
```

### 3. グラフ構造検証

```python
from celestialflow.runtime.util_errors import DuplicateNodeError

try:
    graph.set_stages([stage_a, stage_a])  # 同名ノード
except DuplicateNodeError as e:
    print(f"重複ノード: {e}")
```

## 使用例

以下の例は CelestialFlow の各種例外の raise と catch の典型的な使用方法を示します。

### 設定例外

```python
from celestialflow.runtime.util_errors import (
    ExecutionModeError,
    StageModeError,
    LogLevelError,
    ScheduleModeError,
    InvalidOptionError,
)

# ExecutionModeError の捕捉
try:
    stage.set_execution_mode("invalid")
except ExecutionModeError as e:
    print(f"フィールド: {e.field}")          # execution_mode
    print(f"渡された値: {e.value}")        # invalid
    print(f"有効な値: {e.allowed}")      # ('serial', 'thread', 'async')

# StageModeError の捕捉
try:
    stage.set_stage_mode("invalid")
except StageModeError as e:
    print(f"設定エラー: {e}")

# InvalidOptionError の直接使用
try:
    raise InvalidOptionError(
        field="strategy",
        value="aggressive",
        allowed=("conservative", "balanced"),
    )
except InvalidOptionError as e:
    print(f"エラー: {e}")
```

### グラフ構造例外

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.runtime.util_errors import DuplicateNodeError, UnknownNodeError

graph = TaskGraph(name="ErrorTestGraph")

stage_a = TaskStage("A", func=lambda x: x)
stage_b = TaskStage("A", func=lambda x: x * 2)  # 同名ノード

try:
    graph.set_stages([stage_a, stage_b])
except DuplicateNodeError as e:
    print(f"重複ノード: {e}")

try:
    from celestialflow.runtime.util_types import TerminationSignal
    # UnknownNodeError は in_queue._record_termination のソース検証時に発生
    from celestialflow.runtime import TaskInQueue
    from queue import Queue
    in_queue = TaskInQueue(queue=Queue(), source_names=["known"], out_name="test")
    in_queue._record_termination(TerminationSignal(source="unknown_source"))
except UnknownNodeError as e:
    print(f"不明なソース: {e}")
```

### 実行時例外とタイムアウト例外

```python
from celestialflow.runtime.util_errors import (
    RuntimeStateError,
    CelestialFlowTimeoutError,
    UnconsumedError,
    TaskFormatError,
    TerminationMergeError,
)

# タイムアウトエラー（組み込み TimeoutError を継承）
try:
    raise CelestialFlowTimeoutError("Task execution timed out after 30s")
except CelestialFlowTimeoutError as e:
    print(f"タイムアウト: {e}")

# タスクフォーマットエラー
try:
    raise TaskFormatError("Expected (target, data) tuple, got str")
except TaskFormatError as e:
    print(f"フォーマットエラー: {e}")

# 終了シグナルマージエラー
try:
    raise TerminationMergeError("Missing termination from source: B")
except TerminationMergeError as e:
    print(f"マージエラー: {e}")
```

### 外部サービス例外

```python
from celestialflow.runtime.util_errors import (
    RemoteWorkerError,
    CelestialTreeConnectionError,
)

try:
    raise RemoteWorkerError("Go worker returned status code 500")
except RemoteWorkerError as e:
    print(f"リモート Worker エラー: {e}")

try:
    raise CelestialTreeConnectionError("Cannot connect to 127.0.0.1:7777")
except CelestialTreeConnectionError as e:
    print(f"接続失敗: {e}")
```

### TaskExecutor との連携

```python
from celestialflow import TaskExecutor
from celestialflow.runtime.util_errors import CelestialFlowError

# 実際のエグゼキュータでは、例外は統一的に捕捉され記録されます
executor = TaskExecutor(
    "SafeWorker",
    func=lambda x: 10 // x,
    execution_mode="serial",
    max_retries=0,
)
executor.start([1, 0, 2])  # 中間タスクで ZeroDivisionError が発生

counts = executor.get_counts()
print(f"成功: {counts['tasks_succeeded']}, 失敗: {counts['tasks_failed']}")
```

## 例外の永続化

`TaskGraph` は `_finalize_nodes()` 内で未処理エラーをローカル JSONL ファイルに永続化します（`FallbackSpout` 経由）。各エラーレコードはエラー型、メッセージ、所属 Stage、イベント ID、タイムスタンプを含み、`PersistedErrorRecord` で表現されます。
