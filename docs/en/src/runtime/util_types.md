# src/celestialflow/runtime/util_types.py

> 📅 Last Updated: 2026/09/24

`util_types.py` defines the basic data types, enums, and helper classes used throughout the framework.

## TerminationSignal

A sentinel object used to mark the end of a task queue. When a node receives this signal, it indicates that the upstream has no more tasks, and the node should prepare to stop.

```python
class TerminationSignal:
    def __init__(self, _id: int = -1, source: str = "input"):
        self.id = _id  # 终止信号 ID
        self.source = source  # 来源标识


# 全局单例
TERMINATION_SIGNAL = TerminationSignal()
```

## TerminationIdPool

Termination signal ID pool, used to store all received termination signal IDs.

```python
class TerminationIdPool:
    def __init__(self, ids: list[int]):
        self.ids = ids  # 终止信号 ID 列表
```

## NoOpContext

An empty context manager, used to disable `with` logic.

```python
class NoOpContext:
    def __enter__(self) -> NoOpContext: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

`__exit__` ignores all exception information and does not swallow exceptions itself (returns `None`).

## ValueWrapper

A counter wrapper for intra-thread / single-process use, **which creates its own thread lock by default**, or can explicitly disable locking.

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

| Method | Description |
|------|------|
| `get_lock()` | Returns the lock object; returns `NoOpContext` when locking is disabled |
| `add(value)` | Increments `value` while holding the lock |
| `get()` | Reads the current value while holding the lock |

> Because `lock=None` creates a real `Lock`, `ValueWrapper` is thread-safe by default; you should explicitly pass `NoOpContext` to disable locking only when single-threaded access is certain.

## StageStatus

The running-state enum for task graph nodes (`BaseTaskNode` and its subclasses, such as `TaskExecutor`, `TaskSplitter`, `TaskRouter`).

```python
class StageStatus(IntEnum):
    NOT_STARTED = 0  # 未启动
    RUNNING = 1  # 运行中
    STOPPED = 2  # 已停止
```

## CTreeEvent

CelestialTree event name constants, used for task tracking and visualization.

| Constant | Value | Trigger Timing |
|----------|-------|----------------|
| `TASK_INPUT` | `"task.input"` | Task enters the system |
| `TASK_SUCCESS` | `"task.success"` | Task execution succeeded |
| `TASK_ERROR` | `"task.error"` | Task execution failed |
| `TASK_RETRY_PREFIX` | `"task.retry."` | Retry prefix (concatenated with retry count) |
| `TERMINATION_INPUT` | `"termination.input"` | Termination signal injected |
| `TERMINATION_MERGE` | `"termination.merge"` | Termination signals merged |

## Usage Examples

The following examples demonstrate typical usage of the data classes and helper classes in the `util_types` module.

### TerminationSignal and TerminationIdPool

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

### StageStatus Enum

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

### CTreeEvent Constants

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

## Notes

- `ValueWrapper` uses a real `Lock` by default, so it is thread-safe by default; `NoOpContext` is used to explicitly eliminate lock overhead in single-threaded mode.
- `TERMINATION_SIGNAL` is a module-level singleton with default `id=-1` and `source="input"`.
- `StageStatus` is an `IntEnum`, so it can be compared directly with integers.
