# TaskExecutor

> 📅 最終更新日: 2026/04/23

`TaskExecutor` は、単一タスクのロジックを実行するコアコンポーネントです。タスクの実行、並行制御、エラーハンドリング、リトライ機構、およびログ記録を担当します。

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
        enable_success_cache=False,
        enable_duplicate_check=True,
        show_progress=False,
        progress_desc="Executing",
        log_level="SUCCESS",
    ):
        ...
```

### パラメータ説明

- **name**: エグゼキューターの名前。ログとトレースに使用されます。
- **func**: タスクを実際に実行するコーラブルオブジェクト（関数）。
- **execution_mode**: 実行モード。
  - `serial`: 逐次実行。
  - `thread`: マルチスレッド実行。
  - `process`: マルチプロセス実行（注意: `TaskGraph` の一部として使用する場合、通常このモードは使用せず、`TaskStage` が管理します）。
  - `async`: 非同期実行 (`asyncio`)。
- **max_workers**: 並行数の制限（スレッド数/プロセス数/コルーチン数）。
- **max_retries**: タスク失敗後の最大リトライ回数。
- **max_info**: ログ内の各メッセージの最大長。
- **unpack_task_args**: タスク引数を展開 (`*args`) して関数に渡すかどうか。
- **enable_success_cache**: 成功結果を `success_dict` にキャッシュするかどうか。
- **enable_duplicate_check**: タスクのハッシュベースの重複チェックを有効にするかどうか。
- **show_progress**: プログレスバーを表示するかどうか。
- **progress_desc**: プログレスバーの表示名。
- **log_level**: ログレベル（TRACE/DEBUG/SUCCESS/INFO/WARNING/ERROR/CRITICAL）。

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
    エグゼキューターを非同期的に起動します（async モード用）。
    """
```

## エラーハンドリング

`TaskExecutor` はタスク実行中の例外をキャッチします：
- 例外が `retry_exceptions` リストに含まれ、最大リトライ回数に達していない場合、タスクはリトライのためにキューに再投入されます。
- そうでない場合、タスクは失敗としてマークされ、エラーログが記録され、`fail_queue` に配置されます。

### add_retry_exceptions

```python
def add_retry_exceptions(self, *exceptions):
    """
    リトライをトリガーする例外タイプを追加します。

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
# 成功結果ペアを取得（enable_success_cache=True が必要）
def get_success_pairs(self) -> list[tuple[Any, Any]]:
    ...

# 失敗結果ペアを取得
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

`TaskExecutor` は、タスクの追跡とデバッグのための CelestialTree イベント追跡システムをサポートしています。

### set_ctree

```python
def set_ctree(self, host: str = "127.0.0.1", http_port: int = 7777, grpc_port: int = 7778):
    """
    CelestialTree クライアント接続を設定します。

    :param host: CelestialTree サービスのホストアドレス
    :param http_port: HTTP ポート
    :param grpc_port: gRPC ポート
    """
```

### set_nullctree

```python
def set_nullctree(self, event_id=None):
    """
    Null クライアントを設定します（外部サービスに接続せず、イベント ID のみを生成します）。

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

# タグを取得（ログと追跡に使用）
def get_tag(self) -> str: ...

# 実行モードの説明を取得（プライベート）
def _get_execution_mode_desc(self) -> str: ...
```

### 状態スナップショットの取得

```python
def get_summary(self) -> dict:
    """
    現在のノードの状態スナップショットを取得します。
    返却値: name, func_name, class_name, execution_mode
    """

def get_counts(self) -> dict:
    """
    現在のノードのカウンターを取得します。
    返却値: total, success, error, duplicate
    """
```

## ランタイム情報

### get_task_repr

```python
def get_task_repr(self, task) -> str:
    """
    タスク引数の人間が読める文字列表現を取得します。
    ログ出力に使用され、長すぎる引数は自動的に切り詰められます。
    """
```

### _get_result_repr

```python
def _get_result_repr(self, result) -> str:
    """
    結果の人間が読める文字列表現を取得します。
    """
```

## 注意事項

### キャッシュと重複チェック

キャッシュが有効で重複チェックが無効の場合、警告がトリガーされます：

```python
# 警告: キャッシュされた結果数と入力タスク数の不一致が生じる可能性があります
executor = TaskExecutor(
    "Processor",
    process,
    enable_success_cache=True,
    enable_duplicate_check=False  # 非推奨
)
```

### 実行モードの選択

| モード | 適用シーン | 注意事項 |
|--------|-----------|---------|
| `serial` | デバッグ、シンプルなタスク | 並行なし |
| `thread` | I/O 集約型 | GIL の制限に注意 |
| `process` | CPU 集約型 | pickle 可能な関数が必要 |
| `async` | ネットワーク I/O | start_async の使用が必要 |
