# src/celestialflow/runtime/core_metrics.py

> 📅 Last Updated: 2026/09/24

The `TaskMetrics` module is responsible for managing and tracking various metrics during task execution: the number of externally injected tasks, the number of tasks received from upstream, the success count, the failure count, the duplicate task count, and the traffic of each upstream/downstream node. It typically exists as a component of a task node (such as `TaskExecutor`, `TaskSplitter`, `TaskRouter`).

## Initialization

```python
class TaskMetrics:
    def __init__(self) -> None:
        """初始化 TaskMetrics。"""
```

`__init__` takes no arguments. It:

1. Sets `retry_exceptions` to an empty tuple;
2. Initializes the observer list `_observers` and the lifecycle status `_status` (`StageStatus.NOT_STARTED`);
3. Initializes the busy-duration state `busy_seconds = 0.0`, `_in_flight = 0`, `_busy_since = None`;
4. Creates a unified thread lock `self.lock` and calls `_init_counter()` to initialize the counters.

## Instance Attributes

| Attribute | Type | Description |
|------|------|------|
| `lock` | `threading.Lock` | The same lock shared by all internal counters |
| `retry_exceptions` | `tuple[type[Exception], ...]` | Exception types that should trigger retries |
| `external_input_counter` | `ValueWrapper` | External injected task count |
| `success_counter` | `ValueWrapper` | Successful task count |
| `fail_counter` | `ValueWrapper` | Failed task count |
| `duplicate_counter` | `ValueWrapper` | Duplicate task count |
| `upstream_counter` | `dict[str, ValueWrapper]` | Each upstream node → received task count |
| `downstream_counter` | `dict[str, ValueWrapper]` | Each downstream node → sent task count |
| `busy_seconds` | `float` | Sum of closed busy time slices |
| `_in_flight` | `int` | Number of tasks currently executing |
| `_busy_since` | `float \| None` | Start of the current busy time slice |

> In `_init_counter()`, every `ValueWrapper` is passed `lock=self.lock`, **sharing the same lock**, so that counter objects stay stable when the execution mode switches.

## Observer Management

```python
def add_observer(self, observer: BaseObserver) -> None:
    """注册观察者。"""


def remove_observer(self, observer: BaseObserver) -> None:
    """移除观察者。"""
```

Registered observers receive callbacks on count changes and lifecycle events:

| Trigger Method | Observer Callback |
|---------|-----------|
| `add_external_input_count()` | `on_task_added(count)` |
| `add_success_count()` | `on_task_success(count)` |
| `add_fail_count()` | `on_task_fail(count)` |
| `add_duplicate_count()` | `on_task_duplicate(count)` |
| `on_start()` | `on_start()` |
| `on_finish()` | `on_finish()` |

> Note: `add_downstream_count()` does not trigger observer callbacks.

## Retry Management

```python
def set_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """添加需要重试的异常类型。"""
```

Exception types are accumulated into `self.retry_exceptions` as a `tuple` (each call appends, never overwrites).

```python
def get_retry_error_type_names(self) -> set[str]:
    """获取当前执行器允许从持久化失败记录中恢复的错误类型名称集合。"""
```

Returns `{exception_type.__name__ ...}`, used in `TaskGraph.restore_db()` to filter retryable persisted records by `error_type`.

## Counter Setup

```python
def set_upstream_counter(self, name: str, counter: ValueWrapper) -> None:
    """添加上游任务计数器（统计从上游节点接收的任务数量）。"""


def set_downstream_counter(self, name: str, counter: ValueWrapper) -> None:
    """添加下游任务计数器（统计向下游节点发送的任务数量）。"""
```

These two methods are called by a node's `connect_to()` when queue connections are awaited: the upstream and downstream of the same edge share the same `ValueWrapper`; when the upstream sends a task it increments, and the downstream counts it as received.

## Counter Operations

```python
def add_external_input_count(self, add_count: int = 1) -> None:
    """更新外部注入任务计数器（经 put_task 进入节点的任务）。"""


def add_success_count(self, count: int = 1) -> None:
    """线程安全地增加成功任务的数量。"""


def add_fail_count(self, count: int = 1) -> None:
    """线程安全地增加失败任务的数量。"""


def add_duplicate_count(self, count: int = 1) -> None:
    """线程安全地增加重复任务的数量。"""


def add_downstream_count(self, name: str, count: int = 1) -> None:
    """线程安全地增加指定下游节点的发送任务数量。"""
```

## Lifecycle Status

`TaskMetrics` internally maintains `_status` (a `StageStatus` enum), updated on start/end:

- `on_start()`: sets the status to `StageStatus.RUNNING` and broadcasts the start event.
- `on_finish()`: sets the status to `StageStatus.STOPPED` and broadcasts the end event.
- `get_status()`: reads the current status and returns a `StageStatus` enum.

## State Queries

### Input Counts

Input tasks are split by source into two categories — "external injection" and "upstream-provided" — and then merged into the total input:

```python
def get_external_input_count(self) -> int:
    """获取外部注入的任务数量。"""


def get_upstream_input_count(self) -> int:
    """获取上游提供的任务数量（累加各上游计数器）。"""


def get_input_count(self) -> int:
    """获取任务总数（外部注入 + 上游提供）。"""
```

