# src/celestialflow/observer/__init__.py

> 📅 最后更新日期: 2026/10/09

`observer` 模块是 CelestialFlow 的**可观测性模块**，负责观察者协议、任务 / 节点 / 任务图事件类型、事件分发中心，以及内置的指标与进度输出观察者。

## 导出符号

模块级 `__all__` 完整导出如下：

```python
__all__ = [
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
    "WorkerCrashEvent",
]
```

导出符号可按下表归类：

| 导出符号 | 来源模块 | 说明 |
|---------|---------|------|
| `Observer` | `core_observer` | 观察者基类，声明任务 / 节点 / 图全生命周期回调接口，所有回调默认空实现 |
| `ObserverHub` | `core_hub` | 观察者分发中心，本身也是 `Observer`，按注册顺序转发事件 |
| `MetricsObserver` | `core_metrics` | 图级指标观察者（写模型 + 只读视图），依据事件维护节点计数与状态 |
| `PrintObserver` | `core_observer_print` | 基于 `print` 的控制台观察者，便于本地调试与示例演示 |
| `NodeStartEvent` / `NodeEndEvent` | `core_event` | 节点启动 / 结束事件 |
| `TaskInputEvent` / `TaskSuccessEvent` / `TaskFailEvent` / `TaskSkipEvent` / `TaskRetryEvent` | `core_event` | 任务输入 / 成功 / 失败 / 跳过 / 重试事件 |
| `TerminationInputEvent` / `TerminationMergeEvent` | `core_event` | 终止信号输入 / 合并事件 |
| `WorkerCrashEvent` | `core_event` | 工作器崩溃事件 |
| `GraphStartEvent` / `GraphEndEvent` | `core_event` | 任务图启动 / 结束事件 |

## 文件说明

1. **core_observer.py**（`Observer`）
   - **作用**: 执行器生命周期观察者基类，声明 12 个事件回调与 `handle_exception`。
   - **特点**: 所有回调均提供默认空实现，不是 ABC，子类按需覆写。

2. **core_event.py**（12 个事件 `dataclass`）
   - **作用**: 定义任务 / 节点 / 任务图生命周期全部事件类型。
   - **特点**: 均为 `frozen=True, slots=True` 的只读数据类，作为观察者回调参数。

3. **core_hub.py**（`ObserverHub`）
   - **作用**: 观察者分发中心，将收到的每个事件按注册顺序转发给已注册观察者。
   - **特点**: 本身也是 `Observer`；观察者列表写时复制（copy-on-write）。

4. **core_metrics.py**（`MetricsObserver`）
   - **作用**: 图级指标观察者，依据事件维护每个节点的计数、状态与运行起始时间。
   - **特点**: 既作为观察者写入，又通过 `MetricsView` 协议暴露只读 `NodeMetrics` 快照。

5. **core_observer_print.py**（`PrintObserver`）
   - **作用**: 开箱即用的控制台观察者。
   - **特点**: 使用线程安全的 `ValueWrapper` 统计 `total` / `succeeded` / `failed` / `skipped`，并以 `[name] ...` 前缀打印。

## 模块关联

### 内部关联
- `Observer` 是观察者模式基类；`ObserverHub` 与 `MetricsObserver`、`PrintObserver` 都是 `Observer` 子类。
- `core_event.py` 定义的事件类型被 `core_observer` / `core_hub` / `core_metrics` / `core_observer_print` 共同引用。

### 外部关联
- **与 Node 模块**: `BaseTaskNode` 持有 `ObserverHub observers`，在某事件发生时调用 `hub.on_*()` 广播。
- **与 Persist 模块**: `run_node_resources` / `run_graph_resources` 将 `LifecycleInlet` / `LogInlet` 作为观察者注册到 hub，消费事件落盘。
- **与 Assembly 模块**: `assembly/core_run.py` 装配 `ObserverHub`，注册 `MetricsObserver`、`LifecycleInlet`、`LogInlet` 等。

## 架构特点

### 事件驱动与分发
- **事件对象为回调参数**: 所有回调都接收 `core_event.py` 中定义的只读 `dataclass`，携带丰富字段。
- **多播分发**: `ObserverHub` 一次性向所有注册观察者广播同一事件。
- **异常隔离**: 单个观察者回调抛出的异常由 hub 捕获并交给该观察者自身的 `handle_exception`，**不中断**其余观察者的分发，也不逃逸到框架执行路径。

## 使用示例

```python
from celestialflow.observer import (
    Observer,
    ObserverHub,
    TaskSuccessEvent,
    MetricsObserver,
)


class MyObserver(Observer):
    def on_task_success(self, event: TaskSuccessEvent) -> None:
        print(f"{event.node} 成功: {event.result_repr}")


hub = ObserverHub()
hub.add_observer(MyObserver())
hub.add_observer(MetricsObserver())
```

## 注意事项

1. **导入路径**: 从 `celestialflow.observer` 导入上述符号，而非旧版 `celestialflow.observability`。
2. **指标与进度分开**: 需要结构化的节点指标使用 `MetricsObserver`；只需控制台进度输出使用 `PrintObserver`。