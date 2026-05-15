# TaskDispatch

> 📅 最終更新日: 2026/05/08

`TaskDispatch` はタスク実行のコアランナーで、キューからタスクを取得し、タスクを実行し、結果とエラーを処理する役割を担います。シリアル、スレッドプール、非同期の3つの実行モードをサポートしています。

## 初期化

```python
class TaskDispatch:
    def __init__(self, task_executor: TaskExecutor, func, max_workers: int):
        """
        タスクランナーを初期化します。

        :param task_executor: タスクエグゼキューター（TaskExecutor インスタンス）
        :param func: タスク関数
        :param max_workers: ワーカースレッドまたはプロセスの数量制限
        """
```

## 実行モード

### dispatch_serial

タスクをシリアルに実行し、1つずつ処理します。

```python
def dispatch_serial(self):
    """
    タスクをシリアルに実行します。

    task_queues からタスクを取得し、終了シグナルを受信してすべてのタスクが完了するまで順次実行します。
    """
```

実行フロー：
1. `task_queues.get()` からタスクを取得
2. 終了シグナル（`TerminationIdPool`）かどうかを確認
3. タスクが重複かどうかを確認
4. タスクを実行し、結果またはエラーを処理
5. プログレスバーを更新
6. 終了シグナルを受信後、すべてのタスクが完了したか確認

### dispatch_thread

スレッドプールを使用してタスクを並列実行します。

```python
def dispatch_thread(self):
    """
    スレッドプールを使用してタスクを並列実行します。
    """
```

実行フロー：
1. スレッドプールを初期化
2. キューからタスクを取得してプールに送信
3. 完了した future を定期的にクリーンアップ（リスト長が `max_workers * 2` に達した時にフィルタリング）
4. すべての future の完了を待ってから終了シグナルを処理
5. プールをシャットダウンしリソースを解放

### dispatch_async

コルーチンとセマフォを使用して並行制御しながらタスクを非同期実行します。

```python
async def dispatch_async(self):
    """
    並行数を制限しながらタスクを非同期実行します。
    """
```

実行フロー：
1. 並行数を制限するセマフォを作成
2. タスクを非同期取得
3. `asyncio.gather` で並行実行
4. 結果とエラーを処理
5. 終了条件を確認

## 内部メソッド

### _worker / _async_worker

```python
def _worker(self, envelope: TaskEnvelope):
    """スレッドプール内のワーカー関数、単一タスクを実行しリトライを処理します。"""

async def _async_worker(self, envelope: TaskEnvelope):
    """非同期ワーカー関数、単一タスクを実行しリトライを処理します。"""
```

### _process_termination_signal

```python
def _process_termination_signal(self, termination_pool: TerminationIdPool) -> TerminationSignal:
    """
    終了シグナルを処理し、マージイベントを生成します。

    :param termination_pool: 複数の終了シグナル ID を含むプール
    :return: マージされた終了シグナル
    """
```

### _release_pool

```python
def _release_pool(self):
    """スレッドプールをシャットダウンし、リソースを解放します。"""
```

## TaskExecutor との関係

`TaskDispatch` は `TaskExecutor` の内部コンポーネントです：

```
TaskExecutor
    ├── func               # タスク関数
    ├── task_queues        # 入力キュー（TaskInQueue）
    ├── result_queues      # 出力キュー（TaskOutQueue）
    ├── metrics            # タスクメトリクス
    └── dispatch           # TaskDispatch インスタンス
            ├── func               # タスク関数
            ├── max_workers        # 並行数制限
            ├── dispatch_serial()
            ├── dispatch_thread()
            └── dispatch_async()
```

`TaskExecutor` は `execution_mode` に基づいて `TaskDispatch` のどのメソッドを呼び出すかを選択します：
- `serial` → `dispatch_serial()`
- `thread` → `dispatch_thread()`
- `async` → `dispatch_async()`

## 注意事項

1. **並行制御**: `max_workers` は並行タスク数を制限し、リソース枯渇を防止
2. **futures クリーンアップ**: `dispatch_thread` では futures リスト長が `max_workers * 2` に達した時に完了した future をフィルタリングし、メモリの無限増加を回避
3. **終了処理**: 終了シグナルの適切なマージと伝播
4. **エラー伝播**: 例外はキャッチされ `TaskExecutor.handle_task_fail()` に渡される
5. **リトライメカニズム**: ワーカー内部でタスクリトライをサポート、`max_retries` で制御
6. **非同期制限**: `dispatch_async` はタスク関数がコルーチン関数である必要がある
