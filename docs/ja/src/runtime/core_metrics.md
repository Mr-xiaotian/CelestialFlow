# TaskMetrics

> 📅 最終更新日: 2026/06/22

TaskMetrics モジュールは、タスク実行プロセスにおける各種メトリクス（入力タスク数、成功数、失敗数、重複タスク数など）の管理と統計を担当します。通常は `TaskExecutor` のコンポーネントとして存在します。


## 初期化

```python
class TaskMetrics:
    def __init__(
        self,
        enable_duplicate_check: bool = False,
    ):
        """
        :param enable_duplicate_check: 重複タスクチェックを有効にするかどうか。デフォルト False
        """
```

- **enable_duplicate_check**: 重複排除用の `processed_set` を維持するかどうかを制御します

## カウンター管理

TaskMetrics は内部に 4 つのコアカウンターを保持します:

| カウンター | 型 | 用途 |
|--------|------|------|
| `task_counter` | `SumCounter` | 総入力タスク数（カスケード対応） |
| `success_counter` | `ValueWrapper` | 成功タスク数 |
| `error_counter` | `ValueWrapper` | 失敗タスク数 |
| `duplicate_counter` | `ValueWrapper` | 重複タスク数 |

すべての `ValueWrapper` は統一して `Lock` でスレッドセーフを保証します。

### 初期化とリセット

```python
def reset_counter(self) -> None:
    """全カウンターをゼロにリセットします。"""

def reset_state(self) -> None:
    """統計状態をリセットします（processed_set をクリア）。"""
```

### カウンター操作

```python
def add_task_count(self, add_count: int = 1):
    """スレッドセーフに入力タスクカウントを増やします。"""

def add_success_count(self, count: int = 1):
    """スレッドセーフに成功タスクカウントを増やします。"""

def add_error_count(self, count: int = 1):
    """スレッドセーフに失敗タスクカウントを増やします。"""

def add_duplicate_count(self, count: int = 1):
    """スレッドセーフに重複タスクカウントを増やします。"""
```

### カウンターカスケード

```python
def append_task_counter(self, counter: ValueWrapper) -> None:
    """外部カウンターを task_counter に追加します（Stage 間カスケード統計用）。"""
```

カスケードは `TaskStage.prev_bindings()` で使用されます — 各下流ノードは上流の成功カウンターを自身の `task_counter` に登録し、「上流の出力 = 下流の入力」というカウントの一貫性を実現します。

## 状態照会

### is_tasks_finished

全入力タスクが処理済みかどうかを判定します。

```python
def is_tasks_finished(self) -> bool:
    """
    task_counter.value と processed（success + error + duplicate）が等しいかを比較します。
    """
```

### get_counts

現在の全メトリクスのスナップショット辞書を取得します。

```python
def get_counts(self) -> dict[str, int]:
    return {
        "tasks_input": int,       # 入力タスク総数
        "tasks_succeeded": int,   # 成功タスク数
        "tasks_failed": int,      # 失敗タスク数
        "tasks_duplicated": int,  # 重複タスク数
        "tasks_processed": int,   # 処理済み総数
        "tasks_pending": int,     # 保留中タスク数
    }
```

### 単項照会

```python
def get_task_count(self) -> int: ...
def get_success_count(self) -> int: ...
def get_error_count(self) -> int: ...
def get_duplicate_count(self) -> int: ...
```

## タスク重複排除

`enable_duplicate_check=True` の場合、処理済みタスクのハッシュ値を記録する `processed_set: set[bytes]` を維持します。

```python
def is_duplicate(self, task_hash: bytes) -> bool:
    """
    アトミック操作: 重複をチェックしてマークします。
    - ハッシュがセットに存在しない場合、セットに追加して False を返す
    - 既存の場合、True を返す
    """

def add_processed_set(self, task_hash: bytes) -> None:
    """タスクハッシュを処理済みセットに追加します（enable_duplicate_check=True 時のみ有効）。"""
```

## リトライ管理

```python
def set_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """リトライが必要な例外型を追加します。"""
```

例外型は `tuple` 形式で `self.retry_exceptions` に格納され、`TaskDispatch._worker` は `isinstance(exception, self.retry_exceptions)` でリトライ要否を判定します。呼び出しごとに既存の例外型に累積追加されます。

## 使用例

以下の例は `TaskMetrics` の完全な使用方法を示し、初期化、カウンター操作、重複排除チェック、リトライ例外設定、状態照会を網羅します。

```python
from celestialflow.runtime import TaskMetrics

# 1. メトリクスマネージャの初期化（重複排除チェックを有効化）
metrics = TaskMetrics(
    enable_duplicate_check=True,
)

# 2. リトライ可能例外型の追加
metrics.set_retry_exceptions(ConnectionError, TimeoutError)

# 3. タスク処理プロセスのシミュレーション
# 5 つの入力タスクを受信
metrics.add_task_count(5)

# 3 つ成功
metrics.add_success_count(3)

# 1 つ失敗
metrics.add_error_count(1)

# 1 つ重複検出
metrics.add_duplicate_count(1)

# 4. 各カウンター値の照会
print(f"タスク総数: {metrics.get_task_count()}")         # 5
print(f"成功数: {metrics.get_success_count()}")        # 3
print(f"失敗数: {metrics.get_error_count()}")          # 1
print(f"重複数: {metrics.get_duplicate_count()}")      # 1

# 5. 完全なスナップショット辞書の取得
counts = metrics.get_counts()
print(f"処理済み: {counts['tasks_processed']}")          # 3+1+1 = 5
print(f"保留中: {counts['tasks_pending']}")            # 0
print(f"全完了: {metrics.is_tasks_finished()}")      # True

# 6. 重複排除チェック例（enable_duplicate_check=True が必要）
task_hash = b"\x00\x01\x02"
print(f"初回チェック: {metrics.is_duplicate(task_hash)}")   # False（初回追加）
print(f"重複チェック: {metrics.is_duplicate(task_hash)}")   # True（既存）

# 7. カウンターのリセット
metrics.reset_counter()
print(f"リセット後タスク数: {metrics.get_task_count()}")      # 0
```

### カウンターカスケード

```python
from celestialflow.runtime import TaskMetrics
from celestialflow.runtime.util_types import ValueWrapper

# 親メトリクスと子メトリクスを作成
parent_metrics = TaskMetrics()
child_counter = ValueWrapper(value=10)

# 子カウンターを親の task_counter にカスケード
parent_metrics.append_task_counter(child_counter)
parent_metrics.add_task_count(5)  # 自身に 5 追加

print(f"総タスク数 (5 + 10) : {parent_metrics.get_task_count()}")  # 15
```
