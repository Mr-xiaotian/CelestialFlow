# src/celestialflow/runtime/core_metrics.py

> 📅 最終更新日: 2026/09/24

`TaskMetrics` モジュールは、タスク実行プロセスにおける各種メトリクスの管理と統計を担当します：外部注入タスク数、上流から受信したタスク数、成功数、失敗数、重複タスク数、および各上流/下流ノードのトラフィック。通常はタスクノード（`TaskExecutor`、`TaskSplitter`、`TaskRouter` など）のコンポーネントとして存在します。

## 初期化

```python
class TaskMetrics:
    def __init__(self) -> None:
        """初始化 TaskMetrics。"""
```

`__init__` は引数を受け取りません。以下を行います：

1. `retry_exceptions` を空のタプルに設定する。
2. オブザーバーリスト `_observers` とライフサイクル状態 `_status`（`StageStatus.NOT_STARTED`）を初期化する。
3. ビジー時間の状態 `busy_seconds = 0.0`、`_in_flight = 0`、`_busy_since = None` を設定する。
4. 統一のスレッドロック `self.lock` を作成し、`_init_counter()` を呼び出してカウンターを初期化する。

## インスタンス属性

| 属性 | 型 | 説明 |
|------|------|------|
| `lock` | `threading.Lock` | すべての内部カウンターが共有する同一のロック |
| `retry_exceptions` | `tuple[type[Exception], ...]` | リトライが必要な例外型 |
| `external_input_counter` | `ValueWrapper` | 外部注入タスクのカウント |
| `success_counter` | `ValueWrapper` | 成功タスクのカウント |
| `fail_counter` | `ValueWrapper` | 失敗タスクのカウント |
| `duplicate_counter` | `ValueWrapper` | 重複タスクのカウント |
| `upstream_counter` | `dict[str, ValueWrapper]` | 各上流ノード → 受信タスク数 |
| `downstream_counter` | `dict[str, ValueWrapper]` | 各下流ノード → 送信タスク数 |
| `busy_seconds` | `float` | 確定済みのビジー時間スライスの合計 |
| `_in_flight` | `int` | 実行中のタスク数 |
| `_busy_since` | `float \| None` | 現在のビジー時間スライスの起点 |

> `_init_counter()` では、すべての `ValueWrapper` に `lock=self.lock` を渡し、**同一のロックを共有**することで、実行モード切替時にも counter オブジェクトが安定するようにしています。

## オブザーバー管理

```python
def add_observer(self, observer: BaseObserver) -> None:
    """注册观察者。"""


def remove_observer(self, observer: BaseObserver) -> None:
    """移除观察者。"""
```

登録済みオブザーバーはカウント変化およびライフサイクルイベント時にコールバックを受信します：

| トリガーメソッド | オブザーバーのコールバック |
|---------|-----------|
| `add_external_input_count()` | `on_task_added(count)` |
| `add_success_count()` | `on_task_success(count)` |
| `add_fail_count()` | `on_task_fail(count)` |
| `add_duplicate_count()` | `on_task_duplicate(count)` |
| `on_start()` | `on_start()` |
| `on_finish()` | `on_finish()` |

> 注意：`add_downstream_count()` はオブザーバーのコールバックをトリガーしません。

## リトライ管理

```python
def set_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """添加需要重试的异常类型。"""
```

例外型は `tuple` 形式で `self.retry_exceptions` に累積的に追加されます（呼び出しごとに追加され、上書きされません）。

```python
def get_retry_error_type_names(self) -> set[str]:
    """获取当前执行器允许从持久化失败记录中恢复的错误类型名称集合。"""
```

`{exception_type.__name__ ...}` を返し、`TaskGraph.restore_db()` で `error_type` によってリトライ可能な永続化レコードをフィルタリングするために使用されます。

## カウンター設定

```python
def set_upstream_counter(self, name: str, counter: ValueWrapper) -> None:
    """添加上游任务计数器（统计从上游节点接收的任务数量）。"""


def set_downstream_counter(self, name: str, counter: ValueWrapper) -> None:
    """添加下游任务计数器（统计向下游节点发送的任务数量）。"""
```

これら 2 つのメソッドは、ノードの `connect_to()` が待機キューの接続時を待つ際に呼び出されます：同じ辺の上流と下流は同じ `ValueWrapper` を共有し、上流がタスクを送信するとインクリメントされ、下流はそれを受信したものと見なします。

## カウンター操作

```python
def add_external_input_count(self, add_count: int = 1) -> None:
    """更新外部注入任务计数器（经 put_task 进入节点的任务）。"""


def add_success_count(self, count: int = 1) -> None:
    """线程安全地增加成功任务的数量。"""


def add_fail_count(self, count: int = 1) -> None:
    """线程安全地增加失败任务的数量。"""


def add_duplicate_count(self, count: int = 1) -> None:
    """线程安全地增加重复任务的数量。"""


def add_downstream_count(self, name: str, count: int = 1) -> None:
    """线程安全地增加指定下游节点的发送任务数量。"""
```

## ライフサイクル状態

`TaskMetrics` は内部に `_status`（`StageStatus` 列挙型）を保持し、起動/終了時に更新されます：

- `on_start()`：状態を `StageStatus.RUNNING` に設定し、起動イベントをブロードキャストします。
- `on_finish()`：状態を `StageStatus.STOPPED` に設定し、終了イベントをブロードキャストします。
- `get_status()`：現在の状態を読み取り、`StageStatus` 列挙型を返します。

## 状態照会

### 入力カウント

