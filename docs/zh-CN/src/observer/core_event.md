# src/celestialflow/observer/core_event.py

> 📅 最后更新日期: 2026/10/09

`core_event.py` 定义了观察者体系中的**全部事件类型**。它们作为观察者回调的入参，描述任务 / 节点 / 任务图生命周期的各类变化。所有事件均为 `frozen=True, slots=True` 的只读 `dataclass`。

## 事件一览

| 事件 | 字段 | 触发时机 |
|------|------|----------|
| `NodeStartEvent` | `node`、`execution_mode`、`max_workers` | 节点启动 |
| `NodeEndEvent` | `node`、`execution_mode`、`max_workers`、`elapsed` | 节点结束 |
| `TaskInputEvent` | `node`、`task`、`task_repr`、`input_id`、`from_node` | 任务进入节点输入队列 |
| `TaskSuccessEvent` | `node`、`task`、`task_repr`、`result`、`result_repr`、`elapsed`、`task_id`、`success_id` | 任务成功处理 |
| `TaskFailEvent` | `node`、`task`、`task_repr`、`exception`、`task_id`、`error_id` | 任务最终失败 |
| `TaskSkipEvent` | `node`、`task`、`task_repr`、`task_id`、`skip_id` | 任务被跳过 |
| `TaskRetryEvent` | `node`、`task`、`task_repr`、`exception`、`task_id`、`retry_times` | 任务失败但触发重试 |
| `TerminationInputEvent` | `node`、`termination_id` | 终止信号进入输入队列 |
| `TerminationMergeEvent` | `node`、`parent_ids`、`termination_id` | 多来源终止信号被合并 |
| `WorkerCrashEvent` | `node`、`exception` | 工作线程 / 协程在兜底层捕获到未处理异常 |
| `GraphStartEvent` | `graph`、`graph_mode`、`start_time`、`class_name`、`is_dag`、`nodes`、`edges`、`source_nodes`、`node_meta` | 任务图启动 |
| `GraphEndEvent` | `graph`、`elapsed` | 任务图结束 |

## 字段说明

### 通用字段

- `node`：节点名称，标识事件所属节点。
- `task`：原始任务数据（`Any`）；`task_repr` 为其可读字符串表示。

### 事件 ID 字段

- `input_id`：当前输入事件 ID。
- `task_id`：任务输入事件 ID（与 `TaskInputEvent.input_id` 对应）。
- `success_id` / `error_id` / `skip_id`：成功 / 错误 / 跳过事件各自的事件 ID。
- `termination_id`：终止信号事件 ID。
- `parent_ids`：参与合并的终止信号事件 ID 列表。

### 任务来源

- `from_node`：上游来源节点名称；`None` 表示由外部直接注入。此字段是 `MetricsObserver` 区分外部注入与上游投递的依据。

### 图元信息（`GraphStartEvent`）

- `graph`：任务图名称。
- `graph_mode`：任务图运行模式。
- `start_time`：任务图启动时间。
- `class_name`：任务图类名。
- `is_dag`：是否为 DAG 任务图。
- `nodes`：任务图节点名称列表。
- `edges`：任务图边邻接表（`{from_name: [to_name, ...]}`）。
- `source_nodes`：源节点名称列表。
- `node_meta`：各节点的构建期元信息。

## 代码示例

```python
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TaskSuccessEvent:
    node: str
    task: Any
    task_repr: str
    result: Any
    result_repr: str
    elapsed: float
    task_id: int
    success_id: int
```

所有事件均使用 `frozen=True, slots=True`，即不可变（构造后字段不可改、可哈希）且通过 `__slots__` 节省内存。

## 使用示例

```python
from celestialflow.observer import (
    Observer,
    ObserverHub,
    TaskFailEvent,
    TaskSuccessEvent,
    WorkerCrashEvent,
)


class MyObserver(Observer):
    def on_task_success(self, event: TaskSuccessEvent) -> None:
        print(f"{event.node} 成功: {event.result_repr}")

    def on_task_fail(self, event: TaskFailEvent) -> None:
        print(f"{event.node} 失败: {event.exception}")

    def on_worker_crash(self, event: WorkerCrashEvent) -> None:
        print(f"{event.node} 工作器崩溃: {event.exception}")


hub = ObserverHub()
hub.add_observer(MyObserver())
```

## 注意事项

1. **只读事件**：事件均为不可变 `dataclass`，观察者不应修改事件内部字段。
2. **由框架构造**：事件由节点 / 任务图在对应时机构造并调用 `hub.on_*()`，一般无需手动构造。
3. **旧的"计数型回调"已废弃**：事件对象取代了旧版 `BaseObserver` 中 `on_task_success(count)` 等基本参数回调，可携带更丰富的上下文。