# TaskExecutor

> 📅 最后更新日期: 2026/05/15

`TaskExecutor` 是执行单一任务逻辑的核心组件。它负责任务的执行、并发控制、错误处理、重试机制以及日志记录。

## 初始化

```python
class TaskExecutor:
    def __init__(
        self,
        name,
        func,
        execution_mode="serial",
        max_workers=20,
        max_retries=1,
        max_info=50,
        unpack_task_args=False,
        enable_duplicate_check=True,
        log_level="INFO",
    ):
        ...
```

### 参数说明

- **name**: 执行器名称，用于日志和追踪。
- **func**: 实际执行任务的可调用对象（函数）。
- **execution_mode**: 执行模式。
  - `serial`: 串行执行。
  - `thread`: 多线程执行。
  - `async`: 异步执行 (`asyncio`)。
- **max_workers**: 并发数量限制（线程数/协程数）。
- **max_retries**: 任务失败后的最大重试次数。
- **max_info**: 日志中每条信息的最大长度。
- **unpack_task_args**: 是否将任务参数解包 (`*args`) 传给函数。
- **enable_duplicate_check**: 是否启用基于任务哈希的重复检查。
- **log_level**: 日志级别（TRACE/DEBUG/SUCCESS/INFO/WARNING/ERROR/CRITICAL）。

## Observer 模式

`TaskExecutor` 通过 observer 模式向外部广播生命周期事件。

### 注册与移除

```python
executor.add_observer(observer)     # 注册观察者
executor.remove_observer(observer)  # 移除观察者
```

### 使用示例

```python
from celestialflow import TaskExecutor, TaskProgress, CallbackObserver

# 使用 TaskProgress 显示进度条
executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)

# 使用 CallbackObserver
observer = CallbackObserver(
    on_task_success=lambda count=1: print(f"成功: {count}"),
)
executor.add_observer(observer)
```

### 广播事件

| 事件 | 触发时机 |
|------|----------|
| `on_start(name, total)` | 执行开始 |
| `on_task_success(count)` | 任务成功 |
| `on_task_fail(count)` | 任务失败 |
| `on_task_duplicate(count)` | 检测到重复 |
| `on_tasks_added(count)` | 新任务加入 |
| `on_finish()` | 执行结束 |

## 核心方法

### start

```python
def start(self, task_source: Iterable):
    """
    启动执行器，处理 task_source 中的所有任务。
    会根据 execution_mode 选择相应的运行策略。
    """
```

### start_async

```python
async def start_async(self, task_source: Iterable):
    """
    异步启动执行器（用于 async 模式）。
    """
```

## 错误处理

`TaskExecutor` 会捕获任务执行中的异常：
- 如果异常在 `retry_exceptions` 列表中且未达到最大重试次数，会将任务重新放入队列重试。
- 否则，将任务标记为失败，记录错误日志，并放入 `fail_queue`。

### add_retry_exceptions

```python
def add_retry_exceptions(self, *exceptions):
    """
    添加需要重试的异常类型。

    :param exceptions: 异常类型列表
    """
```

示例：
```python
executor = TaskExecutor("Processor", process, max_retries=3)
executor.add_retry_exceptions(ValueError, ConnectionError, TimeoutError)
```

## 结果处理

### 可重写方法

- **process_result(task, result)**: 可重写此方法以自定义结果处理逻辑。
- **get_args(task)**: 可重写此方法以自定义参数提取逻辑。

### 获取结果

```python
# 获取成功结果列表
def get_success_pairs(self) -> list[tuple[Any, Any]]:
    ...

# 获取失败结果列表
def get_error_pairs(self) -> list[tuple[Any, Exception]]:
    ...
```

### 处理结果字典

```python
# 处理结果字典（合并成功和失败）
def process_result_dict(self) -> dict:
    ...

# 处理错误字典（按错误类型分组）
def handle_error_dict(self) -> dict:
    ...
```

## CelestialTree 集成

`TaskExecutor` 支持 CelestialTree 事件追踪系统，用于任务追踪和调试。

### set_ctree

```python
def set_ctree(self, host: str = "127.0.0.1", http_port: int = 7777, grpc_port: int = 7778):
    """
    设置 CelestialTree 客户端连接。

    :param host: CelestialTree 服务主机地址
    :param http_port: HTTP 端口
    :param grpc_port: gRPC 端口
    """
```

### set_nullctree

```python
def set_nullctree(self, event_id=None):
    """
    设置空客户端（不连接外部服务，仅生成事件 ID）。

    :param event_id: 可选的事件 ID
    """
```

## 状态查询方法

### 获取基本信息

```python
# 获取执行器名称
def get_name(self) -> str: ...

# 获取函数名
def get_func_name(self) -> str: ...

# 获取类名（私有）
def _get_class_name(self) -> str: ...

# 获取标签（用于日志和追踪）
def get_tag(self) -> str: ...

# 获取执行模式描述（私有）
def _get_execution_mode_desc(self) -> str: ...
```

### 获取状态快照

```python
def get_summary(self) -> dict:
    """
    获取当前节点的状态快照。
    返回：name, func_name, class_name, execution_mode
    """

def get_counts(self) -> dict:
    """
    获取当前节点的计数器。
    返回：tasks_input, tasks_succeeded, tasks_failed, tasks_duplicated, tasks_processed, tasks_pending
    """
```

## 运行时信息

### get_task_repr

```python
def get_task_repr(self, task) -> str:
    """
    获取任务参数的可读字符串表示。
    用于日志输出，会自动截断过长的参数。
    """
```

### _get_result_repr

```python
def _get_result_repr(self, result) -> str:
    """
    获取结果的可读字符串表示。
    """
```

## 注意事项

### 执行模式选择

| 模式 | 适用场景 | 注意事项 |
|------|----------|----------|
| `serial` | 调试、简单任务 | 无并发 |
| `thread` | I/O 密集型 | 注意 GIL 限制 |
| `async` | 网络 I/O | 需要使用 start_async |
