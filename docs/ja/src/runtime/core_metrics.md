# TaskMetrics

> 📅 最終更新日: 2026/04/24

TaskMetrics モジュールは、タスク実行中の各種メトリクス（入力タスク数、成功数、失敗数、重複タスク数など）の管理と統計を担当します。通常、`TaskExecutor` のコンポーネントとして存在します。

## 初期化

```python
class TaskMetrics:
    def __init__(
        self,
        execution_mode: str,
        max_retries: int = 1,
        enable_duplicate_check: bool = False,
    ):
        ...
```

- **execution_mode**: タスク実行モード。`"thread"` や `"async"` などの値を指定可能。カウンターの実装方式の選択に使用されます。
- **max_retries**: 最大リトライ回数。デフォルト値は 1。
- **enable_duplicate_check**: 重複タスクチェックを有効にするかどうか。デフォルト値は False。

## カウンター管理

TaskMetrics はカウンターを安全に更新するための一連のメソッドを提供します（通常、マルチスレッド/マルチプロセス環境ではロックを使用）。

### 初期化とリセット

```python
def _init_counter(self) -> None:
    """カウンターを初期化する（execution_mode に応じて実装を選択）。"""

def reset_counter(self) -> None:
    """すべてのカウンターをゼロにリセットする。"""

def reset_state(self) -> None:
    """統計状態をリセットする（リトライ時間記録と処理済みタスク集合をクリア）。"""
```

### カウンター操作

```python
def add_task_count(self, add_count: int = 1):
    """入力タスクカウントを増加させる。"""

def add_success_count(self, count: int = 1):
    """スレッドセーフに成功タスクカウントを増加させる。"""

async def add_success_count_async(self, count: int = 1):
    """非同期で成功タスクカウンターを更新する。"""

def add_error_count(self, count: int = 1):
    """スレッドセーフに失敗タスクカウントを増加させる。"""

def add_duplicate_count(self, count: int = 1):
    """スレッドセーフに重複タスクカウントを増加させる。"""
```

### カウンターのカスケード

```python
def append_task_counter(self, counter) -> None:
    """外部カウンターをタスク総数カウンターに追加する（Stage 間のカスケード統計に使用）。"""
```

## 状態クエリ

### is_tasks_finished

すべての入力タスクが処理完了したかどうかを判定します（成功 + 失敗 + 重複 == 入力）。

```python
def is_tasks_finished(self) -> bool: ...
```

### get_counts

現在のすべてのメトリクスのスナップショット辞書を取得します。

```python
def get_counts(self) -> dict:
    return {
        "tasks_input": int,       # 入力タスク総数
        "tasks_succeeded": int,   # 成功タスク数
        "tasks_failed": int,      # 失敗タスク数
        "tasks_duplicated": int,  # 重複タスク数
        "tasks_processed": int,   # 処理済み総数 (成功+失敗+重複)
        "tasks_pending": int,     # 未処理タスク数 (入力-処理済み)
    }
```

### 単項クエリ

```python
def get_task_count(self) -> int:
    """現在のタスク総数を取得する。"""

def get_success_count(self) -> int:
    """現在の成功タスク数を取得する。"""

def get_error_count(self) -> int:
    """現在の失敗タスク数を取得する。"""

def get_duplicate_count(self) -> int:
    """現在の重複タスク数を取得する。"""
```

## タスク重複排除

`enable_duplicate_check` が有効な場合、TaskMetrics は `processed_set` 集合を維持して処理済みタスクのハッシュ値を記録します。

```python
def is_duplicate(self, task_hash: str) -> bool:
    """タスクが既に存在するか確認する。"""

def add_processed_set(self, task_hash: str) -> None:
    """タスクハッシュを処理済み集合に追加する。"""
```

## リトライ管理

TaskMetrics はタスクのリトライロジックを管理します。

### 例外設定

```python
def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """リトライが必要な例外タイプを追加する。"""
```

## 実行モード設定

```python
def set_execution_mode(self, execution_mode: str) -> None:
    """タスク実行モードを設定し、カウンターを再初期化する。"""
```
