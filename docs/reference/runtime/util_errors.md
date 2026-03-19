# TaskErrors

TaskErrors 模块定义了框架中使用的自定义异常类。

## 异常层级

```
CelestialFlowError
├── ConfigurationError
│   └── InvalidOptionError
│       ├── ExecutionModeError
│       ├── StageModeError
│       └── LogLevelError
├── RemoteWorkerError
├── UnconsumedError
└── PickleError
```

## 基类

### CelestialFlowError

所有自定义异常的基类。

```python
class CelestialFlowError(Exception):
    """CelestialFlow 所有自定义异常的基类"""
    pass
```

## 配置相关异常

### ConfigurationError

配置错误基类（参数非法、组合不支持等）。

```python
class ConfigurationError(CelestialFlowError):
    """配置错误基类"""
    pass
```

### InvalidOptionError

某个配置项的取值不合法（不在允许集合里）。

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
        :param value: 实际值
        :param allowed: 允许的值列表
        :param prefix: 错误消息前缀
        """
```

### ExecutionModeError

`execution_mode` 配置错误。

```python
class ExecutionModeError(InvalidOptionError):
    """非法的 execution_mode 配置错误"""

    def __init__(self, execution_mode: str, valid_modes=None):
        # valid_modes 默认为 ("serial", "process", "thread", "async")
```

### StageModeError

`stage_mode` 配置错误。

```python
class StageModeError(InvalidOptionError):
    """非法的 stage_mode 配置错误"""

    def __init__(self, stage_mode: str, valid_modes=None):
        # valid_modes 默认为 ("serial", "process")
```

### LogLevelError

`log_level` 配置错误。

```python
class LogLevelError(InvalidOptionError):
    """非法的 log_level 配置错误"""

    def __init__(self, log_level: str, valid_levels=None):
        # valid_levels 默认为 ("TRACE", "DEBUG", "SUCCESS", "INFO", "WARNING", "ERROR", "CRITICAL")
```

## 运行时异常

### RemoteWorkerError

远程 Worker（如 Go Worker）执行失败时抛出的异常。

```python
class RemoteWorkerError(CelestialFlowError):
    pass
```

### UnconsumedError

标记任务未被消费的异常类。

```python
class UnconsumedError(CelestialFlowError):
    """用于标记任务未消费的异常类"""
    pass
```

当 `TaskGraph` 停止时，会收集所有未消费的任务并记录为 `UnconsumedError`。

### PickleError

任务函数或参数无法 pickle 序列化的错误。

```python
class PickleError(CelestialFlowError):
    """
    任务函数或参数无法 pickle 序列化的错误。
    """

    def __init__(self, obj: Any):
        message = f"Object of type {type(obj).__name__} is not pickleable."
        super().__init__(message)
        self.obj = obj
        self.type = type(obj).__name__
        self.message = message
```

在 `TaskStage.set_func()` 中，会检查函数是否可 pickle：

```python
from celestialflow.runtime.util_errors import PickleError
from celestialflow.utils.util_debug import find_unpickleable

if find_unpickleable(func):
    raise PickleError(func)
```

## 错误处理策略

在 `TaskExecutor` 中，异常被分为两类：

1. **可重试异常**: 如果异常类型在 `retry_exceptions` 列表中，且重试次数未达上限，框架会自动重试该任务。
2. **不可重试异常**: 任务会被标记为失败，记录错误日志，并放入 `fail_queue`。

## 错误持久化

`TaskGraph` 会自动将所有未处理的错误（包括重试失败和 UnconsumedError）持久化到本地的 `fallback/` 目录下，格式为 JSONL。

每个错误记录包含：
- 时间戳
- 阶段标签
- 错误信息
- 原始任务数据
- 错误 ID

## 使用示例

### 捕获特定异常

```python
from celestialflow.runtime.util_errors import (
    ExecutionModeError,
    StageModeError,
    RemoteWorkerError,
    PickleError,
)

try:
    stage.set_execution_mode("invalid_mode")
except ExecutionModeError as e:
    print(f"无效的执行模式: {e.execution_mode}")
    print(f"有效选项: {e.valid_modes}")
```

### 添加可重试异常

```python
executor = TaskExecutor(func=process, max_retries=3)
executor.add_retry_exceptions(ConnectionError, TimeoutError)
```

## 注意事项

1. **Pickle 检查**: 在 process 模式下，确保所有函数和参数可 pickle
2. **错误传播**: `RemoteWorkerError` 包含远程 Worker 返回的错误信息
3. **日志记录**: 所有异常都会被记录到日志中
4. **优雅降级**: 即使发生异常，框架也会尝试正确清理资源