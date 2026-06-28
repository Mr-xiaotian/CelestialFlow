# TaskErrors

> 📅 最后更新日期: 2026/06/28

TaskErrors 模块定义了 CelestialFlow 框架中使用的完整异常类体系。

## 异常层级

```
CelestialFlowError
├── ConfigurationError
│   └── InvalidOptionError
│       ├── ExecutionModeError      # ("serial", "thread", "async")
│       ├── StageModeError          # ("serial", "thread")
│       ├── LogLevelError           # (TRACE/DEBUG/SUCCESS/INFO/...)
│       ├── ScheduleModeError       # ("eager", "staged")
│       └── CallableParameterKindError  # 可调用对象参数 kind 不合法
├── GraphStructureError
│   ├── DuplicateNodeError          # 重复的节点名称
│   ├── UnknownNodeError            # 未知的节点名称
│   └── NodeNotFoundError           # 图中未找到指定节点
├── RuntimeStateError
│   ├── InitializationError         # 初始化失败
│   └── GraphManagedError           # 图管理错误
├── PersistedError                  # 持久化错误摘要
├── RemoteWorkerError               # 远端 Worker 执行失败
├── ReporterError                   # 上报器错误
├── CelestialTreeConnectionError    # CelestialTree 连接失败
├── CelestialFlowTimeoutError       # 超时错误
├── UnconsumedError                 # 标记未消费任务
├── TaskFormatError                 # 任务格式错误
└── TerminationMergeError           # 终止信号合并错误
```

## 基类

### CelestialFlowError

所有自定义异常的基类。

```python
class CelestialFlowError(Exception):
    """CelestialFlow 所有自定义异常的基类"""
    pass
```

## 配置相关异常（ConfigurationError）

### ConfigurationError

配置错误基类（参数非法、组合不支持等）。

```python
class ConfigurationError(CelestialFlowError):
    """配置错误（参数非法、组合不支持等）"""
    pass
```

### InvalidOptionError

某个配置项的取值不合法。

```python
class InvalidOptionError(ConfigurationError):
    def __init__(
        self,
        field: str,
        value: Any,
        allowed: Iterable[Any],
        *,
        prefix: str = "Invalid",
    ):
        """
        :param field: 配置项名称
        :param value: 实际传入值
        :param allowed: 允许的取值集合
        :param prefix: 错误消息前缀
        """
        # 示例: "Invalid execution mode: xxx. Valid options are ('serial', 'thread', 'async')."
```

### ExecutionModeError

`execution_mode` 配置错误。

```python
class ExecutionModeError(InvalidOptionError):
    """非法的 execution_mode"""
    def __init__(self, execution_mode: str, valid_modes=None):
        # valid_modes 默认为 ("serial", "thread", "async")
```

### StageModeError

`stage_mode` 配置错误。

```python
class StageModeError(InvalidOptionError):
    """非法的 stage_mode"""
    def __init__(self, stage_mode: str, valid_modes=None):
        # valid_modes 默认为 ("serial", "thread")
```

### LogLevelError

`log_level` 配置错误。

```python
class LogLevelError(InvalidOptionError):
    """非法的 log_level"""
    def __init__(self, log_level: str, valid_levels=None):
        # valid_levels 默认为 ("TRACE", "DEBUG", "SUCCESS", "INFO", "WARNING", "ERROR", "CRITICAL")
```

### ScheduleModeError

`schedule_mode` 配置错误。

```python
class ScheduleModeError(InvalidOptionError):
    """非法的 schedule_mode"""
    def __init__(self, schedule_mode: str, valid_modes=None):
        # valid_modes 默认为 ("eager", "staged")
```

### CallableParameterKindError

可调用对象参数 kind 不合法。

```python
class CallableParameterKindError(InvalidOptionError):
    def __init__(self, callable_name: str, parameter_kind: Any, valid_kinds: Iterable[Any]):
        """
        :param callable_name: 可调用对象名称
        :param parameter_kind: 实际参数 kind
        :param valid_kinds: 允许的参数 kind 集合
        """
```

## 图结构异常（GraphStructureError）

### GraphStructureError

图结构错误基类。

```python
class GraphStructureError(ConfigurationError):
    """图结构错误"""
    pass
```

### DuplicateNodeError

