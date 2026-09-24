# src/celestialflow/runtime/core_queue.py

> 📅 最后更新日期: 2026/09/24

`core_queue.py` 提供了 `TaskInQueue` 和 `TaskOutQueue` 两个类，用于连接任务图中不同节点的管道。它们支持多生产者、多消费者模型，并集成了终止信号合并功能。

## 概述

- **TaskInQueue**: 任务输入队列，聚合多个上游来源的任务并合并终止信号
- **TaskOutQueue**: 任务输出队列，将结果广播到一个或多个下游队列通道

两者都在内部使用 `queue.Queue`（线程安全队列）作为默认后端。

---

## TaskInQueue

任务输入队列，用于接收来自多个上游的任务并合并终止信号。

### 初始化

```python
class TaskInQueue[T]:
    def __init__(
        self,
        out_name: str,
        maxsize: int = 0,
    ) -> None:
        """
        :param out_name: 当前节点唯一名称
        :param maxsize: 队列最大容量，默认为 0（无限制）
        """
```

内部属性：

| 属性 | 类型 | 说明 |
|------|------|------|
| `out_name` | `str` | 当前节点唯一名称 |
| `queue` | `Queue[TaskEnvelope[T] \| TerminationSignal]` | 底层线程安全队列 |
| `source_names` | `list[str]` | 上游来源名称列表 |
| `termination_dict` | `dict[str, int]` | 已记录的终止信号来源 → ID |

队列在内部自动创建，无需外部传入。上游来源通过 `add_source_name()` 动态添加。

### 主要方法

#### put

```python
def put(self, item: TaskEnvelope[T] | TerminationSignal) -> None:
    """入队任务或终止信号。"""
```

#### get

```python
def get(self) -> TaskEnvelope[T] | TerminationIdPool:
    """
    出队任务或终止符号 id 池。
    """
```

`get()` 内部循环消费底层队列，直到 `_process_item()` 返回非 `None`。

终止信号合并逻辑：

- 收到来自 `"input"` 的终止信号 → 立即返回 `TerminationIdPool(ids=[...])`
- 收到来自所有 `source_names` 的终止信号 → 合并后返回
- 仅收到部分上游信号 → 继续等待（`_process_item` 返回 `None`，外层循环继续）
- 收到 `TerminationIdPool` 本身（上游已合并的池）→ 直接返回，不再经上游汇合逻辑

#### drain

```python
def drain(self) -> list[TaskEnvelope[T]]:
    """
    清空队列中的所有任务，返回任务列表。
    记录终止信号但不会返回 TerminationIdPool（仅用于同步环境，如 _finish_start）。
    """
```

### 辅助方法

```python
def add_source_name(self, name: str) -> None:
    """
    添加入队来源名称。

    :param name: 入队来源名称
    :raises DuplicateNodeError: 如果名称已存在
    """
```

内部终止处理辅助方法：

```python
def _record_termination(self, signal: TerminationSignal) -> None:
    """记录入队来源的终止信号；来源不在 source_names ∪ {"input"} 时抛 UnknownNodeError。"""


def _can_merge_termination(self) -> bool:
    """所有 source_names 都已发出终止信号时返回 True。"""


def _merge_termination(self) -> TerminationIdPool:
    """合并所有 source_names 的终止信号；存在遗漏来源时抛 TerminationMergeError。"""
```

> `_merge_termination()` 只合并来自 `source_names` 的终止信号，不处理 `"input"` 注入的直接终止，也不处理 `self.out_name` 的合并后终止。

## TaskOutQueue

任务输出队列，用于向多个下游广播任务。

### 初始化

```python
class TaskOutQueue[T]:
    def __init__(
        self,
        in_name: str,
    ) -> None:
        """
        :param in_name: 当前节点唯一名称，用于记录日志
        """
```

输出队列字典 `_queues` 初始为空，通过 `add_queue()` 动态添加下游通道。

### 主要方法

#### put

```python
def put(self, item: TaskEnvelope[T] | TerminationSignal) -> None:
    """入队任务或终止信号到所有输出队列通道（遍历所有目标逐个转发）。"""
```

#### put_target

```python
def put_target(self, name: str, item: TaskEnvelope[T] | TerminationSignal) -> None:
    """
    入队任务或终止信号到指定的输出队列。

    :param name: 输出队列目标节点名称
    :param item: 要入队的任务或终止信号
    """
```

