# src/celestialflow/runtime/util_types.py

> 📅 最終更新日: 2026/10/09

`util_types.py` はフレームワークで使用される基本データ型、列挙型、補助クラスを定義します。

## TerminationSignal

タスクキュー終了をマークするセンチネルオブジェクト。ノードがこのシグナルを受信すると、上流にもはやタスクが存在しないことを示し、停止準備に入るべきです。

```python
class TerminationSignal:
    def __init__(self, _id: int = -1, source: str = "input"):
        self.id = _id  # 終了シグナル ID
        self.source = source  # ソース識別子


# グローバルシングルトン
TERMINATION_SIGNAL = TerminationSignal()
```

## TerminationIdPool

終了シグナル ID プール。受信済みのすべての終了シグナル ID を格納するために使用します。

```python
class TerminationIdPool:
    def __init__(self, ids: list[int]):
        self.ids = ids  # 終了シグナル ID リスト
```

## NoOpContext

空のコンテキストマネージャ。`with` ロジックを無効化するために使用します。

```python
class NoOpContext:
    def __enter__(self) -> NoOpContext: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

`__exit__` はすべての例外情報を無視し、自身では例外を飲み込みません（`None` を返します）。

## ValueWrapper

スレッド内/単一プロセス用のカウンターラッパー。**デフォルトで自前のスレッドロックを作成**し、明示的にロックを無効化することもできます。

```python
class ValueWrapper:
    def __init__(self, value: int, lock: Lock | NoOpContext | None = None):
        """
        :param value: 初期値
        :param lock: 任意のスレッドロック。デフォルトの None は自前のロックを作成することを示す；
            既存の Lock を渡すと複数のカウンターが同じロックを共有できる；
            明示的に NoOpContext を渡すとロックが無効になる（単一スレッドアクセス時のみ）
        """
        self.value = value
        self._lock = lock if lock is not None else Lock()
```

| メソッド | 説明 |
|------|------|
| `get_lock()` | ロックオブジェクトを取得；ロック無効時は `NoOpContext` を返す |
| `add(value)` | ロックを保持した状態で `value` を増加 |
| `get()` | ロックを保持した状態で現在値を読み取る |

> `lock=None` の場合に実際の `Lock` を自前で作成するため、`ValueWrapper` はデフォルトでスレッドセーフです；明示的に単一スレッドアクセスと分かっている場合にのみ `NoOpContext` を渡してロックを無効化すべきです。

## NodeStatus

タスクグラフノード（`BaseTaskNode` およびそのサブクラス、`TaskExecutor`、`TaskSplitter`、`TaskRouter` など）のライフサイクル状態を表す列挙型です。

```python
class NodeStatus(IntEnum):
    NOT_STARTED = 0  # 未起動
    RUNNING = 1  # 実行中
    STOPPED = 2  # 停止済み
```

## CTreeEvent

CelestialTree イベント名定数。タスクトレーシングと可視化に使用されます。

| 定数 | 値 | 発生タイミング |
|------|-----|---------|
| `TASK_INPUT` | `"task.input"` | タスクがシステムに入力 |
| `TASK_SUCCESS` | `"task.success"` | タスク実行成功 |
| `TASK_ERROR` | `"task.error"` | タスク実行失敗 |
| `TASK_SKIP` | `"task.skip"` | タスクがスキップされる |
| `TASK_RETRY_PREFIX` | `"task.retry."` | リトライプレフィックス（リトライ回数を連結） |
| `TERMINATION_INPUT` | `"termination.input"` | 終了シグナル注入 |
| `TERMINATION_MERGE` | `"termination.merge"` | 終了シグナルマージ |

## NodeMetrics

単一ノードの指標スナップショット（読み取り専用 DTO、`@dataclass(frozen=True, slots=True)`）。指標オブザーバーがイベントに基づいて書き込みモデルを維持し、本クラスはある時点の読み取り専用スナップショットのみを保持します。

| フィールド | 型 | 説明 |
|------|------|------|
| `node` | `str` | ノード名 |
| `status` | `NodeStatus` | ノードのライフサイクル状態 |
| `start_time` | `float` | 実行状態に入った壁時計時刻（秒）；未起動なら `0.0` |
| `external_input` | `int` | 外部注入タスク数 |
| `upstream_input` | `int` | 上流から提供されたタスク数 |
| `input_total` | `int` | 入力タスク総数（外部注入と上流提供の合計） |
| `succeeded` | `int` | 成功タスク数 |
| `failed` | `int` | 失敗タスク数 |
| `skipped` | `int` | スキップタスク数 |
| `processed` | `int` | 処理済みタスク数（成功 + 失敗 + スキップ） |
| `pending` | `int` | 未処理タスク数 |
| `upstream_counts` | `dict[str, int]` | 各上流ノードが提供したタスク数のマッピング |
| `downstream_counts` | `dict[str, int]` | 各下流ノードへ送信したタスク数のマッピング |

## MetricsView

指標の読み取り専用ビュー・プロトコル（`Protocol`）。書き込みモデルは指標オブザーバーがイベントに基づいて維持し、本プロトコルは不変の読み取り入口のみを公開します。ログ・レポートなどの消費者がクエリに使用し、可変の内部状態が外部に漏れるのを防ぎます。

```python
class MetricsView(Protocol):
    def get_node_metrics(self, node: str) -> NodeMetrics | None: ...
    def get_graph_metrics(self) -> dict[str, NodeMetrics]: ...
