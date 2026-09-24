# src/celestialflow/runtime/core_queue.py

> 📅 Last Updated: 2026/09/24

The `TaskQueue` module provides `TaskInQueue` and `TaskOutQueue`, two classes used for connecting pipelines between different nodes. They support a multi-producer, multi-consumer model and integrate termination signal merge functionality.

## Overview

- **TaskInQueue**: Task input queue, aggregating tasks from multiple upstream sources and merging termination signals
- **TaskOutQueue**: Task output queue, broadcasting results to one or more downstream queue channels

Both internally use `queue.Queue` (thread-safe queue) as the default backend.

---

## TaskInQueue

Task input queue, used to receive tasks from multiple upstream sources and merge termination signals.

### Initialization

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

Internal attributes:

| Attribute | Type | Description |
|------|------|------|
| `out_name` | `str` | Unique name of the current node |
| `queue` | `Queue[TaskEnvelope[T] \| TerminationSignal]` | Underlying thread-safe queue |
| `source_names` | `list[str]` | List of upstream source names |
| `termination_dict` | `dict[str, int]` | Recorded termination signal source → ID |

The queue is automatically created internally; no external injection is required. Upstream sources are dynamically added via `add_source_name()`.

### Main Methods

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

`get()` internally loops over the underlying queue until `_process_item()` returns a non-`None` value.

Termination signal merging logic:

- Receive a termination signal from `"input"` → immediately return `TerminationIdPool(ids=[...])`
- Receive termination signals from all `source_names` → merge and return
- Only partial upstream signals received → continue waiting (`_process_item` returns `None`, and the outer loop continues)
- Receive the `TerminationIdPool` itself (a pool already merged upstream) → return directly, without going through the upstream merge logic again
```

#### drain

```python
def drain(self) -> list[TaskEnvelope[T]]:
    """
    清空队列中的所有任务，返回任务列表。
    记录终止信号但不会返回 TerminationIdPool（仅用于同步环境，如 _finish_start）。
    """
```

### Helper Methods

```python
def add_source_name(self, name: str) -> None:
    """
    添加入队来源名称。

    :param name: 入队来源名称
    :raises DuplicateNodeError: 如果名称已存在
    """
```

Internal termination-handling helper methods:

```python
def _record_termination(self, signal: TerminationSignal) -> None:
    """记录入队来源的终止信号；来源不在 source_names ∪ {"input"} 时抛 UnknownNodeError。"""


def _can_merge_termination(self) -> bool:
    """所有 source_names 都已发出终止信号时返回 True。"""


def _merge_termination(self) -> TerminationIdPool:
    """合并所有 source_names 的终止信号；存在遗漏来源时抛 TerminationMergeError。"""
```

> `_merge_termination()` only merges termination signals from `source_names`; it does not handle the direct termination injected by `"input"`, nor the post-merge termination of `self.out_name`.

## TaskOutQueue

Task output queue, used to broadcast tasks to multiple downstream targets.

### Initialization

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

The output queue dictionary `_queues` is initially empty, with downstream channels dynamically added via `add_queue()`.

### Main Methods

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

Used for directed dispatch to a specific downstream node.

#### get_target_names

```python
def get_target_names(self) -> list[str]:
    """获取所有输出队列的目标节点名称。"""
```

Returns the list of names of all currently registered downstream channels (i.e., the keys of `_queues`).

### Helper Methods

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

## Termination Signal Mechanism

### Signal Flow

```
Upstream node → out_queue.put(TerminationSignal) → queue
                                                    ↓
                                            in_queue.get()
                                                    ↓
                                        termination_dict[source] = id
                                                    ↓
                                        All sources collected? → Yes → merge → TerminationIdPool
                                        Direct input termination?  → Yes → return immediately
                                        Otherwise                 → continue waiting
```

### Merge Rules

`TaskInQueue` waits for termination signals from all `source_names` and merges them into a single `TerminationIdPool`:

1. In `_record_termination`, validate source legitimacy (must be in `source_names ∪ {"input"}`)
2. If `"input"` is present → immediately return `TerminationIdPool(ids=[...])`
3. If `_can_merge_termination()` is True → call `_merge_termination()`
4. Otherwise continue waiting (`_process_item` returns `None`, outer `get` loop continues)

---

## Usage Examples

The following example demonstrates basic usage of `TaskInQueue` and `TaskOutQueue`, including task put/get, termination signal merging, and dynamic channel addition.

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

## Notes

1. **Multi-channel**: `TaskOutQueue` manages multiple downstream queues
2. **Source management**: Both `add_source_name` and `add_queue` prevent duplicates (`DuplicateNodeError`)
3. **Termination merge**: `_merge_termination` checks for missing sources and raises `TerminationMergeError` if any are absent
4. **drain characteristics**: Only used in synchronous environments (`_finish_start`) to collect unconsumed tasks
