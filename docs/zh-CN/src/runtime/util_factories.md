# RuntimeFactories

> 📅 最后更新日期: 2026/05/24

`runtime/util_factories.py` 提供运行时队列对象的工厂函数，用于创建 `TaskInQueue` 和 `TaskOutQueue` 实例。

## 主要函数

### make_task_in_queue

创建任务输入队列实例。

```python
def make_task_in_queue(
    *,
    queue: Any,
    executor: "TaskExecutor",
) -> TaskInQueue:
    """
    构造 TaskInQueue 实例。

    :param queue: 队列实例
    :param executor: 任务执行器
    :return: TaskInQueue 实例
    """
```

内部实现：
```python
return TaskInQueue(
    queue=queue,
    source_names=[],
    out_name=executor.get_name(),
    log_inlet=executor.log_inlet,
)
```

### make_task_out_queue

创建任务输出队列实例。

```python
def make_task_out_queue(
    *,
    queue: Any,
    executor: "TaskExecutor",
) -> TaskOutQueue:
    """
    构造 TaskOutQueue 实例。

    :param queue: 队列实例
    :param executor: 任务执行器
    :return: TaskOutQueue 实例
    """
```

内部实现：
```python
return TaskOutQueue(
    queue_list=[queue],
    target_names=[None],
    in_name=executor.get_name(),
    log_inlet=executor.log_inlet,
)
```

## 使用示例

以下示例展示工厂函数的实际使用方式，包括创建执行器后为其构建输入/输出队列。

```python
from queue import Queue as ThreadQueue
from celestialflow import TaskExecutor
from celestialflow.runtime.util_factories import make_task_in_queue, make_task_out_queue

# 1. 创建 TaskExecutor 实例
def process(x: int) -> int:
    return x * 10

executor = TaskExecutor(
    name="Processor",
    func=process,
    execution_mode="serial",
)

# 手动初始化环境（让 executor 拥有 log_inlet）
executor.init_env()

# 2. 使用 make_task_in_queue 创建输入队列
in_queue = make_task_in_queue(
    queue=ThreadQueue(),
    executor=executor,
)
print(f"输入队列所属节点: {in_queue.out_name}")  # "Processor"
print(f"上游来源列表: {in_queue.source_names}")   # []（初始为空）

# 动态添加上游
in_queue.add_source_name("StageA")
print(f"添加上游后: {in_queue.source_names}")     # ["StageA"]

# 3. 使用 make_task_out_queue 创建输出队列
out_queue = make_task_out_queue(
    queue=ThreadQueue(),
    executor=executor,
)
print(f"输出队列所属节点: {out_queue.in_name}")    # "Processor"
print(f"目标节点列表: {out_queue.target_names}")   # [None]（初始为 None）

# 动态添加更多下游
out_queue.add_queue(ThreadQueue(), "StageB")
print(f"添加下游后通道数: {len(out_queue.queue_list)}")  # 2

# 4. 实际使用：生产任务并消费
from celestialflow.runtime import TaskEnvelope

# 生产
env = TaskEnvelope(task=42, id=1, source="StageA")
in_queue.put(env)

# 消费
retrieved = in_queue.get()
print(f"出队任务: {retrieved.get_task()}")  # 42

# 广播到所有下游
out_queue.put(retrieved)
```

### 配合 TaskExecutor 的 init_queue 方法

`TaskExecutor` 内部已使用工厂函数创建默认队列：

```python
from celestialflow import TaskExecutor

# 调用 init_env() 时自动调用 make_task_in_queue 和 make_task_out_queue
executor = TaskExecutor(name="Demo", func=lambda x: x)
executor.init_env()

print(f"task_queue 类型: {type(executor.task_queue).__name__}")    # TaskInQueue
print(f"result_queue 类型: {type(executor.result_queue).__name__}")  # TaskOutQueue
```

## 注意事项

1. **执行器依赖**: 两个工厂函数都需要 `TaskExecutor` 实例来获取节点名称（`get_name()`）和日志记录器（`log_inlet`）。
2. **source_names 初始为空**: `make_task_in_queue` 创建的队列上游列表为空，后续通过 `add_source_name()` 动态添加。
3. **queue_list 初始为单元素**: `make_task_out_queue` 创建的输出队列列表初始仅包含传入的队列，后续通过 `add_queue()` 动态扩展。
