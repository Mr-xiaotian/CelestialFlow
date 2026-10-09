# src/celestialflow/runtime/util_types.py

> 📅 最后更新日期: 2026/10/09

`util_types.py` 定义了框架中使用的基础数据类型、枚举和辅助类。

## TerminationSignal

用于标记任务队列终止的哨兵对象。当节点接收到此信号时，表示上游已无更多任务，应当准备停止。

```python
class TerminationSignal:
    def __init__(self, _id: int = -1, source: str = "input"):
        self.id = _id  # 终止信号 ID
        self.source = source  # 来源标识


# 全局单例
TERMINATION_SIGNAL = TerminationSignal()
```

## TerminationIdPool

终止信号 ID 池，用于存储所有已接收的终止信号 ID。

```python
class TerminationIdPool:
    def __init__(self, ids: list[int]):
        self.ids = ids  # 终止信号 ID 列表
```

## NoOpContext

空上下文管理器，用于禁用 `with` 逻辑。

```python
class NoOpContext:
    def __enter__(self) -> NoOpContext: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

`__exit__` 忽略所有异常信息，本身不吞掉异常（返回 `None`）。

## ValueWrapper

线程内/单进程的计数器包装，**默认自建一把线程锁**，也可显式关闭加锁。

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

| 方法 | 说明 |
|------|------|
| `get_lock()` | 获取锁对象；关闭加锁时返回 `NoOpContext` |
| `add(value)` | 在持锁状态下增加 `value` |
| `get()` | 在持锁状态下读取当前值 |

> 因为 `lock=None` 时会自建一把真实 `Lock`，`ValueWrapper` 默认就是线程安全的；只有在明确单线程访问时才应显式传入 `NoOpContext` 关闭加锁。

## NodeStatus

任务图节点（`BaseTaskNode` 及其子类，如 `TaskExecutor`、`TaskSplitter`、`TaskRouter`）的生命周期状态枚举。

```python
class NodeStatus(IntEnum):
    NOT_STARTED = 0  # 未启动
    RUNNING = 1  # 运行中
    STOPPED = 2  # 已停止
```

## CTreeEvent

CelestialTree 事件名称常量，用于任务追踪和可视化。

| 常量 | 值 | 触发时机 |
|------|-----|---------|
| `TASK_INPUT` | `"task.input"` | 任务进入系统 |
| `TASK_SUCCESS` | `"task.success"` | 任务执行成功 |
| `TASK_ERROR` | `"task.error"` | 任务执行失败 |
| `TASK_SKIP` | `"task.skip"` | 任务被跳过 |
| `TASK_RETRY_PREFIX` | `"task.retry."` | 重试前缀（拼接重试次数） |
| `TERMINATION_INPUT` | `"termination.input"` | 注入终止信号 |
| `TERMINATION_MERGE` | `"termination.merge"` | 合并终止信号 |

## NodeMetrics

单节点指标快照（只读 DTO，`@dataclass(frozen=True, slots=True)`）。由指标观察者依据事件维护写模型，本类只保存某一时刻的只读快照。

| 字段 | 类型 | 说明 |
|------|------|------|
| `node` | `str` | 节点名称 |
| `status` | `NodeStatus` | 节点生命周期状态 |
| `start_time` | `float` | 进入运行状态的墙钟时间（秒）；未启动为 `0.0` |
| `external_input` | `int` | 外部注入任务数 |
| `upstream_input` | `int` | 上游提供任务数 |
| `input_total` | `int` | 输入任务总数（外部注入与上游提供之和） |
| `succeeded` | `int` | 成功任务数 |
| `failed` | `int` | 失败任务数 |
| `skipped` | `int` | 跳过任务数 |
| `processed` | `int` | 已处理任务数（成功 + 失败 + 跳过） |
| `pending` | `int` | 待处理任务数 |
| `upstream_counts` | `dict[str, int]` | 各上游节点提供的任务数量映射 |
| `downstream_counts` | `dict[str, int]` | 发往各下游节点的任务数量映射 |

## MetricsView

指标只读视图协议（`Protocol`）。写模型由指标观察者依据事件维护，本协议只暴露不可变的读取入口，供日志、上报等消费者查询，避免把可变内部状态外泄。

```python
class MetricsView(Protocol):
    def get_node_metrics(self, node: str) -> NodeMetrics | None: ...
    def get_graph_metrics(self) -> dict[str, NodeMetrics]: ...
```

## 使用示例

以下示例展示 `util_types` 模块中各数据类和工具类的典型用法。

### TerminationSignal 和 TerminationIdPool

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

### NodeStatus 枚举

```python
from celestialflow.runtime.util_types import NodeStatus

# 枚举值
print(f"NOT_STARTED = {NodeStatus.NOT_STARTED.value}")  # 0
print(f"RUNNING = {NodeStatus.RUNNING.value}")  # 1
print(f"STOPPED = {NodeStatus.STOPPED.value}")  # 2

# 状态转换
status = NodeStatus.NOT_STARTED
print(f"初始状态: {status.name}")
```

### NodeMetrics 与 MetricsView

```python
from celestialflow.runtime.util_types import NodeMetrics, NodeStatus, MetricsView

# 构造只读指标快照
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

### CTreeEvent 常量

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

## 注意事项

- `ValueWrapper` 默认使用真实 `Lock`，因此默认线程安全；`NoOpContext` 用于单线程模式下显式关闭锁开销。
- `TERMINATION_SIGNAL` 是模块级单例，默认 `id=-1`、`source="input"`。
- `NodeStatus` 为 `IntEnum`，可直接与整数比较。