重复的节点名称（在 `set_stages` 或 `add_source_name` / `add_queue` 时触发）。

```python
class DuplicateNodeError(GraphStructureError):
    """重复的节点名称"""
    pass
```

### UnknownNodeError

未知的节点名称（在验证终止信号来源时触发）。

```python
class UnknownNodeError(GraphStructureError):
    """未知的节点名称"""
    pass
```

### NodeNotFoundError

图中未找到指定节点（在 `connect()` 或查询时触发）。

```python
class NodeNotFoundError(GraphStructureError):
    """图中未找到指定节点"""
    pass
```

## 运行时异常（RuntimeStateError）

### RuntimeStateError

运行时状态错误基类（重复启动、未初始化等）。

```python
class RuntimeStateError(CelestialFlowError):
    """运行时状态错误"""
    pass
```

### InitializationError

初始化错误（如线程池未初始化时使用）。

```python
class InitializationError(RuntimeStateError):
    """初始化错误"""
    pass
```

### GraphManagedError

当 Stage 已被 TaskGraph 管理时，尝试通过 standalone 路径直接调用 `start()` 时抛出。

```python
class GraphManagedError(RuntimeStateError):
    """Stage 已被 Graph 管理，不应通过 standalone 路径启动。"""
    def __init__(self, message: str = "This stage is managed by a TaskGraph. ..."):
        ...
```

## 持久化异常

### PersistedError

从持久化层恢复出的错误摘要对象。

```python
class PersistedError(CelestialFlowError):
    def __init__(self, error_type: str, error_message: str) -> None:
        self.error_type = error_type
        self.error_message = error_message

    def __str__(self) -> str:
        """返回 ``ErrorType(message)`` 形式的紧凑表示。"""
```

## 外部服务异常

### RemoteWorkerError

远端 Worker（如 Go Worker）执行失败时抛出。

```python
class RemoteWorkerError(CelestialFlowError):
    """远端 Worker 执行失败"""
    pass
```

### ReporterError

上报器错误。

```python
class ReporterError(CelestialFlowError):
    """上报器错误"""
    pass
```

### CelestialTreeConnectionError

CelestialTree 客户端连接失败。

```python
class CelestialTreeConnectionError(CelestialFlowError):
    def __init__(self, message: str = "CelestialTreeClient is not available"):
        ...
```

## 其他运行时异常

### CelestialFlowTimeoutError

超时错误（继承内置 `TimeoutError`）。

```python
class CelestialFlowTimeoutError(CelestialFlowError, TimeoutError):
    """超时错误"""
    pass
```

### UnconsumedError

标记未被消费的任务。

```python
class UnconsumedError(CelestialFlowError):
    """用于标记任务未消费的异常类"""
    pass
```

当 `TaskGraph._finalize_nodes()` 发现队列中有剩余任务时，会将其标记为 `UnconsumedError` 并通过 `fallback_inlet` / `FallbackSpout` 持久化到 sqlite 回退数据库。

### TaskFormatError

任务格式错误。

```python
class TaskFormatError(CelestialFlowError):
    """任务格式错误"""
    pass
```

### TerminationMergeError

终止信号合并错误（缺少上游终止信号时触发）。

```python
class TerminationMergeError(CelestialFlowError):
    """终止信号合并错误"""
    pass
```

## 使用场景

### 1. 添加可重试异常

```python
executor = TaskExecutor("Processor", process, max_retries=3)
executor.set_retry_exceptions(ConnectionError, TimeoutError)
```

### 2. 捕获配置错误

```python
from celestialflow.runtime.util_errors import ExecutionModeError

try:
    stage.set_execution_mode("invalid_mode")
except ExecutionModeError as e:
    print(f"无效的执行模式: {e.execution_mode}")
    print(f"有效选项: {e.valid_modes}")
```

### 3. 图结构验证

```python
from celestialflow.runtime.util_errors import DuplicateNodeError

try:
    graph.set_stages([stage_a, stage_a])  # 同名节点
except DuplicateNodeError as e:
    print(f"重复节点: {e}")
```

## 使用示例

以下示例展示 CelestialFlow 各类异常的 raise 和 catch 典型用法。

### 配置异常

