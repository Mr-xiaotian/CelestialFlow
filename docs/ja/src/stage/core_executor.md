# TaskExecutor

> 📅 最終更新日: 2026/05/15

`TaskExecutor` は単一タスクロジックを実行するコアコンポーネントです。タスクの実行、並行制御、エラーハンドリング、リトライメカニズム、ログ記録を担当します。

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
        log_level="INFO",
    ):
        ...
```

### パラメータ説明

- **name**: エグゼキューター名、ログとトレースに使用。
- **func**: タスクを実際に実行する呼び出し可能オブジェクト（関数）。
- **execution_mode**: 実行モード。
  - `serial`: シリアル実行。
  - `thread`: マルチスレッド実行。
  - `async`: 非同期実行（`asyncio`）。
- **max_workers**: 並行数制限（スレッド数/コルーチン数）。
- **max_retries**: タスク失敗後の最大リトライ回数。
- **max_info**: ログメッセージの最大長。
- **unpack_task_args**: タスク引数を関数に渡す際に展開（`*args`）するかどうか。
- **enable_duplicate_check**: ハッシュベースの重複チェックの有効化。
- **log_level**: ログレベル（TRACE/DEBUG/SUCCESS/INFO/WARNING/ERROR/CRITICAL）。

## Observer パターン

`TaskExecutor` は Observer パターンを通じてライフサイクルイベントを外部にブロードキャストします。

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

| イベント | 発火タイミング |
|---------|--------------|
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
    エグゼキューターを起動し、task_source 内のすべてのタスクを処理します。
    execution_mode に基づいて適切な実行戦略を選択します。
    """
```

### start_async

```python
async def start_async(self, task_source: Iterable):
    """
    エグゼキューターを非同期起動します（async モード用）。
    """
```

## エラーハンドリング

`TaskExecutor` はタスク実行中の例外をキャッチします：
- 例外が `retry_exceptions` リストに含まれ、最大リトライ回数に達していない場合、タスクをキューに戻してリトライします。
- それ以外の場合、タスクを失敗としてマークし、エラーログを記録し、`fail_queue` に配置します。

### add_retry_exceptions

```python
def add_retry_exceptions(self, *exceptions):
    """
    リトライが必要な例外タイプを追加します。

    :param exceptions: 例外タイプのリスト
    """
```

例：
```python
executor = TaskExecutor("Processor", process, max_retries=3)
executor.add_retry_exceptions(ValueError, ConnectionError, TimeoutError)
```

## 結果処理

### オーバーライド可能なメソッド

- **process_result(task, result)**: このメソッドをオーバーライドして結果処理ロジックをカスタマイズできます。
- **get_args(task)**: このメソッドをオーバーライドして引数抽出ロジックをカスタマイズできます。

### 結果の取得

```python
# 成功結果リストを取得
def get_success_pairs(self) -> list[tuple[Any, Any]]:
    ...

# 失敗結果リストを取得
def get_error_pairs(self) -> list[tuple[Any, Exception]]:
    ...
```

### 結果辞書の処理

```python
# 結果辞書を処理（成功と失敗をマージ）
def process_result_dict(self) -> dict:
    ...

# エラー辞書を処理（エラータイプ別にグループ化）
def handle_error_dict(self) -> dict:
    ...
```

## CelestialTree 統合

`TaskExecutor` は CelestialTree イベントトラッキングシステムをサポートし、タスクのトレースとデバッグに使用されます。

### set_ctree

```python
def set_ctree(self, host: str = "127.0.0.1", http_port: int = 7777, grpc_port: int = 7778):
    """
    CelestialTree クライアント接続を設定します。

    :param host: CelestialTree サービスホストアドレス
    :param http_port: HTTP ポート
    :param grpc_port: gRPC ポート
    """
```

### set_nullctree

```python
def set_nullctree(self, event_id=None):
    """
    Null クライアントを設定します（外部サービスに接続せず、イベント ID のみ生成）。

    :param event_id: オプションのイベント ID
    """
```

## 状態クエリメソッド

### 基本情報の取得

```python
# エグゼキューター名を取得
def get_name(self) -> str: ...

# 関数名を取得
def get_func_name(self) -> str: ...

# クラス名を取得（プライベート）
def _get_class_name(self) -> str: ...

# タグを取得（ログとトレース用）
def get_tag(self) -> str: ...

# 実行モード説明を取得（プライベート）
def _get_execution_mode_desc(self) -> str: ...
```

### 状態スナップショットの取得

```python
def get_summary(self) -> dict:
    """
    現在のノードの状態スナップショットを取得します。
    返却値：name, func_name, class_name, execution_mode
    """

def get_counts(self) -> dict:
    """
    現在のノードのカウンターを取得します。
    返却値：tasks_input, tasks_succeeded, tasks_failed, tasks_duplicated, tasks_processed, tasks_pending
    """
```

## ランタイム情報

### get_task_repr

```python
def get_task_repr(self, task) -> str:
    """
    タスク引数の可読文字列表現を取得します。
    ログ出力に使用され、長すぎる引数は自動的に切り詰められます。
    """
```

### _get_result_repr

```python
def _get_result_repr(self, result) -> str:
    """
    結果の可読文字列表現を取得します。
    """
```

## 注意事項

### 実行モード選択

| モード | 適用シナリオ | 注意事項 |
|-------|------------|---------|
| `serial` | デバッグ、シンプルなタスク | 並行性なし |
| `thread` | I/O 集約型 | GIL 制限に注意 |
| `async` | ネットワーク I/O | start_async の使用が必要 |
