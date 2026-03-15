# TaskRunner

`TaskRunner` 是任务执行的核心运行器，负责从队列获取任务、执行任务、处理结果和错误。它支持串行、线程池、进程池和异步四种执行模式。

## 初始化

```python
class TaskRunner:
    def __init__(self, task_executor: TaskExecutor, worker_limit: int):
        """
        初始化任务运行器。

        :param task_executor: 任务执行器（TaskExecutor 实例）
        :param worker_limit: 工作线程或进程数量限制
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

### run_with_pool

使用线程池或进程池并行执行任务。

```python
def run_with_pool(self, execution_mode: str):
    """
    使用指定的执行池（线程池或进程池）来并行执行任务。

    :param execution_mode: 执行模式，"thread" 或 "process"
    """
```

执行流程：
1. 初始化线程池或进程池
2. 从队列获取任务并提交到池中
3. 使用回调函数处理任务完成事件
4. 使用 `in_flight` 计数器和 `Event` 同步
5. 等待所有任务完成后处理终止信号
6. 关闭池并释放资源

特点：
- 支持并发执行多个任务
- 自动管理并发数量（通过 `worker_limit`）
- 使用回调机制处理结果

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

特点：
- 适用于 I/O 密集型任务
- 使用 `asyncio.Semaphore` 控制并发
- 支持 `async/await` 语法

## 内部方法

### init_pool

```python
def init_pool(self, execution_mode):
    """
    初始化线程池或进程池。

    :param execution_mode: 执行模式，"thread" 或 "process"
    """
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
    """
    关闭线程池和进程池，释放资源。
    """
```

### _run_single_task

```python
async def _run_single_task(self, task):
    """
    运行单个任务并捕获异常。

    :param task: 要运行的任务
    :return: 任务的结果或异常
    """
```

## 使用示例

### 在 TaskExecutor 中使用

```python
# TaskExecutor 内部会创建 TaskRunner
executor = TaskExecutor(func=process, execution_mode="thread", worker_limit=4)
executor.start(task_source)  # 内部调用 runner.run_with_pool("thread")
```

### 直接使用（不推荐）

```python
from celestialflow.runtime import TaskRunner

runner = TaskRunner(task_executor, worker_limit=10)

# 串行执行
runner.run_in_serial()

# 线程池执行
runner.run_with_pool("thread")

# 进程池执行
runner.run_with_pool("process")

# 异步执行
await runner.run_in_async()
```

## 与 TaskExecutor 的关系

`TaskRunner` 是 `TaskExecutor` 的内部组件：

```
TaskExecutor
    ├── func               # 任务函数
    ├── task_queues        # 输入队列（TaskInQueue）
    ├── result_queues      # 输出队列（TaskOutQueue）
    ├── metrics            # 任务指标
    └── runner             # TaskRunner 实例
            ├── run_in_serial()
            ├── run_with_pool()
            └── run_in_async()
```

`TaskExecutor` 根据 `execution_mode` 选择调用 `TaskRunner` 的哪个方法：
- `serial` → `run_in_serial()`
- `thread` → `run_with_pool("thread")`
- `process` → `run_with_pool("process")`
- `async` → `run_in_async()`

## 注意事项

1. **并发控制**: `worker_limit` 限制并发任务数量，防止资源耗尽
2. **池复用**: 线程池/进程池可以复用，避免频繁创建销毁
3. **终止处理**: 正确处理终止信号的合并和传递
4. **错误传播**: 异常会被捕获并传递给 `TaskExecutor.handle_task_error()`
5. **异步限制**: `run_in_async` 需要任务函数是协程函数