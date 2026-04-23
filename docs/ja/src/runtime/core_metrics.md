# TaskMetrics

> 📅 最終更新日: 2026/04/22

TaskMetrics モジュールは、タスク実行中のさまざまなメトリクス（入力タスク数、成功数、失敗数、重複タスク数など）を管理・統計します。通常、`TaskExecutor` のコンポーネントとして存在します。

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

- **execution_mode**: タスク実行モード。`"thread"` や `"async"` などが指定可能です。カウンターの実装方式の選択に使用されます。
- **max_retries**: 最大リトライ回数。デフォルト値は 1 です。
- **enable_duplicate_check**: 重複タスクチェックを有効にするかどうか。デフォルト値は False です。

## カウンター管理

TaskMetrics は、カウンターを安全に更新するための一連のメソッドを提供します（通常、マルチスレッド/マルチプロセス環境ではロックを使用します）。

### 初期化とリセット

```python
def init_counter(self) -> None:
    """カウンターを初期化します（execution_mode に基づいて実装を選択します）。"""

def reset_counter(self) -> None:
    """すべてのカウンターをゼロにリセットします。"""

def reset_state(self) -> None:
    """統計状態をリセットします（リトライ時間記録と処理済みタスクセットをクリアします）。"""
```

### カウンター操作

```python
def add_task_count(self, add_count: int = 1):
    """入力タスクカウントを増加させます。"""

def add_success_count(self, count: int = 1):
    """スレッドセーフに成功タスクカウントを増加させます。"""

async def add_success_count_async(self, count: int = 1):
    """非同期で成功タスクカウンターを更新します。"""

def add_error_count(self, count: int = 1):
    """スレッドセーフに失敗タスクカウントを増加させます。"""

def add_duplicate_count(self, count: int = 1):
    """スレッドセーフに重複タスクカウントを増加させます。"""
```

### カウンターカスケード

```python
def append_task_counter(self, counter) -> None:
    """外部カウンターをタスク合計カウンターに追加します（Stage 間のカスケード統計に使用されます）。"""
```

## 状態クエリ

### is_tasks_finished

すべての入力タスクが処理済みかどうかを判定します（成功 + 失敗 + 重複 == 入力）。

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
        "tasks_processed": int,   # 処理済み合計（成功+失敗+重複）
        "tasks_pending": int,     # 未処理タスク数（入力-処理済み）
    }
```

### 個別クエリ

```python
def get_task_count(self) -> int:
    """現在のタスク総数を取得します。"""

def get_success_count(self) -> int:
    """現在の成功タスク数を取得します。"""

def get_error_count(self) -> int:
    """現在の失敗タスク数を取得します。"""

def get_duplicate_count(self) -> int:
    """現在の重複タスク数を取得します。"""
```

## タスク重複排除

`enable_duplicate_check` が有効な場合、TaskMetrics は処理済みタスクのハッシュ値を記録する `processed_set` セットを維持します。

```python
def is_duplicate(self, task_hash: str) -> bool:
    """タスクが既に存在するかチェックします。"""

def add_processed_set(self, task_hash: str) -> None:
    """タスクハッシュを処理済みセットに追加します。"""

def discard_processed_set(self, task_hash: str) -> None:
    """処理済みセットからタスクを削除します（リトライ時に再処理を許可するために使用されます）。"""
```

## リトライ管理

TaskMetrics は、リトライ可能な例外タイプとリトライ回数の追跡を含む、タスクのリトライロジックを管理します。

### 例外設定

```python
def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """リトライをトリガーする例外タイプを追加します。"""
```

### リトライ判定

```python
def is_retry_able(self, task_hash: str, exception: Exception) -> bool:
    """
    タスクがリトライ可能かチェックします。
    例外タイプと現在のリトライ回数に基づいて判定します。
    """
```

### リトライカウント

```python
def get_retry_time(self, task_hash: str) -> int:
    """タスクのリトライ回数を取得します（存在しない場合は 0 を返します）。"""

def add_retry_time(self, task_hash: str, retry_time: int = 1) -> int:
    """タスクのリトライ回数を増加させ、新しい回数を返します。"""

def pop_retry_time(self, task_hash: str) -> int | None:
    """タスクのリトライ回数をポップして返します（成功または最終失敗後に呼び出されます）。"""
```

## 実行モード設定

```python
def set_execution_mode(self, execution_mode: str) -> None:
    """タスク実行モードを設定し、カウンターを再初期化します。"""
```
