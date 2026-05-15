# RuntimeFactories

> 📅 最后更新日期: 2026/05/15

`runtime/util_factories.py` 提供运行时对象的工厂函数，用于创建相应的队列对象。

## 设计目标

- 封装队列创建逻辑
- 简化上层代码的条件判断

---

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
    queue_tags=[],
    out_tag=executor.get_tag(),
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
    queue_tags=[None],
    in_tag=executor.get_tag(),
    log_inlet=executor.log_inlet,
)
```

---

## 使用示例

### 在 TaskExecutor 中使用

```python
from celestialflow.runtime.util_factories import (
    make_task_in_queue,
    make_task_out_queue,
)

# 创建任务输入队列
in_queue = make_task_in_queue(queue=queue, executor=executor)

# 创建任务输出队列
out_queue = make_task_out_queue(queue=queue, executor=executor)
```

---

## 注意事项

1. **执行器依赖**: `make_task_in_queue` 和 `make_task_out_queue` 需要 `TaskExecutor` 实例来获取标签和日志记录器。