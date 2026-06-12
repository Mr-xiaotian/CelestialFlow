# TaskExecutor

> 📅 最終更新日: 2026/06/11

`TaskExecutor` は単一タスクロジックを実行するコアコンポーネントです。タスクの実行、並行性制御、エラー処理、リトライ機構、およびログ記録を担当します。

> 注意：`TaskExecutor` は使い捨てオブジェクトです。`start()` または `start_async()` の完了後、現在のインスタンスを安全に再利用できるとは限りません。再実行が必要な場合は、新しい `TaskExecutor` を作成してください。

## 初期化

```python
class TaskExecutor[T, R]:
    def __init__(
        self,
        name: str,
        func: Callable[[T], R] | Callable[[T], Awaitable[R]],
        execution_mode: str = "serial",
        max_workers: int | None = None,
        max_retries: int = 1,
        max_info: int = 50,
        enable_duplicate_check: bool = True,
        log_level: str = "INFO",
    ):
        ...
```

### パラメータ説明

| パラメータ | デフォルト値 | 説明 |
|------|--------|------|
| `name` | — | 実行者名。ログと追跡に使用 |
| `func` | — | タスクを実際に実行する呼び出し可能オブジェクト（同期関数とコルーチン関数の両方をサポート） |
| `execution_mode` | `"serial"` | 実行モード：`"serial"` / `"thread"` / `"async"` |
| `max_workers` | `None` | 並行数制限（None の場合は動的: `min(32, cpu_count+4)`） |
| `max_retries` | `1` | タスク失敗後の最大リトライ回数（最大で retries+1 回実行） |
| `max_info` | `50` | ログにおける各情報の最大長 |
| `enable_duplicate_check` | `True` | タスクハッシュに基づく重複チェックを有効にするか |
| `log_level` | `"INFO"` | ログレベル |

> **変更点**：以前のドキュメントには `unpack_task_args` パラメータが記載されていましたが、現在のソースコードには存在せず、削除されました。

## Observer パターン

`TaskExecutor` は observer パターンを通じてライフサイクルイベントを外部にブロードキャストします。

### 登録と解除

```python
executor.add_observer(observer)     # オブザーバーを登録
executor.remove_observer(observer)  # オブザーバーを解除
```

### ブロードキャストイベント

| イベント | トリガー位置 | 説明 |
|------|---------|------|
| `on_start(name, total)` | `_prepare_start()` | 実行開始（注意：total は常に 0。実際のタスク数は `on_tasks_added` で通知） |
| `on_task_success()` | `process_task_success()` | タスク成功（パラメータなし。Observer が自身でカウントを取得） |
| `on_task_fail()` | `handle_task_fail()` | タスク失敗（パラメータなし） |
| `on_task_duplicate()` | `deal_duplicate()` | 重複検出（パラメータなし） |
| `on_tasks_added(count)` | `_put_task_queue()` | 新規タスク追加（100 件ごとに通知） |
| `on_finish()` | `_finish_start()` finally | 実行終了（パラメータなし） |

> **変更点**：以前のドキュメントでは `on_start` が実際のタスク総数を渡すと記載されていましたが、ソースコードでは常に `0` を渡します。実際のタスク数は後続の `on_tasks_added` イベントで逐次通知されます。成功/失敗/重複イベントもカウントパラメータを渡しません。

## コアメソッド

### start / start_async

```python
def start(self, task_source: Iterable[T]) -> None:
    """
    実行者を同期的に起動。フロー：
    1. _prepare_start() — init_env() + タスク注入 + 起動ログ記録
    2. execution_mode に応じて dispatch の対応メソッドを呼び出し
    3. _finish_start() — on_finish 通知 + 全 spout 停止
    """

async def start_async(self, task_source: Iterable[T]) -> None:
    """
    実行者を非同期的に起動。内部で execution_mode="async" を設定。
    asyncio.run() の代わりに await dispatch.dispatch_async() を使用。
    """
```

ライフサイクル制約：

- 実行中はキュー、`spout/inlet`、統計状態、スケジューラー実行時リソースを作成・保持します。
- 現在の実装は単回実行向けに設計されており、一度の実行終了後に完全にリセットできることは保証されません。
- 同じロジックを複数回実行する必要がある場合は、同じオブジェクトの `start()` / `start_async()` を繰り返し呼ぶのではなく、新しい実行者インスタンスを作成してください。

## エラー処理

### リトライロジック

例外は `TaskDispatch._worker` で分類されます：
- **リトライ可能な例外**: `retry_exceptions` に含まれ、かつ `max_retries` に達していない場合、`emit_retry_envelope()` でタスク ID を更新してリトライ
- **リトライ不可能な例外**: タスクを失敗としてマークし、エラーログを記録、`fail_inlet` に投入

```python
def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """リトライが必要な例外型を追加する。"""
```

### 結果処理（コアメソッド）

タスクの結果処理は以下のメソッドで実装されます：