用于向指定下游节点定向分发。

#### get_target_names

```python
def get_target_names(self) -> list[str]:
    """获取所有输出队列的目标节点名称。"""
```

返回当前所有已注册下游通道的名称列表（即 `_queues` 的键）。

### 辅助方法

```python
def add_queue(self, name: str, queue: Any) -> None:
    """
    添加一个输出队列到队列列表中。

    :param name: 队列的目标节点名称，用于标识该队列
    :param queue: 要添加的输出队列
    :raises DuplicateNodeError: 如果名称已存在于队列列表中
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
4. 否则继续等待（`_process_item` 返回 `None`，外层 `get` 循环继续）

---

## 使用示例

以下示例展示 `TaskInQueue` 和 `TaskOutQueue` 的基本用法，包括任务 put/get、终止信号合并和动态添加通道。

```python
from queue import Queue as ThreadQueue
from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue
from celestialflow.runtime.util_types import TerminationSignal, TerminationIdPool

# ===== TaskInQueue 使用示例 =====

# 创建输入队列，指定当前节点名称和队列容量
in_queue = TaskInQueue(
    out_name="processor",
    maxsize=0,  # 0 表示无限制
)

# 添加上游来源名称
in_queue.add_source_name("producer1")
in_queue.add_source_name("producer2")

# 上游生产者放入任务
env1 = TaskEnvelope(task=100, id=1)
env2 = TaskEnvelope(task=200, id=2)
in_queue.put(env1)
in_queue.put(env2)

# 下游消费者获取任务
task1 = in_queue.get()
print(f"收到任务: {task1.get_task()}, ID: {task1.get_id()}")

# 动态添加新的上游来源
in_queue.add_source_name("producer3")
print(f"上游来源数: {len(in_queue.source_names)}")

# ===== TaskOutQueue 使用示例 =====

# 创建输出队列（初始为空，后续通过 add_queue 动态添加通道）
out_queue = TaskOutQueue(
    in_name="processor",
)

# 动态添加下游队列通道（注意参数顺序：先名称，后队列）
consumer_q1 = ThreadQueue()
consumer_q2 = ThreadQueue()
out_queue.add_queue("consumer1", consumer_q1)
out_queue.add_queue("consumer2", consumer_q2)

# 广播任务到所有下游
env3 = TaskEnvelope(task="broadcast_msg", id=3)
out_queue.put(env3)

# 验证两个消费者都收到了
print(f"consumer1 收到: {consumer_q1.get().get_task()}")
print(f"consumer2 收到: {consumer_q2.get().get_task()}")

# 定向发送到指定下游
consumer_q3 = ThreadQueue()
out_queue.add_queue("consumer3", consumer_q3)

env4 = TaskEnvelope(task="targeted_msg", id=4)
out_queue.put_target("consumer3", env4)
print(f"consumer3 收到: {consumer_q3.get().get_task()}")

# ===== 终止信号合并 =====

# 新建一个只用于演示合并的输入队列
merge_queue = TaskInQueue(out_name="merger")
merge_queue.add_source_name("producer1")
merge_queue.add_source_name("producer2")

# 两个上游都发送终止信号
merge_queue.put(TerminationSignal(_id=1, source="producer1"))
merge_queue.put(TerminationSignal(_id=2, source="producer2"))

# get() 会自动合并所有上游的终止信号并返回 TerminationIdPool
result = merge_queue.get()

if isinstance(result, TerminationIdPool):
    print(f"收到合并终止信号，包含 IDs: {result.ids}")  # [1, 2]

# ===== drain 清空队列 =====
# 创建新队列并放入残留任务
residual_q = TaskInQueue(
    out_name="drain_test",
)
residual_q.add_source_name("src")
residual_q.put(TaskEnvelope(task="leftover", id=5))

# drain 清空所有剩余任务
leftovers = residual_q.drain()
print(f"残留任务数: {len(leftovers)}")
```

## 注意事项

1. **多通道**: `TaskOutQueue` 管理多个下游队列
2. **来源管理**: `add_source_name` 和 `add_queue` 均防重（`DuplicateNodeError`）
3. **终止合并**: `_merge_termination` 会检查是否遗漏 source，遗漏则抛 `TerminationMergeError`
4. **drain 特性**: 仅在同步环境（`_finish_start`）中使用，用于收集未消费任务
