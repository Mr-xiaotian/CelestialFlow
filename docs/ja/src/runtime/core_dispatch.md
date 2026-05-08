# TaskDispatch

> 📅 最終更新日: 2026/05/08

`TaskDispatch` はタスク実行のコアランナーであり、キューからタスクを取得し、タスクを実行し、結果とエラーを処理する役割を担います。シリアル、スレッドプール、非同期の3つの実行モードをサポートしています。

## 初期化

```python
class TaskDispatch:
    def __init__(self, task_executor: TaskExecutor, func, max_workers: int):
        """
        タスクランナーを初期化する。

        :param task_executor: タスクエグゼキューター（TaskExecutor インスタンス）
        :param func: タスク関数
        :param max_workers: ワーカースレッドまたはプロセス数の上限
        """
```

## 実行モード

### dispatch_serial

タスクをシリアルに実行し、1つずつ処理します。

```python
def dispatch_serial(self):
    """
    タスクをシリアルに実行する。

    task_queues からタスクを取得し、順番に実行し、終了シグナルを受信してすべてのタスクが完了するまで続ける。
    """
```

実行フロー：
1. `task_queues.get()` からタスクを取得
2. 終了シグナル（`TerminationIdPool`）かどうかを確認
3. タスクが重複していないか確認
4. タスクを実行し、結果またはエラーを処理
5. プログレスバーを更新
6. 終了シグナルを受信後、すべてのタスクが完了しているか確認

### dispatch_thread

スレッドプールを使用してタスクを並列実行します。

```python
def dispatch_thread(self):
    """
    スレッドプールを使用してタスクを並列実行する。
    """
```

実行フロー：
1. スレッドプールを初期化
2. キューからタスクを取得してプールに送信
3. 完了した futures を定期的にクリーンアップし、メモリの蓄積を防止
4. すべての future が完了してから終了シグナルを処理
5. プールを閉じてリソースを解放

### dispatch_async

非同期でタスクを実行し、コルーチンとセマフォで並行数を制御します。

```python
async def dispatch_async(self):
    """
    非同期でタスクを実行し、並行数を制限する。
    """
```

実行フロー：
1. セマフォを作成して並行数を制限
2. 非同期でタスクを取得
3. `asyncio.gather` で並行にタスクを実行
4. 結果とエラーを処理
5. 終了条件を確認

## 内部メソッド

### _worker / _async_worker

```python
def _worker(self, envelope: TaskEnvelope):
    """スレッドプール内のワーカー関数。単一タスクを実行しリトライを処理する。"""

async def _async_worker(self, envelope: TaskEnvelope):
    """非同期ワーカー関数。単一タスクを実行しリトライを処理する。"""
```

### _process_termination_signal

```python
def _process_termination_signal(self, termination_pool: TerminationIdPool) -> TerminationSignal:
    """
    終了シグナルを処理し、マージイベントを生成する。

    :param termination_pool: 複数の終了シグナル ID を含むプール
    :return: マージされた終了シグナル
    """
```

### _release_pool

```python
def _release_pool(self):
    """スレッドプールを閉じ、リソースを解放する。"""
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
            ├── max_workers        # 並行数の上限
            ├── dispatch_serial()
            ├── dispatch_thread()
            └── dispatch_async()
```

`TaskExecutor` は `execution_mode` に基づいて `TaskDispatch` のどのメソッドを呼び出すかを選択します：
- `serial` → `dispatch_serial()`
- `thread` → `dispatch_thread()`
- `async` → `dispatch_async()`

## 注意事項

1. **並行制御**: `max_workers` で並行タスク数を制限し、リソースの枯渇を防止
2. **終了処理**: 終了シグナルのマージと伝達を正しく処理
3. **エラー伝播**: 例外はキャッチされ、`TaskExecutor.handle_task_fail()` に渡される
4. **リトライ機構**: ワーカー内部でタスクのリトライをサポートし、`max_retries` で制御
5. **非同期の制限**: `dispatch_async` ではタスク関数がコルーチン関数である必要がある
6. **futures クリーンアップ**: `dispatch_thread` では完了した futures を定期的にクリーンアップし、不要な future の蓄積によるメモリオーバーヘッドを防止
