# TaskDispatch

> 📅 最終更新日: 2026/04/22

`TaskDispatch` はタスク実行のコアランナーであり、キューからタスクを取得し、実行し、結果とエラーを処理する役割を担います。シリアル、スレッドプール、非同期の3つの実行モードをサポートしています。

## 初期化

```python
class TaskDispatch:
    def __init__(self, task_executor: TaskExecutor, func, max_workers: int):
        """
        タスクランナーを初期化します。

        :param task_executor: タスクエグゼキューター（TaskExecutor インスタンス）
        :param func: タスク関数
        :param max_workers: ワーカースレッドまたはプロセスの最大数
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

実行フロー:
1. `task_queues.get()` からタスクを取得します
2. 終了シグナル（`TerminationIdPool`）かどうかを確認します
3. タスクが重複していないか確認します
4. タスクを実行し、結果またはエラーを処理します
5. プログレスバーを更新します
6. 終了シグナルを受信した後、すべてのタスクが完了したか確認します

### dispatch_thread

スレッドプールを使用してタスクを並列実行します。

```python
def dispatch_thread(self):
    """
    スレッドプールを使用してタスクを並列実行します。
    """
```

実行フロー:
1. スレッドプールを初期化します
2. キューからタスクを取得し、プールに送信します
3. すべての future が完了するのを待ってから終了シグナルを処理します
4. プールをシャットダウンし、リソースを解放します

### dispatch_async

コルーチンとセマフォを使用して並行性を制御しながら、タスクを非同期に実行します。

```python
async def dispatch_async(self):
    """
    並行数を制限してタスクを非同期に実行します。
    """
```

実行フロー:
1. 並行数を制限するセマフォを作成します
2. タスクを非同期に取得します
3. `asyncio.gather` を使用してタスクを並行実行します
4. 結果とエラーを処理します
5. 終了条件を確認します

## 内部メソッド

### _worker / _async_worker

```python
def _worker(self, envelope: TaskEnvelope):
    """スレッドプール内のワーカー関数。単一タスクを実行し、リトライを処理します。"""

async def _async_worker(self, envelope: TaskEnvelope):
    """非同期ワーカー関数。単一タスクを実行し、リトライを処理します。"""
```

### process_termination_signal

```python
def process_termination_signal(self, termination_pool: TerminationIdPool) -> TerminationSignal:
    """
    終了シグナルを処理し、マージイベントを生成します。

    :param termination_pool: 複数の終了シグナル ID を含むプール
    :return: マージされた終了シグナル
    """
```

### release_pool

```python
def release_pool(self):
    """スレッドプールをシャットダウンし、リソースを解放します。"""
```

## TaskExecutor との関係

`TaskDispatch` は `TaskExecutor` の内部コンポーネントです:

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

`TaskExecutor` は `execution_mode` に基づいて `TaskDispatch` のどのメソッドを呼び出すかを選択します:
- `serial` → `dispatch_serial()`
- `thread` → `dispatch_thread()`
- `async` → `dispatch_async()`

## 注意事項

1. **並行性制御**: `max_workers` は並行タスク数を制限し、リソースの枯渇を防ぎます
2. **終了処理**: 終了シグナルのマージと転送を正しく処理します
3. **エラー伝搬**: 例外はキャッチされ、`TaskExecutor.handle_task_fail()` に渡されます
4. **リトライメカニズム**: ワーカー内部でタスクのリトライをサポートし、`max_retries` で制御されます
5. **非同期の制限**: `dispatch_async` はタスク関数がコルーチン関数であることを要求します
