# TaskQueue

`TaskQueue` 模块提供了 `TaskInQueue` 和 `TaskOutQueue` 两个类，用于连接不同 Stage 的管道。它们支持多生产者、多消费者模型，并集成了日志记录和监控功能。

## 概述

- **TaskInQueue**: 任务输入队列，用于从上游接收任务
- **TaskOutQueue**: 任务输出队列，用于向下游发送任务

两者都支持多种后端：`queue.Queue` (Thread)、`multiprocessing.Queue` (Process)、`asyncio.Queue` (Async)。

---

## TaskInQueue

任务输入队列，用于接收和合并来自多个上游的任务。

### 初始化

```python
class TaskInQueue:
    def __init__(
        self,
        queue: ThreadQueue | MPQueue | AsyncQueue,
        queue_tags: List[str],
        out_tag: str,
        log_sinker: "LogSinker",
    ):
        """
        初始化任务入队。

        :param queue: 队列对象
        :param queue_tags: 上游队列标签列表
        :param out_tag: 当前节点标签
        :param log_sinker: 日志记录器
        """
```

### 主要方法

#### put / put_async

```python
def put(self, item: TaskEnvelope | TerminationSignal):
    """
    入队任务或终止信号。

    :param item: 要入队的任务或终止信号
    """

async def put_async(self, item: TaskEnvelope | TerminationSignal):
    """
    异步入队任务或终止信号。
    """
```

#### get / get_async

```python
def get(self) -> TaskEnvelope | TerminationIdPool:
    """
    出队任务或终止信号池。

    :return: 任务信封或终止信号 ID 池
    """

async def get_async(self) -> TaskEnvelope | TerminationIdPool:
    """
    异步出队任务或终止信号池。
    """
```

**终止信号合并逻辑**：
- 当收到来自 `"input"` 的终止信号时，立即返回
- 当收到来自当前节点标签（`out_tag`）的终止信号时，立即返回
- 当收到来自所有 `queue_tags` 的终止信号时，合并后返回

#### drain

```python
def drain(self) -> List[TaskEnvelope]:
    """
    清空队列中的所有任务，返回任务列表。
    记录终止信号状态，但不返回 TerminationIdPool。

    :return: 包含所有任务的列表
    """
```

### 辅助方法

```python
def add_source_tag(self, tag: str):
    """
    添加上游队列标签。

    :param tag: 上游队列标签
    :raises ValueError: 如果标签已存在
    """

def reset(self):
    """
    重置任务入队状态（清空终止信号记录）。
    """
```

---

## TaskOutQueue

任务输出队列，用于向多个下游发送任务。

### 初始化

```python
class TaskOutQueue:
    def __init__(
        self,
        queue_list: List[ThreadQueue] | List[MPQueue] | List[AsyncQueue],
        queue_tags: List[str],
        in_tag: str,
        log_sinker: "LogSinker",
    ):
        """
        初始化任务输出队列。

        :param queue_list: 输出队列列表
        :param queue_tags: 队列标签列表
        :param in_tag: 当前节点标签
        :param log_sinker: 日志记录器
        :raises ValueError: 如果队列列表和标签列表长度不一致
        """
```

### 主要方法

#### put / put_async

```python
def put(self, item: TaskEnvelope | TerminationSignal):
    """
    入队任务或终止信号到所有输出通道。
    """

async def put_async(self, item: TaskEnvelope | TerminationSignal):
    """
    异步入队任务或终止信号到所有输出通道。
    """
```

#### put_target

```python
def put_target(self, item: TaskEnvelope | TerminationSignal, tag: str):
    """
    入队任务或终止信号到指定标签的输出通道。

    :param item: 要入队的任务或终止信号
    :param tag: 输出队列标签
    """
```

常用于 `TaskRouter` 的定向分发。

#### put_channel / put_channel_async

```python
def put_channel(self, item: TaskEnvelope | TerminationSignal, idx: int):
    """
    入队任务或终止信号到指定索引的输出通道。

    :param item: 要入队的任务或终止信号
    :param idx: 输出通道索引
    """

async def put_channel_async(self, item: TaskEnvelope | TerminationSignal, idx: int):
    """
    异步入队任务或终止信号到指定索引的输出通道。
    """
```

### 辅助方法

```python
def add_queue(self, queue: ThreadQueue | MPQueue | AsyncQueue, tag: str):
    """
    添加一个输出队列到队列列表中。

    :param queue: 要添加的输出队列
    :param tag: 队列标签
    :raises ValueError: 如果标签已存在
    """
```

---

## 终止信号机制

### 信号流向

```
上游节点 ──TaskOutQueue──> 队列 ──TaskInQueue──> 当前节点
    │                              │
    └── TerminationSignal ──────> termination_dict
                                        │
                                        v
                               合并为 TerminationIdPool
```

### 合并规则

`TaskInQueue` 会等待来自所有 `queue_tags` 的终止信号，然后合并为一个 `TerminationIdPool`：

1. 收到终止信号时，记录到 `termination_dict`
2. 检查是否所有上游都已发送终止信号
3. 如果全部收到，合并为 `TerminationIdPool` 返回
4. 否则继续等待

特殊处理：
- `"input"` 标签的终止信号立即返回
- 当前节点标签（`out_tag`）的终止信号立即返回

---

## 使用示例

### 在 TaskGraph 中使用

```python
from celestialflow.runtime import TaskInQueue, TaskOutQueue
from multiprocessing import Queue as MPQueue

# 输入队列
in_queue = TaskInQueue(
    queue=MPQueue(),
    queue_tags=["upstream_stage"],
    out_tag="current_stage",
    log_sinker=log_sinker,
)

# 输出队列
out_queue = TaskOutQueue(
    queue_list=[MPQueue()],
    queue_tags=["downstream_stage"],
    in_tag="current_stage",
    log_sinker=log_sinker,
)
```

### 动态添加下游

```python
# 添加新的下游队列
out_queue.add_queue(new_queue, "new_downstream")
```

### 处理终止信号

```python
# 获取任务
item = in_queue.get()

if isinstance(item, TaskEnvelope):
    # 处理任务
    result = process(item.task)
    out_queue.put(TaskEnvelope.wrap(result, result_id))
elif isinstance(item, TerminationIdPool):
    # 所有上游都已终止，发送终止信号给下游
    out_queue.put(TerminationSignal())
```

---

## 注意事项

1. **多通道**: 一个 `TaskOutQueue` 可以管理多个下游队列
2. **日志记录**: 所有入队/出队操作都会记录日志
3. **异步支持**: 提供 `put_async`、`get_async` 等异步方法
4. **线程安全**: 内部使用队列实现，支持多线程/多进程访问
5. **终止合并**: 正确处理多上游的终止信号合并