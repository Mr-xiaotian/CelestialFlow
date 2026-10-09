# src/celestialflow/observer/core_observer.py

> 📅 最后更新日期: 2026/10/09

`core_observer.py` 定义了执行器生命周期观察者的**基类** `Observer`。它声明了任务 / 节点 / 任务图全生命周期的事件回调接口，所有回调均提供默认空实现，实现方继承本基类即可只覆写关心的方法。

## Observer

```python
class Observer:
    def on_node_start(self, event: NodeStartEvent) -> None: ...
    def on_task_input(self, event: TaskInputEvent) -> None: ...
    def on_task_success(self, event: TaskSuccessEvent) -> None: ...
    def on_task_fail(self, event: TaskFailEvent) -> None: ...
    def on_task_skip(self, event: TaskSkipEvent) -> None: ...
    def on_task_retry(self, event: TaskRetryEvent) -> None: ...
    def on_termination_input(self, event: TerminationInputEvent) -> None: ...
    def on_termination_merge(self, event: TerminationMergeEvent) -> None: ...
    def on_worker_crash(self, event: WorkerCrashEvent) -> None: ...
    def on_node_end(self, event: NodeEndEvent) -> None: ...
    def on_graph_start(self, event: GraphStartEvent) -> None: ...
    def on_graph_end(self, event: GraphEndEvent) -> None: ...

    def handle_exception(self, exception: Exception) -> None: ...
```

所有事件回调默认空实现（不是 ABC），子类按需覆写。回调参数都是 `core_event.py` 中定义的事件 `dataclass`。

### 事件说明

| 回调 | 事件 | 触发时机 |
|------|------|----------|
| `on_node_start` | `NodeStartEvent` | 节点启动（`BaseTaskNode._prepare_start`） |
| `on_node_end` | `NodeEndEvent` | 节点结束（`BaseTaskNode._finish_start`） |
| `on_task_input` | `TaskInputEvent` | 任务进入节点输入队列 |
| `on_task_success` | `TaskSuccessEvent` | 任务成功处理 |
| `on_task_fail` | `TaskFailEvent` | 任务最终失败 |
| `on_task_skip` | `TaskSkipEvent` | 任务被跳过 |
| `on_task_retry` | `TaskRetryEvent` | 任务失败但触发重试 |
| `on_termination_input` | `TerminationInputEvent` | 终止信号进入输入队列 |
| `on_termination_merge` | `TerminationMergeEvent` | 多来源终止信号被合并 |
| `on_worker_crash` | `WorkerCrashEvent` | 工作线程/协程在兜底层捕获到未处理异常 |
| `on_graph_start` | `GraphStartEvent` | 任务图启动 |
| `on_graph_end` | `GraphEndEvent` | 任务图结束 |

### handle_exception

```python
def handle_exception(self, exception: Exception) -> None:
    traceback.print_exception(exception)
```

当观察者的某个回调自身抛出异常时，`ObserverHub` 会捕获该异常并调用**该观察者自身**的 `handle_exception` 处理。默认实现把异常回溯打印到标准错误；子类可覆写以实现自定义策略（收集、上报或忽略）。若 `handle_exception` 自身再抛出异常，则由 hub 的 `handle_exception` 作为最终兜底。

## 事件分发机制

`Observer` 的事件**并非由节点逐个直接调用每个观察者**，而是通过 `ObserverHub` 广播：

- 节点持有 `ObserverHub`（`BaseTaskNode.observers`），通过 `add_observer()` 注册观察者；
- 节点在某事件发生时调用 `hub.on_*()`，hub 再按注册顺序转发给每个观察者；
- 单个观察者回调抛出的异常由 hub 捕获，交给该观察者的 `handle_exception`，**不中断其他观察者的分发，也不逃逸到框架路径**。

内置观察者（也是 `Observer` 子类）：

| 类 | 所在文件 | 说明 |
|---|---------|------|
| `PrintObserver` | `core_observer_print.py` | 基于 `print` 的控制台观察者 |
| `MetricsObserver` | `core_metrics.py` | 依据事件维护节点计数与状态的指标观察者 |
| `ObserverHub` | `core_hub.py` | 观察者分发中心，本身也是 `Observer` |
| `LifecycleInlet` / `LogInlet` | `persist` | 由 `run_node_resources` / `run_graph_resources` 装配，消费事件落盘 |

## 使用示例

```python
from celestialflow.node import TaskExecutor
from celestialflow.observer import Observer, TaskFailEvent, TaskSuccessEvent


class MyObserver(Observer):
    def on_task_success(self, event: TaskSuccessEvent) -> None:
        print(f"{event.node} 成功: {event.result_repr}")

    def on_task_fail(self, event: TaskFailEvent) -> None:
        print(f"{event.node} 失败: {event.exception}")


executor = TaskExecutor("Test", lambda x: x * 2)
executor.add_observer(MyObserver())
executor.run([1, 2, 3])
```

## 注意事项

1. **回调参数为事件对象**：与旧版 `BaseObserver`（回调接收 `count` 等基本参数）不同，所有回调都接收对应的事件 `dataclass`，可用字段更丰富。
2. **`handle_exception` 不自动包装**：回调自身不能保证不抛异常——异常由 hub 捕获后转交本观察者的 `handle_exception`；它自身不会被 hub 再包装，但会被 hub 的 `handle_exception` 兜底。
3. **继承而不是实例化**：`Observer` 基类开放所有回调，实际使用通常继承它并只覆写需要的方法。