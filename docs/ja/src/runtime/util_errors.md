# TaskErrors

> 📅 最終更新日: 2026/04/23

TaskErrors モジュールは、フレームワークで使用されるカスタム例外クラスを定義します。

## 例外階層

```
CelestialFlowError
├── ConfigurationError
│   └── InvalidOptionError
│       ├── ExecutionModeError
│       ├── StageModeError
│       └── LogLevelError
├── RemoteWorkerError
├── UnconsumedError
└── PickleError
```

## 基底クラス

### CelestialFlowError

すべてのカスタム例外の基底クラスです。

```python
class CelestialFlowError(Exception):
    """CelestialFlow のすべてのカスタム例外の基底クラス"""
    pass
```

## 設定関連の例外

### ConfigurationError

設定エラーの基底クラスです（不正なパラメータ、サポートされていない組み合わせなど）。

```python
class ConfigurationError(CelestialFlowError):
    """設定エラーの基底クラス"""
    pass
```

### InvalidOptionError

設定項目の値が許可されたセットに含まれていない場合に発生します。

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
        :param value: 実際の値
        :param allowed: 許可された値のリスト
        :param prefix: エラーメッセージのプレフィックス
        """
```

### ExecutionModeError

`execution_mode` の設定エラーです。

```python
class ExecutionModeError(InvalidOptionError):
    """不正な execution_mode の設定エラー"""

    def __init__(self, execution_mode: str, valid_modes=None):
        # valid_modes のデフォルトは ("serial", "process", "thread", "async")
```

### StageModeError

`stage_mode` の設定エラーです。

```python
class StageModeError(InvalidOptionError):
    """不正な stage_mode の設定エラー"""

    def __init__(self, stage_mode: str, valid_modes=None):
        # valid_modes のデフォルトは ("serial", "process")
```

### LogLevelError

`log_level` の設定エラーです。

```python
class LogLevelError(InvalidOptionError):
    """不正な log_level の設定エラー"""

    def __init__(self, log_level: str, valid_levels=None):
        # valid_levels のデフォルトは ("TRACE", "DEBUG", "SUCCESS", "INFO", "WARNING", "ERROR", "CRITICAL")
```

## ランタイム例外

### RemoteWorkerError

リモートワーカー（例: Go Worker）の実行が失敗した場合にスローされる例外です。

```python
class RemoteWorkerError(CelestialFlowError):
    pass
```

### UnconsumedError

タスクが未消費であることを示す例外クラスです。

```python
class UnconsumedError(CelestialFlowError):
    """タスクが未消費であることを示す例外クラス"""
    pass
```

`TaskGraph` が停止する際、すべての未消費タスクを収集し、`UnconsumedError` として記録します。

### PickleError

タスク関数またはその引数が pickle シリアライズできない場合に発生するエラーです。

```python
class PickleError(CelestialFlowError):
    """
    タスク関数またはその引数が pickle シリアライズできない場合のエラー。
    """

    def __init__(self, obj: Any):
        message = f"Object of type {type(obj).__name__} is not pickleable."
        super().__init__(message)
        self.obj = obj
        self.type = type(obj).__name__
        self.message = message
```

`TaskStage.set_func()` では、関数が pickle 可能かどうかをチェックします:

```python
from celestialflow.runtime.util_errors import PickleError
from celestialflow.utils.util_debug import find_unpickleable

if find_unpickleable(func):
    raise PickleError(func)
```

## エラーハンドリング戦略

`TaskExecutor` では、例外は2つのタイプに分類されます:

1. **リトライ可能な例外**: 例外タイプが `retry_exceptions` リストに含まれており、リトライ回数が上限に達していない場合、フレームワークは自動的にタスクをリトライします。
2. **リトライ不可能な例外**: タスクは失敗としてマークされ、エラーログが記録され、`fail_queue` に入れられます。

## エラーの永続化

`TaskGraph` は、すべての未処理エラー（リトライ失敗や UnconsumedError を含む）をローカルの `fallback/` ディレクトリに JSONL 形式で自動的に永続化します。

各エラーレコードには以下が含まれます:
- タイムスタンプ
- Stage タグ
- エラーメッセージ
- 元のタスクデータ
- エラー ID

## 使用例

### 特定の例外のキャッチ

```python
from celestialflow.runtime.util_errors import (
    ExecutionModeError,
    StageModeError,
    RemoteWorkerError,
    PickleError,
)

try:
    stage.set_execution_mode("invalid_mode")
except ExecutionModeError as e:
    print(f"無効な実行モード: {e.execution_mode}")
    print(f"有効なオプション: {e.valid_modes}")
```

### リトライ可能な例外の追加

```python
executor = TaskExecutor("Processor", process, max_retries=3)
executor.add_retry_exceptions(ConnectionError, TimeoutError)
```

## 注意事項

1. **Pickle チェック**: process モードでは、すべての関数と引数が pickle 可能であることを確認してください
2. **エラー伝搬**: `RemoteWorkerError` にはリモートワーカーが返したエラーメッセージが含まれます
3. **ロギング**: すべての例外がログに記録されます
4. **グレースフルデグラデーション**: 例外が発生した場合でも、フレームワークはリソースの適切なクリーンアップを試みます