```python
from celestialflow.runtime.util_errors import (
    ExecutionModeError,
    StageModeError,
    LogLevelError,
    ScheduleModeError,
    InvalidOptionError,
)

# 捕获 ExecutionModeError
try:
    stage.set_execution_mode("invalid")
except ExecutionModeError as e:
    print(f"字段: {e.field}")          # execution_mode
    print(f"传入值: {e.value}")        # invalid
    print(f"合法值: {e.allowed}")      # ('serial', 'thread', 'async')

# 捕获 StageModeError
try:
    stage.set_stage_mode("invalid")
except StageModeError as e:
    print(f"配置错误: {e}")

# 直接使用 InvalidOptionError
try:
    raise InvalidOptionError(
        field="strategy",
        value="aggressive",
        allowed=("conservative", "balanced"),
    )
except InvalidOptionError as e:
    print(f"错误: {e}")
```

### 图结构异常

```python
from celestialflow import TaskGraph, TaskStage
from celestialflow.runtime.util_errors import DuplicateNodeError, UnknownNodeError

graph = TaskGraph(name="ErrorTestGraph")

stage_a = TaskStage("A", func=lambda x: x)
stage_b = TaskStage("A", func=lambda x: x * 2)  # 同名节点

try:
    graph.set_stages([stage_a, stage_b])
except DuplicateNodeError as e:
    print(f"重复节点: {e}")

try:
    from celestialflow.runtime.util_types import TerminationSignal
    # UnknownNodeError 在 in_queue._record_termination 验证来源时触发
    from celestialflow.runtime import TaskInQueue
    from queue import Queue
    in_queue = TaskInQueue(queue=Queue(), source_names=["known"], out_name="test")
    in_queue._record_termination(TerminationSignal(source="unknown_source"))
except UnknownNodeError as e:
    print(f"未知来源: {e}")
```

### 运行时和超时异常

```python
from celestialflow.runtime.util_errors import (
    RuntimeStateError,
    CelestialFlowTimeoutError,
    UnconsumedError,
    TaskFormatError,
    TerminationMergeError,
)

# 超时错误（继承内置 TimeoutError）
try:
    raise CelestialFlowTimeoutError("Task execution timed out after 30s")
except CelestialFlowTimeoutError as e:
    print(f"超时: {e}")

# 任务格式错误
try:
    raise TaskFormatError("Malformed task input: expected structured payload, got str")
except TaskFormatError as e:
    print(f"格式错误: {e}")

# 终止信号合并错误
try:
    raise TerminationMergeError("Missing termination from source: B")
except TerminationMergeError as e:
    print(f"合并错误: {e}")
```

### 外部服务异常

```python
from celestialflow.runtime.util_errors import (
    RemoteWorkerError,
    CelestialTreeConnectionError,
)

try:
    raise RemoteWorkerError("Go worker returned status code 500")
except RemoteWorkerError as e:
    print(f"远端 Worker 错误: {e}")

try:
    raise CelestialTreeConnectionError("Cannot connect to 127.0.0.1:7777")
except CelestialTreeConnectionError as e:
    print(f"连接失败: {e}")
```

### 结合 TaskExecutor 使用

```python
from celestialflow import TaskExecutor
from celestialflow.runtime.util_errors import CelestialFlowError

# 在实际执行器中，异常被统一捕获并记录
executor = TaskExecutor(
    "SafeWorker",
    func=lambda x: 10 // x,
    execution_mode="serial",
    max_retries=0,
)
executor.start([1, 0, 2])  # 中间任务会触发 ZeroDivisionError

counts = executor.get_counts()
print(f"成功: {counts['tasks_succeeded']}, 失败: {counts['tasks_failed']}")
```

## 未消费任务的处理

`UnconsumedError` 主要用于标记任务未被正常消费的场景。在 `TaskGraph._finalize_nodes()` 收尾阶段，会调用每个 stage 的 `drain_task_queue()`：

1. 清空 stage 的任务队列，取出剩余任务。
2. 对每个剩余任务调用 `handle_task_fail(source, UnconsumedError())`。
3. 失败信息经 `fallback_inlet` 写入 `FallbackSpout`，最终持久化到按日期组织的 sqlite 回退数据库中。

因此，未消费任务的“持久化”并不是由 `util_errors.py` 自身完成，而是依赖 Stage / Graph 层的 fallback 机制。
