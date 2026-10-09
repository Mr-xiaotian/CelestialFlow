# src/celestialflow/observer/core_hub.py

> 📅 最后更新日期: 2026/10/09

`core_hub.py` 定义了观察者**分发中心** `ObserverHub`。它本身也是 `Observer`，将收到的每个事件按注册顺序转发给已注册的观察者。它是节点与各下游观察者之间的广播枢纽。

## ObserverHub

```python
class ObserverHub(Observer):
    def __init__(self) -> None: ...

    def add_observer(self, observer: Observer) -> None: ...

    # 继承 Observer 的 12 个事件回调 + handle_exception
    def on_node_start(self, event: NodeStartEvent) -> None: ...
    def on_node_end(self, event: NodeEndEvent) -> None: ...
    # ... 依次对每个事件向所有观察者转发 ...
    def on_graph_start(self, event: GraphStartEvent) -> None: ...
    def on_graph_end(self, event: GraphEndEvent) -> None: ...
```

每个事件回调（`on_*`）的转发语义一致：遍历当前观察者快照，对每个观察者调用对应回调；若某观察者的回调抛出异常，交给该观察者自身的 `handle_exception` 处理；若 `handle_exception` 自身再抛异常，则由 hub 自身的 `handle_exception` 作为最终兜底。两种情况都不会中断其余观察者的分发，也不会逃逸到框架执行路径。

## 注册与写时复制

观察者列表采用 **copy-on-write（写时复制）**：

- 写入方通过 `add_observer()` 在 `_write_lock` 保护下，用新的不可变元组整体替换 `_observers`；
- 读路径 `_snapshot()` 直接返回当前引用，不加锁也不拷贝；
- 由于元组不可变、且 CPython 对属性读取与替换不会撕裂，读到的永远是某个完整版本的快照，迭代期间无需担心并发修改。

```python
def add_observer(self, observer: Observer) -> None:
    self._reject_cycle(observer)
    with self._write_lock:
        self._observers = (*self._observers, observer)
```

### 循环引用拒绝

`add_observer` 会先调用 `_reject_cycle`，拒绝会形成 hub 循环引用的注册（避免分发时无限递归）：

- 若 `observer is self`，抛 `ConfigurationError`；
- 若 `observer` 是 `ObserverHub`，会沿其观察者树 DFS 检查是否（直接或间接）已持有当前 hub，是则抛 `ConfigurationError`。

## 使用示例

```python
from celestialflow.observer import (
    Observer,
    ObserverHub,
    MetricsObserver,
    TaskSuccessEvent,
)


class MyObserver(Observer):
    def on_task_success(self, event: TaskSuccessEvent) -> None:
        print(f"{event.node} 成功: {event.result_repr}")


hub = ObserverHub()
hub.add_observer(MyObserver())
hub.add_observer(MetricsObserver())
```

## 装配场景

节点的观察者 hub 由 `BaseTaskNode` 持有。在装配（`assembly/core_run.py`）阶段：

- `MetricsObserver` 被注册为写模型；
- `LifecycleInlet` / `LogInlet`（来自 `persist` 模块）被注册，消费事件落盘；
- 启用上报时 `PushSnapshotHandler` / `PushInlet` 也会被注册。

这些均通过 `observers.add_observer(...)` 挂入同一 hub，节点只向 `hub.on_*()` 广播，感知不到具体观察者细节。

## 注意事项

1. **线程安全**：`add_observer` 可在运行期调用，读取侧无需加锁即可安全迭代快照。
2. **异常不逃逸**：单个观察者的异常被隔离在 hub 内，不会中断同批其他观察者，也不会返回给节点执行路径。
3. **本身也是 Observer**：`ObserverHub` 继承 `Observer`，可被注册进另一个 hub（也正因如此需要循环检测）。