# src/celestialflow/observer/__init__.py

> 📅 最后更新日期: 2026/11/13

`observer` 模块是 CelestialFlow 的**可观测性模块**，负责观察者协议、统一事件类型、事件分发中心，以及内置的指标与进度输出观察者。

## 导出符号

模块级 `__all__` 完整导出如下：

```python
__all__ = [
    "Event",
    "GraphEndEvent",
    "GraphStartEvent",
    "MetricsObserver",
    "NodeEndEvent",
    "NodeStartEvent",
    "Observer",
    "ObserverHub",
    "PrintObserver",
    "TaskFailEvent",
    "TaskInputEvent",
    "TaskRetryEvent",
    "TaskSkipEvent",
    "TaskSuccessEvent",
    "TerminationInputEvent",
    "TerminationMergeEvent",
]
```

导出符号可按下表归类：

| 导出符号 | 来源模块 | 说明 |
|---------|---------|------|
| `Event` | `core_event` | 所有观测事件的基类，仅作类型标识，不携带状态 |
| `Observer` | `core_observer` | 观察者基类，只声明统一的 `on_event(event)` 与 `handle_exception(exception)` |
| `ObserverHub` | `core_hub` | 观察者分发中心，本身也是 `Observer`，按注册顺序转发事件，并提供 `find()` |
| `MetricsObserver` | `core_metrics` | 图级指标观察者（写模型 + 只读视图），依据事件维护节点计数与状态 |
| `PrintObserver` | `core_print` | 基于 `print` 的控制台观察者，便于本地调试与示例演示 |
| `NodeStartEvent` / `NodeEndEvent` | `core_event` | 节点启动 / 结束事件 |
| `TaskInputEvent` / `TaskSuccessEvent` / `TaskFailEvent` / `TaskSkipEvent` / `TaskRetryEvent` | `core_event` | 任务输入 / 成功 / 失败 / 跳过 / 重试事件 |
| `TerminationInputEvent` / `TerminationMergeEvent` | `core_event` | 终止信号输入 / 合并事件 |
| `GraphStartEvent` / `GraphEndEvent` | `core_event` | 任务图启动 / 结束事件 |

## 文件说明

1. **core_observer.py**（`Observer`）
   - **作用**: 执行器生命周期观察者基类，只声明 `on_event` 与 `handle_exception`。
   - **特点**: 所有事件从单一入口进入，子类用 `match` 按类型分派；基类不是 `ABC`。

2. **core_event.py**（`Event` + 11 个事件 `dataclass`）
   - **作用**: 定义统一事件基类与任务 / 节点 / 任务图生命周期全部事件类型。
   - **特点**: 具体事件均为 `frozen=True, slots=True` 的只读数据类；`Event` 使用 `__slots__ = ()` 不携带状态。

3. **core_hub.py**（`ObserverHub`）
   - **作用**: 观察者分发中心，将收到的每个事件按注册顺序转发给已注册观察者；`find()` 按类型递归查找观察者。
   - **特点**: 本身也是 `Observer`；观察者列表写时复制（copy-on-write）。

4. **core_metrics.py**（`MetricsObserver`）
   - **作用**: 图级指标观察者，依据事件维护每个节点的计数、状态与运行起始时间。
   - **特点**: 既作为观察者写入，又通过 `MetricsView` 协议暴露只读 `NodeMetrics` 快照。

5. **core_print.py**（`PrintObserver`）
   - **作用**: 开箱即用的控制台观察者。
   - **特点**: 使用线程安全的 `ValueWrapper` 统计 `total` / `succeeded` / `failed` / `skipped`，并以 `[name] ...` 前缀打印。

## 模块关联

### 内部关联
- `Observer` 是观察者模式基类；`ObserverHub` 与 `MetricsObserver`、`PrintObserver` 都是 `Observer` 子类。
- `core_event.py` 定义的事件类型被 `core_observer` / `core_hub` / `core_metrics` / `core_print` 共同引用。

### 外部关联
- **与 Node 模块**: `BaseTaskNode` 持有 `ObserverHub observers`，在某事件发生时构造事件并调用 `hub.on_event(...)` 广播；结果读取时用 `observers.find(LifecycleObserver)` 定位生命周期观察者并取得 `db_path`。
- **与 Persist 模块**: `LifecycleObserver` / `LogObserver` 是 `Observer` 子类，由 `run_node_resources` / `run_graph_resources` 注册到 hub，消费事件落盘。
- **与 Assembly 模块**: `assembly/core_run.py` 装配 `ObserverHub`，注册 `MetricsObserver`、`LifecycleObserver`、`LogObserver` 等。

## 架构特点

### 事件驱动与分发
- **单一入口**: 所有观察者只实现 `on_event(event)`，事件对象为 `core_event.py` 中定义的只读 `dataclass`，携带丰富字段。
- **显式生命周期时间戳**: 节点 / 任务图的起止时间由事件字段（`start_time` / `end_time`）携带，观察者无需自行调用 `time.time()` 采样。
- **多播分发**: `ObserverHub` 一次性向所有注册观察者广播同一事件。
- **异常隔离**: 单个观察者回调抛出的异常由 hub 捕获并交给该观察者自身的 `handle_exception`，**不中断**其余观察者的分发，也不逃逸到框架执行路径。

## 使用示例

```python
from celestialflow.observer import (
    Event,
    MetricsObserver,
    Observer,
    ObserverHub,
    TaskSuccessEvent,
)


class MyObserver(Observer):
    def on_event(self, event: Event) -> None:
        match event:
            case TaskSuccessEvent():
                print(f"{event.node} 成功: {event.result_repr}")
            case _:
                pass


hub = ObserverHub()
hub.add_observer(MyObserver())
hub.add_observer(MetricsObserver())
```

查找已注册的观察者：

```python
from celestialflow.observer import ObserverHub, PrintObserver

hub = ObserverHub()
hub.add_observer(PrintObserver("StageA"))

printer = hub.find(PrintObserver)
print(printer.name if printer is not None else None)  # StageA
```

## 注意事项

1. **导入路径**: 从 `celestialflow.observer` 导入上述符号，而非旧版 `celestialflow.observability`。
2. **指标与进度分开**: 需要结构化的节点指标使用 `MetricsObserver`；只需控制台进度输出使用 `PrintObserver`。
3. **观察者只实现 `on_event`**: 旧版的 `on_node_start` / `on_task_success` 等逐个回调已全部移除。
