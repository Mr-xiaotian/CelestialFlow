# TaskErrors

> 📅 最終更新日: 2026/05/09

TaskErrors モジュールは、フレームワークで使用されるカスタム例外クラスを定義します。

## 例外階層

```
CelestialFlowError
├── ConfigurationError
│   └── InvalidOptionError
│       ├── ExecutionModeError
│       ├── StageModeError
│       ├── LogLevelError
│       └── ScheduleModeError
├── RemoteWorkerError
├── CelestialTreeConnectionError
├── UnconsumedError
```

## 基底クラス

### CelestialFlowError

すべてのカスタム例外の基底クラス。

```python
class CelestialFlowError(Exception):
    """CelestialFlow のすべてのカスタム例外の基底クラス"""
    pass
```

## 設定関連例外

### ConfigurationError

設定エラーの基底クラス（不正なパラメータ、サポートされない組み合わせなど）。

```python
class ConfigurationError(CelestialFlowError):
    """設定エラー基底クラス"""
    pass
```

### InvalidOptionError

設定項目の値が不正（許可された集合に含まれていない）。

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
        :param allowed: 許可される値のリスト
        :param prefix: エラーメッセージのプレフィックス
        """
```

### ExecutionModeError

`execution_mode` の設定エラー。

```python
class ExecutionModeError(InvalidOptionError):
    """不正な execution_mode 設定エラー"""

    def __init__(self, execution_mode: str, valid_modes=None):
        # valid_modes のデフォルトは ("serial", "thread", "async")
```

### StageModeError

`stage_mode` の設定エラー。

```python
class StageModeError(InvalidOptionError):
    """不正な stage_mode 設定エラー"""

    def __init__(self, stage_mode: str, valid_modes=None):
        # valid_modes のデフォルトは ("serial", "thread")
```

### LogLevelError

`log_level` の設定エラー。

```python
class LogLevelError(InvalidOptionError):
    """不正な log_level 設定エラー"""

    def __init__(self, log_level: str, valid_levels=None):
        # valid_levels のデフォルトは ("TRACE", "DEBUG", "SUCCESS", "INFO", "WARNING", "ERROR", "CRITICAL")
```

## ランタイム例外

### RemoteWorkerError

リモートワーカー（例：Go Worker）の実行失敗時にスローされる例外。

```python
class RemoteWorkerError(CelestialFlowError):
    pass
```

### ScheduleModeError

`schedule_mode` の設定エラー。

```python
class ScheduleModeError(InvalidOptionError):
    """不正な schedule_mode 設定エラー"""

    def __init__(self, schedule_mode: str, valid_modes=None):
        # valid_modes のデフォルトは ("eager", "staged")
```

### CelestialTreeConnectionError

CelestialTree 接続エラー。

```python
class CelestialTreeConnectionError(CelestialFlowError):
    def __init__(self, message: str = "CelestialTreeClient is not available"):
        ...
```

### UnconsumedError

未消費タスクをマークするための例外クラス。

```python
class UnconsumedError(CelestialFlowError):
    """未消費タスクをマークするための例外クラス"""
    pass
```

`TaskGraph` が停止する際、すべての未消費タスクを収集し `UnconsumedError` として記録します。

## エラーハンドリング戦略

`TaskExecutor` では、例外は2つのカテゴリに分類されます：

1. **リトライ可能な例外**: 例外タイプが `retry_exceptions` リストに含まれ、リトライ回数上限に達していない場合、フレームワークが自動的にタスクをリトライします。
2. **リトライ不可能な例外**: タスクは失敗としてマークされ、エラーログが記録され、`fail_queue` に配置されます。

## エラー永続化

`TaskGraph` は、すべての未処理エラー（リトライ失敗と UnconsumedError を含む）を自動的にローカルの `fallback/` ディレクトリに JSONL 形式で永続化します。

各エラーレコードには以下が含まれます：
- タイムスタンプ
- ステージタグ
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
)

try:
    stage.set_execution_mode("invalid_mode")
except ExecutionModeError as e:
    print(f"不正な実行モード: {e.execution_mode}")
    print(f"有効なオプション: {e.valid_modes}")
```

### リトライ可能な例外の追加

```python
executor = TaskExecutor("Processor", process, max_retries=3)
executor.add_retry_exceptions(ConnectionError, TimeoutError)
```

## 注意事項

1. **エラー伝播**: `RemoteWorkerError` にはリモートワーカーが返したエラー情報が含まれる
2. **ログ記録**: すべての例外がログに記録される
3. **グレースフルデグラデーション**: 例外が発生しても、フレームワークはリソースの適切なクリーンアップを試みる
