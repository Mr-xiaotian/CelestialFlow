# TaskQueue

`TaskQueue` 是连接不同 Stage 的管道，支持多生产者、多消费者模型，并集成了日志记录和监控功能。

## 核心功能

- **多后端支持**: 支持 `queue.Queue` (Thread), `multiprocessing.Queue` (Process), `asyncio.Queue` (Async)。
- **多通道**: 一个 `TaskQueue` 实例可以管理多个底层队列（Channels），用于支持复杂的拓扑结构（如 Router 分发）。
- **终止信号传递**: 自动处理 `TerminationSignal`，当所有上游队列都发送了终止信号后，才向下游传递终止信号。
- **日志与监控**: 记录入队/出队操作，通过 `TaskLogger` 上报。

## 初始化

```python
class TaskQueue:
    def __init__(
        self,
        queue_list: List[Queue],
        queue_tags: List[str],
        direction: str,  # "in" or "out"
        stage: TaskStage,
        task_logger: TaskLogger,
        ctree_client: CelestialTreeClient,
    ):
        ...
```

## 主要方法

### put / put_async

将项目放入所有管理的队列中。

```python
def put(self, item: TaskEnvelope | TerminationSignal): ...
async def put_async(self, item: TaskEnvelope | TerminationSignal): ...
```

### put_first / put_first_async

仅将项目放入第一个队列。常用于重试任务（优先处理）。

### put_target / put_target_async

将项目放入指定标签（Tag）的队列。常用于 `TaskRouter` 的定向分发。

### get / get_async

从管理的多个队列中轮询获取任务。

- 自动处理 `TerminationSignal` 的合并逻辑。
- 支持轮询策略，避免某些队列饥饿。

```python
def get(self, poll_interval: float = 0.01) -> TaskEnvelope | TerminationSignal: ...
```

### drain

非阻塞地提取所有队列中当前剩余的所有项目。