```python
def process_task_success(self, task_envelope: TaskEnvelope[T, R], result: R, start_time: float) -> None:
    """成功タスクの処理：observer 通知、ログ書き込み、結果エンベロープ生成、result_queue への投入。"""

def handle_task_fail(self, task_envelope: TaskEnvelope[T, R], exception: Exception) -> None:
    """失敗タスクの処理：observer 通知、fail_inlet と log_inlet への記録。"""

def deal_duplicate(self, task_envelope: TaskEnvelope[T, R]) -> None:
    """重複タスクの処理：observer 通知、ログ記録。"""
```

> **変更点**：以前のドキュメントではオーバーライド可能なメソッド `process_result()` と `get_args()` が記載されていましたが、現在のソースコードにはこれらのメソッドは存在しません。実際の結果処理は `process_task_success()` で行われ、パラメータ抽出ロジックは `TaskDispatch` 内部で処理されます。

### 結果の取得

```python
def get_success_pairs(self) -> list[tuple[T, R]]:
    """成功タスク (task, result) リストを取得（SuccessSpout キャッシュ経由）。"""

def get_error_pairs(self) -> list[tuple[Any, PersistedErrorRecord]]:
    """失敗タスク (task, error_record) リストを取得（FailSpout キャッシュ経由）。"""

def process_result_dict(self) -> dict[T, R | str]:
    """成功と失敗の結果辞書をマージ。"""

def handle_error_dict(self) -> dict[tuple[str, str], list[T]]:
    """(error_type, error_message) でエラーをグループ化。"""
```

## CelestialTree 統合

```python
def set_ctree(self, host: str = "127.0.0.1", http_port: int = 7777, grpc_port: int = 7778) -> None:
    """CelestialTree クライアントを設定（gRPC 転送のみ）。"""

def set_nullctree(self, event_id: int | None = None) -> None:
    """空クライアントを設定（外部サービスに接続せず、イベント ID のみ生成）。"""
```

## 状態照会メソッド

```python
def get_name(self) -> str:                    # 実行者名
def get_full_name(self) -> str:               # "name(mode-workers)" または "name(serial)"
def get_func_name(self) -> str:               # 関数名
def _get_class_name(self) -> str:             # クラス名
def _get_execution_mode_desc(self) -> str:    # 実行モード説明文字列
def get_summary(self) -> dict:                # スナップショット：name, func_name, execution_mode, max_workers
def get_counts(self) -> dict:                 # カウンター：tasks_input/succeeded/failed/duplicated/processed/pending
```

> **変更点**：`get_summary()` が返す辞書のキーは `name, func_name, execution_mode, max_workers` であり、`class_name` は含まれません。

## ライフサイクル

```mermaid
flowchart TD
    INIT[__init__] -->|set_name, _set_func| CONFIG[set_execution_mode<br/>set max_workers/retries/info]
    CONFIG -->|_init_dispatch| DISPATCH[TaskDispatch 作成]
    CONFIG -->|_init_queue| QUEUE[task_queue + result_queue]
    CONFIG -->|_init_metrics| METRICS[TaskMetrics 初期化]
    CONFIG -->|set_nullctree| CTREE[NullCelestialTreeClient]

    INIT -->|start/start_async| PREPARE[_prepare_start]
    PREPARE --> ENV[init_env:<br/>_init_state → _init_spout → _init_inlet]
    ENV --> PUT[_put_task_queue:<br/>task_source を走査 → put_task → put_signal]
    PUT --> NOTIFY_START[_notify: on_start]
    NOTIFY_START --> LOG_START[fail_inlet.start_executor<br/>log_inlet.start_executor]

    LOG_START --> RUN{dispatch ループ}
    RUN -->|serial| SERIAL[dispatch_serial]
    RUN -->|thread| THREAD[dispatch_thread]
    RUN -->|async| ASYNC[dispatch_async]

    SERIAL --> FINISH[_finish_start]
    THREAD --> FINISH
    ASYNC --> FINISH

    FINISH --> NOTIFY_END[_notify: on_finish]
    NOTIFY_END --> LOG_END[log_inlet.end_executor]
    LOG_END --> STOP[spout ×3 停止:<br/>log_spout + fail_spout + success_spout]
```

> **変更点**：以前のフローチャートには `_release_client` ノードが含まれていましたが、現在のソースコードにはこの操作は存在しません。`_finish_start` は実際には `_notify → log → stop spouts` の 3 ステップを実行します。

## 注意事項

| モード | 適したシナリオ | 注意事項 |
|------|----------|---------|
| `serial` | デバッグ、単純なタスク | 並行性なし、シングルスレッド |
| `thread` | I/O 密集型 | GIL 制限に注意、内部でスレッドプールを使用 |
| `async` | ネットワーク I/O | 関数はコルーチンである必要あり。`start` ではなく `start_async` を使用 |

- `process_task_success` は結果エンベロープを作成し `result_queue`（= `SuccessSpout` のキュー）に投入
- `handle_task_fail` はエラーレコードを `fail_inlet` に書き込み
- `deal_duplicate` は重複タスクを処理しログを記録
- `_init_spout` は自動的に `FailSpout`、`LogSpout`、`SuccessSpout` の 3 つのバックグラウンドスレッドを作成・起動
