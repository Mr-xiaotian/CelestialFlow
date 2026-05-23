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

## 注意事项

1. **执行器依赖**: 两个工厂函数都需要 `TaskExecutor` 实例来获取节点名称（`get_name()`）和日志记录器（`log_inlet`）。
2. **source_names 初始为空**: `make_task_in_queue` 创建的队列上游列表为空，后续通过 `add_source_name()` 动态添加。
3. **queue_list 初始为单元素**: `make_task_out_queue` 创建的输出队列列表初始仅包含传入的队列，后续通过 `add_queue()` 动态扩展。