### Individual Queries

```python
def get_success_count(self) -> int: ...
def get_fail_count(self) -> int: ...
def get_duplicate_count(self) -> int: ...
```

### get_upstream_counts / get_downstream_counts

```python
def get_upstream_counts(self) -> dict[str, int]:
    """各上游节点传输给当前节点的任务数量；无上游时返回空字典。"""


def get_downstream_counts(self) -> dict[str, int]:
    """当前节点传输给各下游节点的任务数量；无下游时返回空字典。"""
```

### is_tasks_finished

Determines whether all input tasks have been processed, by comparing `get_input_count()` against `processed = success + fail + duplicate` for equality.

```python
def is_tasks_finished(self) -> bool:
    """所有任务处理完毕返回 True，否则返回 False。"""
```

### get_counts

Gets a snapshot dictionary of all current metric counts:

```python
def get_counts(self) -> dict[str, int]:
    return {
        "tasks_input": int,  # 输入任务总数（外部注入与上游提供之和）
        "tasks_succeeded": int,  # 成功任务数
        "tasks_failed": int,  # 失败任务数
        "tasks_duplicated": int,  # 重复任务数
        "tasks_processed": int,  # 已处理总数
        "tasks_pending": int,  # 待处理任务数（max(0, input - processed)）
    }
```

## Busy Duration (Measured)

The busy duration no longer relies on estimation; instead, the scheduler records it via `begin_task()` / `end_task()` during each task's actual execution, directly accumulating wall-clock time:

```python
def begin_task(self) -> None:
    """一个任务开始实际执行。"""


def end_task(self) -> None:
    """一个任务执行结束（含重试全部结束）。"""


def get_elapsed(self) -> float:
    """累计忙碌墙钟时间（秒），含当前尚未闭合的时间片。"""
```

Implementation mechanism:

- `begin_task()` increments `_in_flight`; when it goes from `0 → 1` (the node turns from idle to busy), it records `_busy_since = time.perf_counter()`.
- `end_task()` decrements `_in_flight`; when it goes from `1 → 0` (the node turns from busy to idle) and `_busy_since` is not `None`, it adds `perf_counter() - _busy_since` into `busy_seconds` and clears `_busy_since`.
- `get_elapsed()` returns the sum of closed time slices; if an unclosed slice currently exists, it additionally adds `perf_counter() - _busy_since`.

Therefore, the time a node spends idly waiting for tasks is not counted; what it reflects is the real busy time.

## Usage Examples

The following examples demonstrate the core usage of `TaskMetrics`: counter operations, upstream/downstream statistics, and state queries.

```python
from celestialflow.runtime import TaskMetrics
from celestialflow.runtime.util_types import ValueWrapper

# 1. 初始化指标管理器
metrics = TaskMetrics()

# 2. 添加可重试异常类型
metrics.set_retry_exceptions(ConnectionError, TimeoutError)

# 3. 模拟任务处理过程
# 外部直接注入 3 个任务
metrics.add_external_input_count(3)
# 上游节点提供 2 个任务
metrics.set_upstream_counter("upstream_a", ValueWrapper(value=2))

# 处理成功 3 个、失败 1 个、重复 1 个
metrics.add_success_count(3)
metrics.add_fail_count(1)
metrics.add_duplicate_count(1)

# 4. 查询各计数器的值
print(f"外部注入: {metrics.get_external_input_count()}")  # 3
print(f"上游提供: {metrics.get_upstream_input_count()}")  # 2
print(f"任务总数: {metrics.get_input_count()}")  # 5
print(f"成功数: {metrics.get_success_count()}")  # 3
print(f"失败数: {metrics.get_fail_count()}")  # 1
print(f"重复数: {metrics.get_duplicate_count()}")  # 1

# 5. 获取完整快照字典
counts = metrics.get_counts()
print(f"已处理: {counts['tasks_processed']}")  # 3+1+1 = 5
print(f"待处理: {counts['tasks_pending']}")  # 0
print(f"全部完成: {metrics.is_tasks_finished()}")  # True
```

### Upstream/Downstream Traffic Statistics

```python
from celestialflow.runtime import TaskMetrics
from celestialflow.runtime.util_types import ValueWrapper

metrics = TaskMetrics()
metrics.set_upstream_counter("producer", ValueWrapper(value=10))
metrics.set_downstream_counter("consumer", ValueWrapper(value=4))
metrics.add_downstream_count("consumer", 2)

print(metrics.get_upstream_counts())  # {'producer': 10}
print(metrics.get_downstream_counts())  # {'consumer': 6}
```

### Measured Busy Duration

```python
import time
from celestialflow.runtime import TaskMetrics

metrics = TaskMetrics()

metrics.begin_task()
time.sleep(0.05)  # 模拟任务执行
print(f"执行中: {metrics.get_elapsed():.3f}s")  # ≈ 0.050

metrics.end_task()
elapsed_after = metrics.get_elapsed()
time.sleep(0.05)  # 空闲等待
print(f"空闲后基本不变: {metrics.get_elapsed() == elapsed_after}")  # True
```
