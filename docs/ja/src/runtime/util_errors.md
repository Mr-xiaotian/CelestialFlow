# TaskErrors

> 📅 最終更新日: 2026/05/28

TaskErrors モジュールは、CelestialFlow フレームワークで使用される完全なカスタム例外体系を定義します。

## 例外階層

```
CelestialFlowError
├── ConfigurationError
│   └── InvalidOptionError
│       ├── ExecutionModeError      # ("serial", "thread", "async")
│       ├── StageModeError          # ("serial", "thread")
│       ├── LogLevelError           # (TRACE/DEBUG/SUCCESS/INFO/...)
│       └── ScheduleModeError       # ("eager", "staged")
├── GraphStructureError
│   ├── DuplicateNodeError          # 重複ノード名
│   └── UnknownNodeError            # 不明なノード名
├── RuntimeStateError
│   ├── InitializationError         # 初期化失敗
│   └── GraphManagedError           # グラフ管理エラー
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

すべてのカスタム例外の基底クラス。

```python
class CelestialFlowError(Exception):
    """CelestialFlow のすべてのカスタム例外の基底クラス"""
    pass
```

## 設定関連例外（ConfigurationError）

### ConfigurationError

設定エラーの基底クラス（不正なパラメータ、サポートされない組み合わせなど）。

```python
class ConfigurationError(CelestialFlowError):
    """設定エラー（不正なパラメータ、サポートされない組み合わせなど）"""
    pass
```

### InvalidOptionError

設定項目の値が不正。

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

グラフ構造エラーの基底クラス。

```python
class GraphStructureError(ConfigurationError):
    """グラフ構造エラー"""
    pass
```

### DuplicateNodeError

重複ノード名（`set_stages` または `add_source_name` / `add_queue` で発生）。

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

## ランタイム例外（RuntimeStateError）

### RuntimeStateError

ランタイム状態エラーの基底クラス（重複起動、未初期化など）。

```python
class RuntimeStateError(CelestialFlowError):
    """ランタイム状態エラー"""
    pass
```

### InitializationError

初期化エラー（例：スレッドプールが初期化されていない場合）。

```python
class InitializationError(RuntimeStateError):
    """初期化エラー"""
    pass
```

### GraphManagedError

グラフ管理エラー（グラフの起動/停止ライフサイクルで不正な操作が発生した場合に発火）。

```python
class GraphManagedError(RuntimeStateError):
    """グラフ管理エラー"""
    pass
```

## 外部サービス例外

### RemoteWorkerError

リモート Worker（例：Go Worker）の実行失敗時にスロー。

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

## その他のランタイム例外

### CelestialFlowTimeoutError

タイムアウトエラー（組み込み `TimeoutError` を継承）。

```python
class CelestialFlowTimeoutError(CelestialFlowError, TimeoutError):
    """タイムアウトエラー"""
    pass
```

### UnconsumedError

未消費タスクをマーク。

```python
class UnconsumedError(CelestialFlowError):
    """未消費タスクをマークするための例外クラス"""
    pass
```

`TaskGraph._finalize_nodes()` がキューに残存タスクを発見した場合、それらは `UnconsumedError` としてマークされ永続化されます。

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

## 使用シーン

### 1. リトライ可能な例外の追加

```python
executor = TaskExecutor("Processor", process, max_retries=3)
executor.add_retry_exceptions(ConnectionError, TimeoutError)
```

### 2. 設定エラーのキャッチ

```python
from celestialflow.runtime.util_errors import ExecutionModeError

try:
    stage.set_execution_mode("invalid_mode")
except ExecutionModeError as e:
    print(f"不正な実行モード: {e.execution_mode}")
    print(f"有効なオプション: {e.valid_modes}")
```

### 3. グラフ構造の検証

```python
from celestialflow.runtime.util_errors import DuplicateNodeError

try:
    graph.set_stages([stage_a, stage_a])  # 重複ノード名
except DuplicateNodeError as e:
    print(f"重複ノード: {e}")
```

## 使用例

以下に、CelestialFlow の各例外の raise と catch の典型的なパターンを示します。

### 設定例外

```python
from celestialflow.runtime.util_errors import (
    ExecutionModeError,
    StageModeError,
    LogLevelError,
    ScheduleModeError,
    InvalidOptionError,
)

# ExecutionModeError のキャッチ
try:
    stage.set_execution_mode("invalid")
except ExecutionModeError as e:
    print(f"フィールド: {e.field}")          # execution_mode
    print(f"値: {e.value}")                 # invalid
    print(f"許可値: {e.allowed}")           # ('serial', 'thread', 'async')

# StageModeError のキャッチ
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

graph = TaskGraph()

stage_a = TaskStage("A", func=lambda x: x)
stage_b = TaskStage("A", func=lambda x: x * 2)  # 重複ノード名

try:
    graph.set_stages([stage_a, stage_b])
except DuplicateNodeError as e:
    print(f"重複ノード: {e}")

try:
    from celestialflow.runtime.util_types import TerminationSignal
    in_queue = list(graph.stage_dict.values())[0].in_queue
    in_queue._record_termination(TerminationSignal(source="unknown_source"))
except UnknownNodeError as e:
    print(f"不明なソース: {e}")
```

### ランタイム例外とタイムアウト例外

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

### TaskExecutor との統合

```python
from celestialflow import TaskExecutor
from celestialflow.runtime.util_errors import CelestialFlowError

# 実際のエグゼキューターでは例外は統一的にキャッチされ記録される
executor = TaskExecutor(
    "SafeWorker",
    func=lambda x: 10 // x,
    execution_mode="serial",
    max_retries=0,
)
executor.start([1, 0, 2])  # 中間のタスクが ZeroDivisionError を発生

counts = executor.get_counts()
print(f"成功: {counts['tasks_succeeded']}, 失敗: {counts['tasks_failed']}")
```

## エラー永続化

`TaskGraph` は `_finalize_nodes()` で未処理エラーをローカル JSONL ファイルに永続化します（`FailSpout` 経由）。各エラーレコードには、エラータイプ、メッセージ、Stage、イベント ID、タイムスタンプが含まれ、`PersistedErrorRecord` で表現されます。
