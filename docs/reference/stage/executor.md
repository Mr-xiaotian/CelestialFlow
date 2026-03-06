# TaskExecutor

`TaskExecutor` 是执行单一任务逻辑的核心组件。它负责任务的执行、并发控制、错误处理、重试机制以及日志记录。

## 初始化

```python
class TaskExecutor:
    def __init__(
        self,
        func,
        execution_mode="serial",
        worker_limit=20,
        max_retries=1,
        max_info=50,
        unpack_task_args=False,
        enable_success_cache=False,
        enable_error_cache=False,
        enable_duplicate_check=True,
        show_progress=False,
        progress_desc="Executing",
        log_level="SUCCESS",
    ):
        ...
```

### 参数说明

- **func**: 实际执行任务的可调用对象（函数）。
- **execution_mode**: 执行模式。
  - `serial`: 串行执行。
  - `thread`: 多线程执行。
  - `process`: 多进程执行（注意：作为 `TaskGraph` 的一部分时通常不使用此模式，而是由 `TaskStage` 管理）。
  - `async`: 异步执行 (`asyncio`)。
- **worker_limit**: 并发数量限制（线程数/进程数/协程数）。
- **max_retries**: 任务失败后的最大重试次数。
- **unpack_task_args**: 是否将任务参数解包 (`*args`) 传给函数。
- **enable_success_cache**: 是否缓存成功结果。
- **enable_error_cache**: 是否缓存失败异常。
- **enable_duplicate_check**: 是否启用基于任务哈希的重复检查。
- **show_progress**: 是否显示进度条。

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

## 结果处理

- **process_result**: 可重写此方法以自定义结果处理逻辑。
- **get_args**: 可重写此方法以自定义参数提取逻辑。
