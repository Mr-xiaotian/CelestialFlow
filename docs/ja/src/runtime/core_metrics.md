# TaskMetrics

> 📅 最終更新日: 2026/05/24

TaskMetrics モジュールは、タスク実行中の各種メトリクス（入力タスク数、成功数、失敗数、重複タスク数など）の管理と統計を担当します。通常、`TaskExecutor` のコンポーネントとして存在します。

## 初期化

```python
class TaskMetrics:
    def __init__(
        self,
        execution_mode: str,
        enable_duplicate_check: bool = False,
    ):
        """
        :param execution_mode: タスク実行モード。"serial"、"thread"、"async" を指定可能
        :param enable_duplicate_check: 重複タスクチェックを有効にするかどうか。デフォルトは False
        """
```

- **execution_mode**: カウンターのスレッドセーフ実装を決定します（thread モードでは `Lock` を使用）
- **enable_duplicate_check**: 重複排除用の `processed_set` を維持するかどうかを制御

## カウンター管理

TaskMetrics は内部で4つのコアカウンターを維持します：

| カウンター | 型 | 用途 |
|--------|------|------|
| `task_counter` | `SumCounter` | 総入力タスク数（カスケード対応） |
| `success_counter` | `ValueWrapper` | 成功タスク数 |
| `error_counter` | `ValueWrapper` | 失敗タスク数 |
| `duplicate_counter` | `ValueWrapper` | 重複タスク数 |

`thread` モードでは、3つの `ValueWrapper` が同一の `Lock` を共有し、ロックオーバーヘッドを削減します。

### 初期化とリセット

```python
def reset_counter(self) -> None:
    """すべてのカウンターをゼロにリセットする。"""

def reset_state(self) -> None:
    """統計状態をリセットする（processed_set をクリア）。"""
```

### カウンター操作

```python
def add_task_count(self, add_count: int = 1):
    """スレッドセーフに入力タスクカウントを増加させる。"""

def add_success_count(self, count: int = 1):
    """スレッドセーフに成功タスクカウントを増加させる。"""

def add_error_count(self, count: int = 1):
    """スレッドセーフに失敗タスクカウントを増加させる。"""

def add_duplicate_count(self, count: int = 1):
    """スレッドセーフに重複タスクカウントを増加させる。"""
```

### カウンターカスケード

```python
def append_task_counter(self, counter: ValueWrapper) -> None:
    """外部カウンターを task_counter に追加する（Stage 間のカスケード統計に使用）。"""
```

カスケードは `TaskStage.prev_bindings()` で使用され、各下流ノードが上流の成功カウンターを自分の `task_counter` に登録することで、「上流の出力 = 下流の入力」というカウントの一貫性を実現します。

## 状態クエリ

### is_tasks_finished

すべての入力タスクが処理完了したかどうかを判定します。

```python
def is_tasks_finished(self) -> bool:
    """
    task_counter.value と processed（success + error + duplicate）が等しいかを比較する。
    """
```

### get_counts

現在のすべてのメトリクスのスナップショット辞書を取得します。

```python
def get_counts(self) -> dict[str, int]:
    return {
        "tasks_input": int,       # 入力タスク総数
        "tasks_succeeded": int,   # 成功タスク数
        "tasks_failed": int,      # 失敗タスク数
        "tasks_duplicated": int,  # 重複タスク数
        "tasks_processed": int,   # 処理済み総数
        "tasks_pending": int,     # 未処理タスク数
    }
```

### 単項クエリ

```python
def get_task_count(self) -> int: ...
def get_success_count(self) -> int: ...
def get_error_count(self) -> int: ...
def get_duplicate_count(self) -> int: ...
```

## タスク重複排除

`enable_duplicate_check=True` の場合、`processed_set: set[bytes]` を維持して処理済みタスクのハッシュ値を記録します。

```python
def is_duplicate(self, task_hash: bytes) -> bool:
    """
    アトミック操作：重複をチェックしてマークする。
    - ハッシュがセットに存在しない場合、セットに追加して False を返す
    - 既に存在する場合、True を返す
    """

def add_processed_set(self, task_hash: bytes) -> None:
    """タスクハッシュを処理済みセットに追加する（enable_duplicate_check=True の場合のみ有効）。"""
```

## リトライ管理

```python
def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """リトライが必要な例外タイプを追加する。"""
```

例外タイプは `tuple` 形式で `self.retry_exceptions` に保存され、`TaskDispatch._worker` が `isinstance(exception, self.retry_exceptions)` でリトライ判定を行います。

## 使用例

以下の例は `TaskMetrics` の完全な使用法を示します。初期化、カウンター操作、重複チェック、リトライ例外設定、状態クエリを含みます。

```python
from celestialflow.runtime import TaskMetrics

# 1. メトリクスマネージャーを初期化（重複チェックを有効化）
metrics = TaskMetrics(
    execution_mode="serial",
    enable_duplicate_check=True,
)

# 2. リトライ可能な例外タイプを追加
metrics.add_retry_exceptions(ConnectionError, TimeoutError)

# 3. タスク処理プロセスをシミュレート
# 5つの入力タスクを受信
metrics.add_task_count(5)

# 3つ成功
metrics.add_success_count(3)

# 1つ失敗
metrics.add_error_count(1)

# 1つ重複を検出
metrics.add_duplicate_count(1)

# 4. 各カウンターの値をクエリ
print(f"タスク総数: {metrics.get_task_count()}")         # 5
print(f"成功数: {metrics.get_success_count()}")          # 3
print(f"失敗数: {metrics.get_error_count()}")            # 1
print(f"重複数: {metrics.get_duplicate_count()}")        # 1

# 5. 完全なスナップショット辞書を取得
counts = metrics.get_counts()
print(f"処理済み: {counts['tasks_processed']}")          # 3+1+1 = 5
print(f"未処理: {counts['tasks_pending']}")              # 0
print(f"すべて完了: {metrics.is_tasks_finished()}")     # True

# 6. 重複チェックの例（enable_duplicate_check=True が必要）
task_hash = b"\x00\x01\x02"
print(f"初回チェック: {metrics.is_duplicate(task_hash)}")   # False（初回追加）
print(f"重複チェック: {metrics.is_duplicate(task_hash)}")   # True（既に存在）

# 7. カウンターをリセット
metrics.reset_counter()
print(f"リセット後のタスク数: {metrics.get_task_count()}")  # 0

# 8. 実行モードを切り替え（スレッドセーフ戦略を再初期化）
metrics.set_execution_mode("thread")
print(f"新しいモード: {metrics.execution_mode}")
```

### カウンターカスケード

```python
from celestialflow.runtime import TaskMetrics
from celestialflow.runtime.util_types import ValueWrapper

# 親メトリクスと子メトリクスを作成
parent_metrics = TaskMetrics(execution_mode="serial")
child_counter = ValueWrapper(value=10)

# 子カウンターを親の task_counter にカスケード
parent_metrics.append_task_counter(child_counter)
parent_metrics.add_task_count(5)  # 自身で5を追加

print(f"総タスク数 (5 + 10) : {parent_metrics.get_task_count()}")  # 15
```

### set_execution_mode

```python
def set_execution_mode(self, execution_mode: str) -> None:
    """タスク実行モードを設定し、カウンターを再初期化する（スレッドセーフ戦略を切り替え）。"""
```
