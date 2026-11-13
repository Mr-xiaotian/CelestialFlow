# src/celestialflow/observer/core_observer.py

> 📅 最后更新日期: 2026/11/13

`core_observer.py` 定义了执行器生命周期观察者的**基类** `Observer`。与旧版"每个事件一个回调"不同，当前所有事件统一经由单个 :meth:`on_event` 进入，实现方继承本基类后只需覆写该方法，并用 `match` 按具体事件类型分派，未关心的事件类型自然被忽略。

## Observer

```python
class Observer:
    def on_event(self, event: Event) -> None: ...

    def handle_exception(self, exception: Exception) -> None: ...
```

- `on_event`：**唯一**的事件入口，默认实现忽略所有事件（方法体为 `...`）。
- `handle_exception`：观察者回调自身抛出异常时的处理回调，默认把回溯打印到标准错误。

`Observer` 不是 `ABC`，子类按需覆写即可。事件对象由 `core_event.py` 定义，全部继承自基类 `Event`。

### 事件分派

子类通常在 `on_event` 中使用结构化模式匹配按类型分派：

```python
from celestialflow.observer import Event, Observer, TaskFailEvent, TaskSuccessEvent


class MyObserver(Observer):
    def on_event(self, event: Event) -> None:
        match event:
            case TaskSuccessEvent():
                print(f"{event.node} 成功: {event.result_repr}")
            case TaskFailEvent():
                print(f"{event.node} 失败: {event.exception}")
            case _:
                pass
```

| 事件 | 触发时机 |
|------|----------|
| `NodeStartEvent` | 节点启动（`BaseTaskNode._prepare_start`） |
| `NodeEndEvent` | 节点结束（`BaseTaskNode._finish_start`） |
| `TaskInputEvent` | 任务进入节点输入队列 |
| `TaskSuccessEvent` | 任务成功处理 |
| `TaskFailEvent` | 任务最终失败 |
| `TaskSkipEvent` | 任务被跳过 |
| `TaskRetryEvent` | 任务失败但触发重试 |
| `TerminationInputEvent` | 终止信号进入输入队列 |
| `TerminationMergeEvent` | 多来源终止信号被合并 |
| `GraphStartEvent` | 任务图启动 |
| `GraphEndEvent` | 任务图结束 |

### handle_exception

```python
def handle_exception(self, exception: Exception) -> None:
    traceback.print_exception(exception)
```

当观察者的 `on_event` 自身抛出异常时，`ObserverHub` 会捕获该异常并调用**该观察者自身**的 `handle_exception` 处理。默认实现把异常回溯打印到标准错误；子类可覆写以实现自定义策略（收集、上报或忽略）。若 `handle_exception` 自身再抛出异常，则由 hub 的 `handle_exception` 作为最终兜底。

## 事件分发机制

`Observer` 的事件**并非由节点逐个直接调用每个观察者**，而是通过 `ObserverHub` 广播：

- 节点持有 `ObserverHub`（`BaseTaskNode.observers`），通过 `add_observer()` 注册观察者；
- 节点在某事件发生时构造对应事件并调用 `hub.on_event(event)`，hub 再按注册顺序转发给每个观察者；
- 单个观察者回调抛出的异常由 hub 捕获，交给该观察者的 `handle_exception`，**不中断其他观察者的分发，也不逃逸到框架路径**。

内置观察者（也是 `Observer` 子类）：

| 类 | 所在文件 | 说明 |
|---|---------|------|
| `PrintObserver` | `core_print.py` | 基于 `print` 的控制台观察者 |
| `MetricsObserver` | `core_metrics.py` | 依据事件维护节点计数与状态的指标观察者 |
| `ObserverHub` | `core_hub.py` | 观察者分发中心，本身也是 `Observer` |
| `LifecycleObserver` / `LogObserver` | `persist` | 生命周期与日志观察者，由 `run_node_resources` / `run_graph_resources` 装配 |

## 使用示例

```python
from celestialflow.node import TaskExecutor
from celestialflow.observer import Event, Observer, TaskFailEvent, TaskSuccessEvent


class MyObserver(Observer):
    def on_event(self, event: Event) -> None:
        match event:
            case TaskSuccessEvent():
                print(f"{event.node} 成功: {event.result_repr}")
            case TaskFailEvent():
                print(f"{event.node} 失败: {event.exception}")


executor = TaskExecutor("Test", lambda x: x * 2)
executor.add_observer(MyObserver())
executor.run([1, 2, 3])
```

## 注意事项

1. **单一回调**：所有事件都从 `on_event` 进入；旧版的 `on_node_start` / `on_task_success` 等逐个回调已全部移除。
2. **`handle_exception` 不自动包装**：回调自身不能保证不抛异常——异常由 hub 捕获后转交本观察者的 `handle_exception`；它自身不会被 hub 再包装，但会被 hub 的 `handle_exception` 兜底。
3. **继承而不是实例化**：`Observer` 基类开放 `on_event`，实际使用通常继承它并覆写需要关心的分支。