入力タスクは来源により「外部注入」と「上流提供」の 2 種類に分けられ、その後、総入力に統合されます：

```python
def get_external_input_count(self) -> int:
    """获取外部注入的任务数量。"""


def get_upstream_input_count(self) -> int:
    """获取上游提供的任务数量（累加各上游计数器）。"""


def get_input_count(self) -> int:
    """获取任务总数（外部注入 + 上游提供）。"""
```

### 単項照会

```python
def get_success_count(self) -> int: ...
def get_fail_count(self) -> int: ...
def get_duplicate_count(self) -> int: ...
```

### get_upstream_counts / get_downstream_counts

```python
def get_upstream_counts(self) -> dict[str, int]:
    """各上游节点传输给当前节点的任务数量；无上游时返回空字典。"""


def get_downstream_counts(self) -> dict[str, int]:
    """当前节点传输给各下游节点的任务数量；无下游时返回空字典。"""
```

### is_tasks_finished

すべての入力タスクが処理済みかどうかを判定し、`get_input_count()` と `processed = success + fail + duplicate` が等しいかを比較します。

```python
def is_tasks_finished(self) -> bool:
    """所有任务处理完毕返回 True，否则返回 False。"""
```

### get_counts

現在のすべてのカウント指標のスナップショット辞書を取得します：

```python
def get_counts(self) -> dict[str, int]:
    return {
        "tasks_input": int,  # 输入任务总数（外部注入与上游提供之和）
        "tasks_succeeded": int,  # 成功任务数
        "tasks_failed": int,  # 失败任务数
        "tasks_duplicated": int,  # 重复任务数
        "tasks_processed": int,  # 已处理总数
        "tasks_pending": int,  # 待处理任务数（max(0, input - processed)）
    }
```

## ビジー時間（実測）

ビジー時間はもはや推定に依存せず、スケジューラが各タスクの実際の実行期間中に `begin_task()` / `end_task()` で打点し、ウォールクロック時間を直接累積します：

```python
def begin_task(self) -> None:
    """一个任务开始实际执行。"""


def end_task(self) -> None:
    """一个任务执行结束（含重试全部结束）。"""


def get_elapsed(self) -> float:
    """累计忙碌墙钟时间（秒），含当前尚未闭合的时间片。"""
```

実装メカニズム：

- `begin_task()` は `_in_flight` を 1 増やします；`0 → 1`（ノードがアイドルからビジーへ）になったとき `_busy_since = time.perf_counter()` を記録します。
- `end_task()` は `_in_flight` を 1 減らします；`1 → 0`（ノードがビジーからアイドルへ）になり、かつ `_busy_since` が非空のとき、`perf_counter() - _busy_since` を `busy_seconds` に加算し、`_busy_since` をクリアします。
- `get_elapsed()` は確定済み時間スライスの合計を返します；現在未確定の時間スライスが存在する場合は、`perf_counter() - _busy_since` をさらに加算します。

したがって、ノードがタスクを待ってアイドル状態だった時間は計上されず、実際のビジー時間を反映します。

## 使用例

以下の例は `TaskMetrics` のコアな使い方を示します：カウンター操作、上流/下流の統計、状態照会。

```python
from celestialflow.runtime import TaskMetrics
from celestialflow.runtime.util_types import ValueWrapper

# 1. 初始化指标管理器
metrics = TaskMetrics()

# 2. 添加可重试异常类型
metrics.set_retry_exceptions(ConnectionError, TimeoutError)

# 3. 模拟任务处理过程
# 外部直接注入 3 个任务
metrics.add_external_input_count(3)
# 上游节点提供 2 个任务
metrics.set_upstream_counter("upstream_a", ValueWrapper(value=2))

# 处理成功 3 个、失败 1 个、重复 1 个
metrics.add_success_count(3)
metrics.add_fail_count(1)
metrics.add_duplicate_count(1)

# 4. 查询各计数器的值
print(f"外部注入: {metrics.get_external_input_count()}")  # 3
print(f"上游提供: {metrics.get_upstream_input_count()}")  # 2
print(f"任务总数: {metrics.get_input_count()}")  # 5
print(f"成功数: {metrics.get_success_count()}")  # 3
print(f"失败数: {metrics.get_fail_count()}")  # 1
print(f"重复数: {metrics.get_duplicate_count()}")  # 1

# 5. 获取完整快照字典
counts = metrics.get_counts()
print(f"已处理: {counts['tasks_processed']}")  # 3+1+1 = 5
print(f"待处理: {counts['tasks_pending']}")  # 0
print(f"全部完成: {metrics.is_tasks_finished()}")  # True
```

### 上流/下流トラフィック統計

```python
from celestialflow.runtime import TaskMetrics
from celestialflow.runtime.util_types import ValueWrapper

metrics = TaskMetrics()
metrics.set_upstream_counter("producer", ValueWrapper(value=10))
metrics.set_downstream_counter("consumer", ValueWrapper(value=4))
metrics.add_downstream_count("consumer", 2)

print(metrics.get_upstream_counts())  # {'producer': 10}
print(metrics.get_downstream_counts())  # {'consumer': 6}
```

### 実測ビジー時間

```python
import time
from celestialflow.runtime import TaskMetrics

metrics = TaskMetrics()

metrics.begin_task()
time.sleep(0.05)  # 模拟任务执行
print(f"执行中: {metrics.get_elapsed():.3f}s")  # ≈ 0.050

metrics.end_task()
elapsed_after = metrics.get_elapsed()
time.sleep(0.05)  # 空闲等待
print(f"空闲后基本不变: {metrics.get_elapsed() == elapsed_after}")  # True
```
