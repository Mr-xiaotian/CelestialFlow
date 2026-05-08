# TaskExecutor

> 📅 最終更新日: 2026/05/08

`TaskExecutor` は単一タスクロジックを実行するコアコンポーネントです。タスクの実行、並行制御、エラー処理、リトライ機構、ログ記録を担当します。

## 初期化

```python
class TaskExecutor:
    def __init__(
        self,
        name,
        func,
        execution_mode="serial",
        max_workers=20,
        max_retries=1,
        max_info=50,
        unpack_task_args=False,
        enable_duplicate_check=True,
        log_level="SUCCESS",
    ):
        ...
```

### パラメータ説明

- **name**: エグゼキューター名。ログと追跡に使用。
- **func**: タスクを実行する呼び出し可能オブジェクト（関数）。
- **execution_mode**: 実行モード。
  - `serial`: シリアル実行。
  - `thread`: マルチスレッド実行。
  - `async`: 非同期実行 (`asyncio`)。
- **max_workers**: 並行数制限（スレッド数/コルーチン数）。
- **max_retries**: タスク失敗後の最大リトライ回数。
- **max_info**: ログの各情報の最大長。
- **unpack_task_args**: タスク引数を展開 (`*args`) して関数に渡すかどうか。
- **enable_duplicate_check**: タスクハッシュに基づく重複チェックを有効にするかどうか。
- **log_level**: ログレベル（TRACE/DEBUG/SUCCESS/INFO/WARNING/ERROR/CRITICAL）。

## Observer パターン

`TaskExecutor` は observer パターンを通じて外部にライフサイクルイベントをブロードキャストします。

### 登録と削除

```python
executor.add_observer(observer)     # オブザーバーを登録
executor.remove_observer(observer)  # オブザーバーを削除
```

### 使用例

```python
from celestialflow import TaskExecutor, TaskProgress, CallbackObserver

# TaskProgress でプログレスバーを表示
executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)

# CallbackObserver を使用
observer = CallbackObserver(
    on_task_success=lambda count=1: print(f"成功: {count}"),
)
executor.add_observer(observer)
```

### ブロードキャストイベント

| イベント | トリガー |
|----------|----------|
| `on_start(name, total)` | 実行開始 |
| `on_task_success(count)` | タスク成功 |
| `on_task_fail(count)` | タスク失敗 |
| `on_task_duplicate(count)` | 重複検出 |
| `on_tasks_added(count)` | 新タスク追加 |
| `on_finish()` | 実行終了 |

## コアメソッド

### start

```python
def start(self, task_source: Iterable):
    """
    エグゼキューターを起動し、task_source 内の全タスクを処理。
    execution_mode に応じた実行戦略を選択。
    """
```

### start_async

```python
async def start_async(self, task_source: Iterable):
    """
    非同期でエグゼキューターを起動（async モード用）。
    """
```

## エラー処理

`TaskExecutor` はタスク実行中の例外をキャッチします：
- 例外が `retry_exceptions` リストに含まれ、最大リトライ回数に達していない場合、タスクをリトライ。
- それ以外の場合、タスクを失敗としてマーク、エラーログを記録し `fail_queue` に入れる。

### add_retry_exceptions

```python
def add_retry_exceptions(self, *exceptions):
    """リトライ対象の例外タイプを追加。"""
```

例：
```python
executor = TaskExecutor("Processor", process, max_retries=3)
executor.add_retry_exceptions(ValueError, ConnectionError, TimeoutError)
```

## 結果処理

### オーバーライド可能メソッド

- **process_result(task, result)**: 結果処理ロジックをカスタマイズ。
- **get_args(task)**: パラメータ抽出ロジックをカスタマイズ。

### 結果取得

```python
def get_success_pairs(self) -> list[tuple[Any, Any]]: ...
def get_error_pairs(self) -> list[tuple[Any, Exception]]: ...
def process_result_dict(self) -> dict: ...
def handle_error_dict(self) -> dict: ...
```

## CelestialTree 統合

```python
def set_ctree(self, host="127.0.0.1", http_port=7777, grpc_port=7778): ...
def set_nullctree(self, event_id=None): ...
```

## 状態クエリメソッド

```python
def get_name(self) -> str: ...
def get_func_name(self) -> str: ...
def get_tag(self) -> str: ...
def get_summary(self) -> dict: ...
def get_counts(self) -> dict: ...
def get_task_repr(self, task) -> str: ...
```

## 注意事項

| モード | 適用シナリオ | 注意事項 |
|--------|-------------|----------|
| `serial` | デバッグ、シンプルなタスク | 並行なし |
| `thread` | I/O 密集型 | GIL 制限に注意 |
| `async` | ネットワーク I/O | start_async を使用 |
