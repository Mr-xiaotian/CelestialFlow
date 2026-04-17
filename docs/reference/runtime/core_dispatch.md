# TaskDispatch

`TaskDispatch` 是任务执行的核心运行器，负责从队列获取任务、执行任务、处理结果和错误。它支持串行、线程池和异步三种执行模式。

## 初始化

```python
class TaskDispatch:
    def __init__(self, task_executor: TaskExecutor, func, max_workers: int):
        """
        初始化任务运行器。

        :param task_executor: 任务执行器（TaskExecutor 实例）
        :param func: 任务函数
        :param max_workers: 工作线程或进程数量限制
        """
```

## 执行模式

### run_in_serial

串行执行任务，一个接一个处理。

```python
def run_in_serial(self):
    """
    串行地执行任务。

    从 task_queues 获取任务，依次执行，直到收到终止信号且所有任务完成。
    """
```

执行流程：
1. 从 `task_queues.get()` 获取任务
2. 检查是否为终止信号（`TerminationIdPool`）
3. 检查任务是否重复
4. 执行任务并处理结果或错误
5. 更新进度条
6. 收到终止信号后，检查是否所有任务完成

### run_in_thread

使用线程池并行执行任务。

```python
def run_in_thread(self):
    """
    使用线程池并行执行任务。
    """
```

执行流程：
1. 初始化线程池
2. 从队列获取任务并提交到池中
3. 等待所有 future 完成后处理终止信号
4. 关闭池并释放资源

### run_in_async

异步执行任务，使用协程和信号量控制并发。

```python
async def run_in_async(self):
    """
    异步地执行任务，限制并发数量。
    """
```

执行流程：
1. 创建信号量限制并发数量
2. 异步获取任务
3. 使用 `asyncio.gather` 并发执行任务
4. 处理结果和错误
5. 检查终止条件

## 内部方法

### _worker / _async_worker

```python
def _worker(self, envelope: TaskEnvelope):
    """线程池中的工作函数，执行单个任务并处理重试。"""

async def _async_worker(self, envelope: TaskEnvelope):
    """异步工作函数，执行单个任务并处理重试。"""
```

### process_termination_signal

```python
def process_termination_signal(self, termination_pool: TerminationIdPool) -> TerminationSignal:
    """
    处理终止信号，生成 merge 事件。

    :param termination_pool: 包含多个终止信号 ID 的池
    :return: 合并后的终止信号
    """
```

### release_pool

```python
def release_pool(self):
    """关闭线程池，释放资源。"""
```

## 与 TaskExecutor 的关系

`TaskDispatch` 是 `TaskExecutor` 的内部组件：

```
TaskExecutor
    ├── func               # 任务函数
    ├── task_queues        # 输入队列（TaskInQueue）
    ├── result_queues      # 输出队列（TaskOutQueue）
    ├── metrics            # 任务指标
    └── dispatch           # TaskDispatch 实例
            ├── func               # 任务函数
            ├── max_workers        # 并发数量限制
            ├── run_in_serial()
            ├── run_in_thread()
            └── run_in_async()
```

`TaskExecutor` 根据 `execution_mode` 选择调用 `TaskDispatch` 的哪个方法：
- `serial` → `run_in_serial()`
- `thread` → `run_in_thread()`
- `async` → `run_in_async()`

## 注意事项

1. **并发控制**: `max_workers` 限制并发任务数量，防止资源耗尽
2. **终止处理**: 正确处理终止信号的合并和传递
3. **错误传播**: 异常会被捕获并传递给 `TaskExecutor.handle_task_fail()`
4. **重试机制**: worker 内部支持任务重试，由 `max_retries` 控制
5. **异步限制**: `run_in_async` 需要任务函数是协程函数
