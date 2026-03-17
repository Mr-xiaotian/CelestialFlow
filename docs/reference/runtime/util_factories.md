# RuntimeFactories

`runtime/factories.py` 提供运行时对象的工厂函数，用于根据执行模式创建相应的队列、计数器等对象。

## 设计目标

- 统一 serial/thread/process/async 的底层资源创建逻辑
- 封装不同模式的实现差异
- 简化上层代码的条件判断

---

## 主要函数

### make_counter

创建计数器，根据执行模式选择合适的实现。

```python
def make_counter(
    mode: str, *, lock: LockType | None = None, init: int = 0
) -> ValueWrapper:
    """
    返回一个计数器。

    :param mode: 执行模式 ('serial', 'thread', 'process', 'async')
    :param lock: 可选的锁对象（thread 模式使用）
    :param init: 初始值
    :return: ValueWrapper 或 MPValue
    """
```

返回类型：
- `process` 模式：`MPValue("i", init)`
- `thread` 模式：`ValueWrapper(init, lock=lock or Lock())`
- `serial`/`async` 模式：`ValueWrapper(init)`

### make_queue_backend

返回队列类/构造器，用于创建单通道队列。

```python
def make_queue_backend(mode: str):
    """
    返回一个队列类。

    :param mode: 执行模式
    :return: 队列类
    """
```

返回类型：
- `async` 模式：`AsyncQueue`
- `thread`/`serial`/`process` 模式：`ThreadQueue`

> 注意：`process` 模式也使用 `ThreadQueue`，因为队列在节点内部使用，不跨进程。

### make_task_in_queue

创建任务输入队列实例。

```python
def make_task_in_queue(
    *,
    mode: str,
    executor: "TaskExecutor",
) -> TaskInQueue:
    """
    构造 TaskInQueue 实例。

    :param mode: 执行模式
    :param executor: 任务执行器
    :return: TaskInQueue 实例
    """
```

内部实现：
```python
Q = make_queue_backend(mode)
return TaskInQueue(
    queue=Q(),
    queue_tags=[],
    out_tag=executor.get_tag(),
    log_sinker=executor.log_sinker,
)
```

### make_task_out_queue

创建任务输出队列实例。

```python
def make_task_out_queue(
    *,
    mode: str,
    executor: "TaskExecutor",
) -> TaskOutQueue:
    """
    构造 TaskOutQueue 实例。

    :param mode: 执行模式
    :param executor: 任务执行器
    :return: TaskOutQueue 实例
    """
```

内部实现：
```python
Q = make_queue_backend(mode)
return TaskOutQueue(
    queue_list=[Q()],
    queue_tags=[None],
    in_tag=executor.get_tag(),
    log_sinker=executor.log_sinker,
)
```

---

## 使用示例

### 在 TaskExecutor 中使用

```python
from celestialflow.runtime.util_factories import (
    make_counter,
    make_queue_backend,
    make_task_in_queue,
    make_task_out_queue,
)

# 创建计数器
counter = make_counter("thread", init=0)

# 创建队列后端
QueueClass = make_queue_backend("async")
queue = QueueClass()

# 创建任务输入队列
in_queue = make_task_in_queue(mode="thread", executor=executor)

# 创建任务输出队列
out_queue = make_task_out_queue(mode="thread", executor=executor)
```

### 直接创建队列

```python
# 获取队列类
ThreadQueue = make_queue_backend("thread")
AsyncQueue = make_queue_backend("async")

# 创建实例
sync_queue = ThreadQueue()
async_queue = AsyncQueue()
```

---

## 模式对照表

| 模式 | 计数器 | 队列后端 |
|------|--------|----------|
| `serial` | `ValueWrapper` | `ThreadQueue` |
| `thread` | `ValueWrapper` + Lock | `ThreadQueue` |
| `process` | `MPValue` | `ThreadQueue` |
| `async` | `ValueWrapper` | `AsyncQueue` |

---

## 注意事项

1. **进程模式队列**: 当前实现中 `process` 模式使用 `ThreadQueue`，因为队列在节点内部使用。如果需要跨进程通信，应改为 `MPQueue`。

2. **锁传递**: `make_counter` 的 `lock` 参数用于 thread 模式下复用锁对象。

3. **执行器依赖**: `make_task_in_queue` 和 `make_task_out_queue` 需要 `TaskExecutor` 实例来获取标签和日志记录器。