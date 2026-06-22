# TaskTypes

> 📅 最后更新日期: 2026/06/22


TaskTypes 模块定义了框架中使用的基础数据类型、枚举和辅助类。

## StageStatus

枚举类，表示 `TaskStage` 的运行状态。

```python
class StageStatus(IntEnum):
    NOT_STARTED = 0  # 未启动
    RUNNING = 1      # 运行中
    STOPPED = 2      # 已停止
```

## TerminationSignal

用于标记任务队列终止的哨兵对象。当 Stage 接收到此信号时，表示上游已无更多任务，应当准备停止。

```python
class TerminationSignal:
    def __init__(self, _id: int = -1, source: str = "input"):
        self.id = _id        # 事件 ID
        self.source = source  # 来源

# 全局单例
TERMINATION_SIGNAL = TerminationSignal()
```

## TerminationIdPool

终止信号 ID 池，用于存储所有已接收的终止信号 ID。

```python
class TerminationIdPool:
    def __init__(self, ids: list[int]):
        self.ids = ids   # 终止信号 ID 列表
        self.id = -1     # 兼容字段，固定为 -1
        self.source = "<signal>"  # 兼容字段，固定为 "<signal>"
```

## NoOpContext

空上下文管理器，用于禁用 `with` 逻辑（例如当无需锁时）。

```python
class NoOpContext:
    def __enter__(self) -> "NoOpContext": ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
```

## ValueWrapper

线程内/单进程的计数器包装，可选配锁。

```python
class ValueWrapper:
    def __init__(self, value: int, lock: Lock | NoOpContext | None = None):
        self.value = value
        self._lock = lock or NoOpContext()

    def get_lock(self) -> Lock | NoOpContext:
        """返回锁对象或 NoOpContext（无锁时）。"""
```

## SumCounter

累加多个 counter（ValueWrapper）的总和计数器。

```python
class SumCounter:
    def __init__(self, lock: Lock | NoOpContext | None = None):
        """
        :param lock: 可选的线程锁，默认 None（使用 NoOpContext）
        """
        self.init_value = ValueWrapper(value=0, lock=self.lock)
        self.counters = []
```

### 方法

| 方法 | 说明 |
|------|------|
| `add(value)` | 增加初始计数值（加到 `init_value`） |
| `append_counter(counter)` | 追加外部计数器 |
| `reset()` | 重置所有计数器归零 |
| `get()` | 获取所有计数器的累加值 |
| `value`（属性） | 累加所有计数器的总值 |

### 使用示例

```python
from celestialflow.runtime.util_types import SumCounter, ValueWrapper

counter = SumCounter()
counter.add(10)

sub_counter = ValueWrapper(value=5)
counter.append_counter(sub_counter)

print(counter.get())  # 15
```

## CTreeEvent

CelestialTree 事件名称常量，用于任务追踪和可视化。

| 常量 | 值 | 触发时机 |
|------|-----|---------|
| `TASK_INPUT` | `"task.input"` | 任务进入系统 |
| `TASK_SUCCESS` | `"task.success"` | 任务执行成功 |
| `TASK_ERROR` | `"task.error"` | 任务执行失败 |
| `TASK_RETRY_PREFIX` | `"task.retry."` | 重试前缀（拼接重试次数） |
| `TASK_DUPLICATE` | `"task.duplicate"` | 检测到重复任务 |
| `TERMINATION_INPUT` | `"termination.input"` | 注入终止信号 |
| `TERMINATION_MERGE` | `"termination.merge"` | 合并终止信号 |



## 使用示例

以下示例展示 `util_types` 模块中各数据类和工具类的典型用法。

### TerminationSignal 和 TerminationIdPool

```python
from celestialflow.runtime.util_types import TerminationSignal, TERMINATION_SIGNAL, TerminationIdPool

# 创建自定义终止信号
signal = TerminationSignal(_id=42, source="my_source")
print(f"信号 ID: {signal.id}, 来源: {signal.source}")

# 使用全局单例
print(f"默认终止信号 ID: {TERMINATION_SIGNAL.id}")      # -1
print(f"默认来源: {TERMINATION_SIGNAL.source}")         # "input"
print(f"是同一个实例: {TERMINATION_SIGNAL is TerminationSignal()}")  # False（每次创建新实例）

# 创建终止信号 ID 池
pool = TerminationIdPool(ids=[1, 2, 3])
print(f"ID 池: {pool.ids}")  # [1, 2, 3]
```

### StageStatus 枚举

```python
from celestialflow.runtime.util_types import StageStatus

# 枚举值
print(f"NOT_STARTED = {StageStatus.NOT_STARTED.value}")  # 0
print(f"RUNNING = {StageStatus.RUNNING.value}")          # 1
print(f"STOPPED = {StageStatus.STOPPED.value}")          # 2

# 状态转换
status = StageStatus.NOT_STARTED
print(f"初始状态: {status.name}")
```

### ValueWrapper 和 SumCounter

```python
from celestialflow.runtime.util_types import ValueWrapper, SumCounter

# ValueWrapper：带可选锁的计数器
counter = ValueWrapper(value=10)
print(f"初始值: {counter.value}")  # 10
with counter.get_lock():
    counter.value += 5
print(f"加锁递增后: {counter.value}")  # 15

# SumCounter：多计数器累加
sum_counter = SumCounter()
sum_counter.add(100)

sub1 = ValueWrapper(value=20)
sub2 = ValueWrapper(value=30)
sum_counter.append_counter(sub1)
sum_counter.append_counter(sub2)

print(f"总和 (100 + 20 + 30): {sum_counter.value}")  # 150

# 重置
sum_counter.reset()
print(f"重置后: {sum_counter.value}")  # 0
```

### NoOpContext

```python
from celestialflow.runtime.util_types import NoOpContext

# 空上下文管理器，用于禁用 with 逻辑
ctx = NoOpContext()
with ctx:
    print("这是一个无操作上下文")
```

### CTreeEvent 常量

```python
from celestialflow.runtime.util_types import CTreeEvent

# 事件名称常量
print(f"任务输入事件: {CTreeEvent.TASK_INPUT}")           # "task.input"
print(f"任务成功事件: {CTreeEvent.TASK_SUCCESS}")         # "task.success"
print(f"任务失败事件: {CTreeEvent.TASK_ERROR}")           # "task.error"
print(f"重试前缀: {CTreeEvent.TASK_RETRY_PREFIX}")        # "task.retry."
print(f"重复任务事件: {CTreeEvent.TASK_DUPLICATE}")       # "task.duplicate"
print(f"终止注入事件: {CTreeEvent.TERMINATION_INPUT}")    # "termination.input"
print(f"终止合并事件: {CTreeEvent.TERMINATION_MERGE}")    # "termination.merge"
```



## 注意事项

- `ValueWrapper` 和 `SumCounter` 的线程安全依赖于调用方传入正确的 `Lock` 对象。
- `NoOpContext` 用于 `serial`/`async` 模式下替代真实锁，避免不必要的锁开销。
