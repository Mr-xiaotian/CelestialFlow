# src/celestialflow/runtime/util_types.py

> 📅 最后更新日期: 2026/09/24

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

## StageStatus

任务图节点（`BaseTaskNode` 及其子类，如 `TaskExecutor`、`TaskSplitter`、`TaskRouter`）的运行状态枚举。

```python
class StageStatus(IntEnum):
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
| `TASK_RETRY_PREFIX` | `"task.retry."` | 重试前缀（拼接重试次数） |
| `TERMINATION_INPUT` | `"termination.input"` | 注入终止信号 |
| `TERMINATION_MERGE` | `"termination.merge"` | 合并终止信号 |

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

### StageStatus 枚举

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
- `StageStatus` 为 `IntEnum`，可直接与整数比较。