```

## 使用例

以下の例は `util_types` モジュールの各データクラスとユーティリティクラスの典型的な使用方法を示します。

### TerminationSignal と TerminationIdPool

```python
from celestialflow.runtime.util_types import (
    TerminationSignal,
    TERMINATION_SIGNAL,
    TerminationIdPool,
)

# カスタム終了シグナルを作成
signal = TerminationSignal(_id=42, source="my_source")
print(f"シグナル ID: {signal.id}, ソース: {signal.source}")

# グローバルシングルトンを使用
print(f"デフォルト終了シグナル ID: {TERMINATION_SIGNAL.id}")  # -1
print(f"デフォルトソース: {TERMINATION_SIGNAL.source}")  # "input"
print(
    f"同じインスタンス: {TERMINATION_SIGNAL is TerminationSignal()}"
)  # False（毎回新しいインスタンスを作成）

# 終了シグナル ID プールを作成
pool = TerminationIdPool(ids=[1, 2, 3])
print(f"ID プール: {pool.ids}")  # [1, 2, 3]
```

### NodeStatus 列挙型

```python
from celestialflow.runtime.util_types import NodeStatus

# 列挙値
print(f"NOT_STARTED = {NodeStatus.NOT_STARTED.value}")  # 0
print(f"RUNNING = {NodeStatus.RUNNING.value}")  # 1
print(f"STOPPED = {NodeStatus.STOPPED.value}")  # 2

# 状態遷移
status = NodeStatus.NOT_STARTED
print(f"初期状態: {status.name}")
```

### NodeMetrics と MetricsView

```python
from celestialflow.runtime.util_types import NodeMetrics, NodeStatus, MetricsView

# 読み取り専用の指標スナップショットを構築
snapshot = NodeMetrics(
    node="processor",
    status=NodeStatus.RUNNING,
    start_time=1234.5,
    external_input=3,
    upstream_input=2,
    input_total=5,
    succeeded=3,
    failed=1,
    skipped=1,
    processed=5,
    pending=0,
    upstream_counts={"producer": 2},
    downstream_counts={"store": 5},
)
print(snapshot.processed)  # 5
```

### ValueWrapper

```python
from celestialflow.runtime.util_types import ValueWrapper

# デフォルトで実際のスレッドロックを保持
counter = ValueWrapper(value=10)
print(f"初期値: {counter.value}")  # 10

counter.add(5)
print(f"増加後: {counter.get()}")  # 15

# 別のカウンターと同じロックを共有
from threading import Lock

shared = Lock()
a = ValueWrapper(value=0, lock=shared)
b = ValueWrapper(value=0, lock=shared)
print(f"ロック共有: {a.get_lock() is b.get_lock()}")  # True
```

### NoOpContext

```python
from celestialflow.runtime.util_types import NoOpContext, ValueWrapper

# 空のコンテキストマネージャ。with ロジックを無効化するために使用
ctx = NoOpContext()
with ctx:
    print("これは無操作コンテキストです")

# 単一スレッド環境でロックを明示的に無効化
single_thread_counter = ValueWrapper(value=0, lock=NoOpContext())
```

### CTreeEvent 定数

```python
from celestialflow.runtime.util_types import CTreeEvent

# イベント名定数
print(f"タスク入力イベント: {CTreeEvent.TASK_INPUT}")  # "task.input"
print(f"タスク成功イベント: {CTreeEvent.TASK_SUCCESS}")  # "task.success"
print(f"タスク失敗イベント: {CTreeEvent.TASK_ERROR}")  # "task.error"
print(f"リトライプレフィックス: {CTreeEvent.TASK_RETRY_PREFIX}")  # "task.retry."
print(f"終了注入イベント: {CTreeEvent.TERMINATION_INPUT}")  # "termination.input"
print(f"終了マージイベント: {CTreeEvent.TERMINATION_MERGE}")  # "termination.merge"
```

## 注意事項

- `ValueWrapper` はデフォルトで実際の `Lock` を使用するため、デフォルトでスレッドセーフです；`NoOpContext` は単一スレッドモードでロックのオーバーヘッドを明示的に排除するために使用します。
- `TERMINATION_SIGNAL` はモジュールレベルのシングルトンで、デフォルトは `id=-1`、`source="input"` です。
- `NodeStatus` は `IntEnum` であり、整数と直接比較できます。