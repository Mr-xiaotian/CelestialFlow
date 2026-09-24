# src/celestialflow/runtime/util_types.py

> 📅 最終更新日: 2026/09/24

`util_types.py` はフレームワークで使用される基本データ型、列挙型、補助クラスを定義します。

## TerminationSignal

タスクキュー終了をマークするセンチネルオブジェクト。ノードがこのシグナルを受信すると、上流にもはやタスクが存在しないことを示し、停止準備に入るべきです。

```python
class TerminationSignal:
    def __init__(self, _id: int = -1, source: str = "input"):
        self.id = _id  # 终止信号 ID
        self.source = source  # 来源标识


# 全局单例
TERMINATION_SIGNAL = TerminationSignal()
```

## TerminationIdPool

終了シグナル ID プール。受信済みのすべての終了シグナル ID を格納するために使用します。

```python
class TerminationIdPool:
    def __init__(self, ids: list[int]):
        self.ids = ids  # 终止信号 ID 列表
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
        :param value: 初始值
        :param lock: 可选的线程锁。默认 None 表示自建一把锁；
            传入已存在的 Lock 可让多个计数器共用同一把锁；
            显式传入 NoOpContext 则关闭加锁（仅适用于单线程访问）
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

## StageStatus

タスクグラフノード（`BaseTaskNode` およびそのサブクラス、`TaskExecutor`、`TaskSplitter`、`TaskRouter` など）の実行状態を表す列挙型です。

```python
class StageStatus(IntEnum):
    NOT_STARTED = 0  # 未启动
    RUNNING = 1  # 运行中
    STOPPED = 2  # 已停止
```

## CTreeEvent

CelestialTree イベント名定数。タスクトレーシングと可視化に使用されます。

| 定数 | 値 | 発生タイミング |
|------|-----|---------|
| `TASK_INPUT` | `"task.input"` | タスクがシステムに入力 |
| `TASK_SUCCESS` | `"task.success"` | タスク実行成功 |
| `TASK_ERROR` | `"task.error"` | タスク実行失敗 |
| `TASK_RETRY_PREFIX` | `"task.retry."` | リトライプレフィックス（リトライ回数を連結） |
| `TERMINATION_INPUT` | `"termination.input"` | 終了シグナル注入 |
| `TERMINATION_MERGE` | `"termination.merge"` | 終了シグナルマージ |

## 使用例

以下の例は `util_types` モジュールの各データクラスとユーティリティクラスの典型的な使用方法を示します。

### TerminationSignal と TerminationIdPool

```python
from celestialflow.runtime.util_types import (
    TerminationSignal,
    TERMINATION_SIGNAL,
    TerminationIdPool,
)

# 创建自定义终止信号
signal = TerminationSignal(_id=42, source="my_source")
print(f"信号 ID: {signal.id}, 来源: {signal.source}")

# 使用全局单例
print(f"默认终止信号 ID: {TERMINATION_SIGNAL.id}")  # -1
print(f"默认来源: {TERMINATION_SIGNAL.source}")  # "input"
print(
    f"是同一个实例: {TERMINATION_SIGNAL is TerminationSignal()}"
)  # False（每次创建新实例）

# 创建终止信号 ID 池
pool = TerminationIdPool(ids=[1, 2, 3])
print(f"ID 池: {pool.ids}")  # [1, 2, 3]
```

### StageStatus 列挙型

```python
from celestialflow.runtime.util_types import StageStatus

# 枚举值
print(f"NOT_STARTED = {StageStatus.NOT_STARTED.value}")  # 0
print(f"RUNNING = {StageStatus.RUNNING.value}")  # 1
print(f"STOPPED = {StageStatus.STOPPED.value}")  # 2

# 状态转换
status = StageStatus.NOT_STARTED
print(f"初始状态: {status.name}")
```

### ValueWrapper

```python
from celestialflow.runtime.util_types import ValueWrapper

# 默认带真实线程锁
counter = ValueWrapper(value=10)
print(f"初始值: {counter.value}")  # 10

counter.add(5)
print(f"递增后: {counter.get()}")  # 15

# 与其它计数器共用同一把锁
from threading import Lock

shared = Lock()
a = ValueWrapper(value=0, lock=shared)
b = ValueWrapper(value=0, lock=shared)
print(f"共用锁: {a.get_lock() is b.get_lock()}")  # True
```

### NoOpContext

```python
from celestialflow.runtime.util_types import NoOpContext, ValueWrapper

# 空上下文管理器，用于禁用 with 逻辑
ctx = NoOpContext()
with ctx:
    print("这是一个无操作上下文")

# 单线程场景下显式关闭加锁
single_thread_counter = ValueWrapper(value=0, lock=NoOpContext())
```

### CTreeEvent 定数

```python
from celestialflow.runtime.util_types import CTreeEvent

# 事件名称常量
print(f"任务输入事件: {CTreeEvent.TASK_INPUT}")  # "task.input"
print(f"任务成功事件: {CTreeEvent.TASK_SUCCESS}")  # "task.success"
print(f"任务失败事件: {CTreeEvent.TASK_ERROR}")  # "task.error"
print(f"重试前缀: {CTreeEvent.TASK_RETRY_PREFIX}")  # "task.retry."
print(f"终止注入事件: {CTreeEvent.TERMINATION_INPUT}")  # "termination.input"
print(f"终止合并事件: {CTreeEvent.TERMINATION_MERGE}")  # "termination.merge"
```

## 注意事項

- `ValueWrapper` はデフォルトで実際の `Lock` を使用するため、デフォルトでスレッドセーフです；`NoOpContext` は単一スレッドモードでロックのオーバーヘッドを明示的に排除するために使用します。
- `TERMINATION_SIGNAL` はモジュールレベルのシングルトンで、デフォルトは `id=-1`、`source="input"` です。
- `StageStatus` は `IntEnum` であり、整数と直接比較できます。
