# TaskQueue

> 📅 最后更新日期: 2026/05/24

`TaskQueue` 模块提供了 `TaskInQueue` 和 `TaskOutQueue` 两个类，用于连接不同 Stage 的管道。它们支持多生产者、多消费者模型，并集成了日志记录和终止信号合并功能。

## 概述

- **TaskInQueue**: 任务输入队列，聚合多个上游来源的任务和终止信号
- **TaskOutQueue**: 任务输出队列，将结果广播到一个或多个下游队列通道

两者都支持多种队列后端：`queue.Queue`（Thread）、`asyncio.Queue`（Async）。

---

## TaskInQueue

任务输入队列，用于接收、去重和合并来自多个上游的任务。

### 初始化

```python
class TaskInQueue:
    def __init__(
        self,
        queue: Any,
        source_names: list[str],
        out_name: str,
        log_inlet: "LogInlet",
    ):
        """
        :param queue: 队列对象
        :param source_names: 上游节点名称列表
        :param out_name: 当前节点唯一名称
        :param log_inlet: 日志记录器
        """
```

### 主要方法

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal) -> None:
    """
    入队任务或终止信号。记录入队日志。
    """
```

#### get

```python
def get(self) -> TaskEnvelope | TerminationIdPool:
    """
    出队任务或终止信号 ID 池。

    终止信号合并逻辑：
    - 收到来自 "input" 的终止信号 → 立即返回 TerminationIdPool
    - 收到来自所有 source_names 的终止信号 → 合并后返回
    - 仅收到部分上游信号 → 继续等待（返回 None，内部循环重试）
    """
```

#### drain

```python
def drain(self) -> list[TaskEnvelope]:
    """
    清空队列中的所有任务，返回任务列表。
    记录终止信号但不会返回 TerminationIdPool（仅用于同步环境，如 _finalize_nodes）。
    """
```

### 辅助方法

```python
def add_source_name(self, name: str) -> None:
    """
    动态添加上游来源名称。

    :param name: 上游节点名称
    :raises DuplicateNodeError: 如果名称已存在
    """
```

## TaskOutQueue

任务输出队列，用于向多个下游广播任务。

### 初始化

```python
class TaskOutQueue:
    def __init__(
        self,
        queue_list: list[Any],
        target_names: list[str | None],
        in_name: str,
        log_inlet: "LogInlet",
    ):
        """
        :param queue_list: 输出队列列表
        :param target_names: 下游节点名称列表（长度须与 queue_list 一致）
        :param in_name: 当前节点唯一名称
        :param log_inlet: 日志记录器
        :raises ConfigurationError: 如果两个列表长度不一致
        """
```

### 主要方法

#### put

```python
def put(self, item: TaskEnvelope | TerminationSignal) -> None:
    """入队任务或终止信号到所有输出通道。"""
```

#### put_target

```python
def put_target(self, item: TaskEnvelope | TerminationSignal, name: str) -> None:
    """
    入队到指定名称的输出通道。

    :param name: 下游 Stage 名称
    """
```

用于向指定下游 Stage 定向分发。

#### put_channel

```python
def put_channel(self, item: TaskEnvelope | TerminationSignal, idx: int) -> None:
    """
    入队到指定索引的输出通道。

    :param idx: 输出通道索引
    """
```

### 辅助方法

```python
def add_queue(self, queue: Any, name: str) -> None:
    """
    动态添加输出队列。

    :param queue: 队列实例
    :param name: 目标节点名称
    :raises DuplicateNodeError: 如果名称已存在
    """
```

---

## 终止信号机制

### 信号流向

```
上游节点 → out_queue.put(TerminationSignal) → 队列
                                                    ↓
                                            in_queue.get()
                                                    ↓
                                        termination_dict[source] = id
                                                    ↓
                                        所有 source 集齐？→ 是 → merge → TerminationIdPool
                                        输入直接终止？    → 是 → 立即返回
                                        否则              → 继续等待
```

### 合并规则

`TaskInQueue` 等待来自所有 `source_names` 的终止信号，合为一个 `TerminationIdPool`：

1. 在 `_record_termination` 中验证 source 合法性（须在 `source_names ∪ {"input"}` 中）
2. 若 `"input"` 存在 → 立即返回 `TerminationIdPool(ids=[...])`
3. 若 `_can_merge_termination()` 为 True → 调用 `_merge_termination()`
4. 否则继续等待（`_deal_get_item` 返回 `None`，外层 `get` 循环继续）

---

## 注意事项

1. **多通道**: `TaskOutQueue` 管理多个下游队列
2. **日志记录**: 所有 put/get 操作记录日志；异常时记录 `put_item_error`
3. **来源管理**: `add_source_name` 和 `add_queue` 均防重（`DuplicateNodeError`）
4. **终止合并**: `_merge_termination` 会检查是否遗漏 source，遗漏则抛 `TerminationMergeError`
5. **drain 特性**: 仅在同步环境（`_finalize_nodes`）中使用，用于收集未消费任务
