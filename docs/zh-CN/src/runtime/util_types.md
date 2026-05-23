# TaskTypes

> 📅 最后更新日期: 2026/05/24

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
        self.ids = ids
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
    def __init__(self, value: int = 0, lock: Lock | None = None):
        self.value = value
        self._lock = lock

    def get_lock(self) -> Lock | NoOpContext:
        """返回锁对象或 NoOpContext（无锁时）。"""
```

## SumCounter

累加多个 counter（ValueWrapper）的总和计数器。

```python
class SumCounter:
    def __init__(self, mode: str = "serial"):
        """
        :param mode: 执行模式，'serial'（无锁）或 'thread'（带锁）
        """
```

### 方法

| 方法 | 说明 |
|------|------|
| `add_init_value(value)` | 增加初始值 |
| `append_counter(counter)` | 追加外部计数器 |
| `reset()` | 重置所有计数器归零 |
| `value`（属性） | 累加所有计数器的总值 |

### 使用示例

```python
from celestialflow.runtime.util_types import SumCounter, ValueWrapper

counter = SumCounter(mode="thread")
counter.add_init_value(10)

sub_counter = ValueWrapper(value=5)
counter.append_counter(sub_counter)

print(counter.value)  # 15
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

## PersistedErrorRecord

持久化错误记录数据类。

```python
@dataclass(frozen=True)
class PersistedErrorRecord:
    error_type: str          # 错误类型名称
    error_message: str       # 错误消息
    error_repr: str          # 错误的完整展示字符串
    stage: str               # 错误所属节点标签
    error_id: int | None     # 错误事件 ID
    timestamp: str           # 错误时间戳字符串
    ts: float | None         # 错误时间戳

    def __str__(self) -> str: ...
    def get_group_key(self) -> tuple[str, str]:
        """返回 (error_type, error_message) 用于分组。"""
```

## STAGE_STYLE

节点标签样式配置，用于 CelestialTree 可视化。

```python
from celestialtree import NodeLabelStyle

STAGE_STYLE = NodeLabelStyle(
    template="{base}  {payload.name}  ‹{type}›",
    missing="-"
)
```
