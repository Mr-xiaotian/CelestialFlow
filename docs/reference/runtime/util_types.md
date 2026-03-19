# TaskTypes

TaskTypes 模块定义了框架中使用的基础数据类型、枚举和辅助类。

## StageStatus

枚举类，表示 `TaskStage` 的运行状态。

```python
class StageStatus(IntEnum):
    NOT_STARTED = 0  # 未启动
    RUNNING = 1      # 运行中
    STOPPED = 2      # 已停止
```

使用示例：
```python
from celestialflow.runtime.util_types import StageStatus

status = stage.get_status()
if status == StageStatus.RUNNING:
    print("节点正在运行")
```

## TerminationSignal

用于标记任务队列终止的哨兵对象。当 Stage 接收到此信号时，表示上游已无更多任务，应当准备停止。

```python
class TerminationSignal:
    def __init__(self, _id: int = -1, source: str = "input"):
        self.id = _id        # 事件 ID
        self.source = source  # 来源

# 单例
TERMINATION_SIGNAL = TerminationSignal()
```

### 使用场景

```python
from celestialflow.runtime import TerminationSignal

# 注入终止信号
queue.put(TerminationSignal())

# 检测终止信号
if isinstance(record, TerminationSignal):
    break  # 停止处理
```

## TerminationIdPool

终止信号 ID 池，用于存储所有已接收的终止信号 ID。

```python
class TerminationIdPool:
    def __init__(self, ids: list[int]):
        self.ids = ids
```

## NoOpContext

空上下文管理器，可用于禁用 `with` 逻辑。

```python
class NoOpContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
```

使用场景：
```python
# 当不需要锁时，返回 NoOpContext
def get_lock(self):
    return self._lock or NoOpContext()
```

## ValueWrapper

线程内/单进程的计数器包装，可选配锁。

```python
class ValueWrapper:
    def __init__(self, value=0, lock=None):
        self.value = value
        self._lock = lock

    def get_lock(self):
        """返回锁对象或 NoOpContext"""
        return self._lock or NoOpContext()
```

## SumCounter

累加多个 counter（支持 ValueWrapper / MPValue）。

```python
class SumCounter:
    def __init__(self, mode: str = "serial"):
        """
        初始化计数器。

        :param mode: 模式 ('serial', 'thread', 'process')
        """
```

### 方法

```python
# 添加初始值
def add_init_value(self, value: int) -> None

# 追加计数器
def append_counter(self, counter: ValueWrapper) -> None

# 重置所有计数器
def reset(self) -> None

# 获取总值
@property
def value(self) -> int
```

### 使用示例

```python
from celestialflow.runtime.util_types import SumCounter, ValueWrapper

# 线程模式
counter = SumCounter(mode="thread")
counter.add_init_value(10)

# 添加子计数器
sub_counter = ValueWrapper(value=5)
counter.append_counter(sub_counter)

print(counter.value)  # 15
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

## 异常类

异常类定义在 `runtime/util_errors.py` 中：

| 异常类 | 说明 |
|--------|------|
| `CelestialFlowError` | 基础异常类 |
| `ConfigurationError` | 配置错误 |
| `InvalidOptionError` | 无效选项错误 |
| `ExecutionModeError` | 执行模式错误 |
| `StageModeError` | 节点模式错误 |
| `LogLevelError` | 日志级别错误 |
| `RemoteWorkerError` | 远程 Worker 错误 |
| `UnconsumedError` | 任务未被消费错误 |
| `PickleError` | 序列化错误 |