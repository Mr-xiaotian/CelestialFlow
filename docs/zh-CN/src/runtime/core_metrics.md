# src/celestialflow/runtime/core_metrics.py

> 📅 最后更新日期: 2026/09/24

`TaskMetrics` 模块负责管理和统计任务执行过程中的各项指标：外部注入任务数、上游接收任务数、成功数、失败数、重复任务数，以及各上游/下游节点的流量。它通常作为任务节点（如 `TaskExecutor`、`TaskSplitter`、`TaskRouter`）的一个组件存在。

## 初始化

```python
class TaskMetrics:
    def __init__(self) -> None:
        """初始化 TaskMetrics。"""
```

`__init__` 不接收参数。它会：

1. 将 `retry_exceptions` 置为空元组；
2. 初始化观察者列表 `_observers` 与生命周期状态 `_status`（`StageStatus.NOT_STARTED`）；
3. 将忙碌耗时状态 `busy_seconds = 0.0`、`_in_flight = 0`、`_busy_since = None`；
4. 创建统一的线程锁 `self.lock`，并调用 `_init_counter()` 初始化计数器。

## 实例属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `lock` | `threading.Lock` | 所有内部计数器共用的同一把锁 |
| `retry_exceptions` | `tuple[type[Exception], ...]` | 需要重试的异常类型 |
| `external_input_counter` | `ValueWrapper` | 外部注入任务计数 |
| `success_counter` | `ValueWrapper` | 成功任务计数 |
| `fail_counter` | `ValueWrapper` | 失败任务计数 |
| `duplicate_counter` | `ValueWrapper` | 重复任务计数 |
| `upstream_counter` | `dict[str, ValueWrapper]` | 各上游节点 → 接收任务数 |
| `downstream_counter` | `dict[str, ValueWrapper]` | 各下游节点 → 发送任务数 |
| `busy_seconds` | `float` | 已闭合的忙碌时间片之和 |
| `_in_flight` | `int` | 正在执行的任务数 |
| `_busy_since` | `float \| None` | 当前忙碌时间片起点 |

> `_init_counter()` 中所有 `ValueWrapper` 都传入 `lock=self.lock`，**共用同一把锁**，以保证执行模式切换时 counter 对象保持稳定。

## 观察者管理

```python
def add_observer(self, observer: BaseObserver) -> None:
    """注册观察者。"""


def remove_observer(self, observer: BaseObserver) -> None:
    """移除观察者。"""
```

已注册的观察者会在计数变化及生命周期事件时收到回调：

| 触发方法 | 观察者回调 |
|---------|-----------|
| `add_external_input_count()` | `on_task_added(count)` |
| `add_success_count()` | `on_task_success(count)` |
| `add_fail_count()` | `on_task_fail(count)` |
| `add_duplicate_count()` | `on_task_duplicate(count)` |
| `on_start()` | `on_start()` |
| `on_finish()` | `on_finish()` |

> 注意：`add_downstream_count()` 不触发观察者回调。

## 重试管理

```python
def set_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """添加需要重试的异常类型。"""
```

异常类型以 `tuple` 形式累加到 `self.retry_exceptions`（每次调用追加，不会覆盖）。

```python
def get_retry_error_type_names(self) -> set[str]:
    """获取当前执行器允许从持久化失败记录中恢复的错误类型名称集合。"""
```

返回 `{exception_type.__name__ ...}`，在 `TaskGraph.restore_db()` 中用于按 `error_type` 过滤可重试的持久化记录。

## 计数器设置

```python
def set_upstream_counter(self, name: str, counter: ValueWrapper) -> None:
    """添加上游任务计数器（统计从上游节点接收的任务数量）。"""


def set_downstream_counter(self, name: str, counter: ValueWrapper) -> None:
    """添加下游任务计数器（统计向下游节点发送的任务数量）。"""
```

这两个方法由节点的 `connect_to()` 在等待队列连接时调用：同一条边的上下游共享同一个 `ValueWrapper`，上游发送任务时递增，下游即视为接收。

## 计数器操作

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

## 生命周期状态

`TaskMetrics` 内部维护 `_status`（`StageStatus` 枚举），启动/结束时更新：

- `on_start()`：将状态置为 `StageStatus.RUNNING`，并广播启动事件。
- `on_finish()`：将状态置为 `StageStatus.STOPPED`，并广播结束事件。
- `get_status()`：读取当前状态，返回 `StageStatus` 枚举。

## 状态查询

### 输入计数

输入任务按来源拆分为「外部注入」与「上游提供」两类，再合并为总输入：

```python
def get_external_input_count(self) -> int:
    """获取外部注入的任务数量。"""


def get_upstream_input_count(self) -> int:
    """获取上游提供的任务数量（累加各上游计数器）。"""


def get_input_count(self) -> int:
    """获取任务总数（外部注入 + 上游提供）。"""
```

### 单项查询

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

判断所有输入任务是否都已处理完毕，比较 `get_input_count()` 与 `processed = success + fail + duplicate` 是否相等。

```python
def is_tasks_finished(self) -> bool:
    """所有任务处理完毕返回 True，否则返回 False。"""
```

### get_counts

获取当前所有计数指标的快照字典：

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

## 忙碌耗时（实测）

忙碌耗时不再依赖估算，而是由调度器在每个任务实际执行期间通过 `begin_task()` / `end_task()` 打点，直接累计墙钟时间：

```python
def begin_task(self) -> None:
    """一个任务开始实际执行。"""


def end_task(self) -> None:
    """一个任务执行结束（含重试全部结束）。"""


def get_elapsed(self) -> float:
    """累计忙碌墙钟时间（秒），含当前尚未闭合的时间片。"""
```

实现机制：

- `begin_task()` 将 `_in_flight` 加一；当从 `0 → 1`（节点由闲变忙）时记录 `_busy_since = time.perf_counter()`。
- `end_task()` 将 `_in_flight` 减一；当从 `1 → 0`（节点由忙变闲）且 `_busy_since` 非空时，把 `perf_counter() - _busy_since` 累加进 `busy_seconds`，并清空 `_busy_since`。
- `get_elapsed()` 返回已闭合时间片之和；若当前存在未闭合时间片，再加上 `perf_counter() - _busy_since`。

因此节点空闲等待任务的时间不会被计入，反应的是真实忙碌时间。

## 使用示例

以下示例展示 `TaskMetrics` 的核心用法：计数器操作、上游/下游统计与状态查询。

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

### 上下游流量统计

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

### 实测忙碌耗时

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
