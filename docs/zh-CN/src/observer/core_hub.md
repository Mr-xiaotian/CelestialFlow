# src/celestialflow/observer/core_hub.py

> 📅 最后更新日期: 2026/11/13

`core_hub.py` 定义了观察者**分发中心** `ObserverHub`。它本身也是 `Observer`，将收到的每个事件按注册顺序转发给已注册的观察者，并提供按类型查找观察者的 `find()`。它是节点与各下游观察者之间的广播枢纽。

## ObserverHub

```python
class ObserverHub(Observer):
    def __init__(self) -> None: ...

    def add_observer(self, observer: Observer) -> None: ...

    def find[O: Observer](self, observer_type: type[O]) -> O | None: ...

    def on_event(self, event: Event) -> None: ...
```

## 事件分发

`on_event` 遍历当前观察者快照，对每个观察者调用 `observer.on_event(event)`。若某观察者的回调抛出异常，交给该观察者自身的 `handle_exception` 处理；若 `handle_exception` 自身再抛异常，则由 hub 自身的 `handle_exception` 作为最终兜底。两种情况都不会中断其余观察者的分发，也不会逃逸到框架执行路径。

```python
def on_event(self, event: Event) -> None:
    for observer in self._snapshot():
        try:
            observer.on_event(event)
        except Exception as exception:
            try:
                observer.handle_exception(exception)
            except Exception as fallback:
                self.handle_exception(fallback)
```

> 由于只有一个 `on_event` 入口，新增事件类型无需改动 hub：所有观察者都会收到全部事件，再各自按 `match` 分支处理。

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

## 按类型查找观察者

```python
def find[O: Observer](self, observer_type: type[O]) -> O | None:
```

查找规则：

1. 先扫描**本层**直接注册的观察者，返回第一个 `isinstance` 匹配者（因此子类实例同样命中）；
2. 本层未命中时，按注册顺序递归进入嵌套 `ObserverHub` 查找；
3. 全部未命中返回 `None`。

因此**越靠近调用方的注册越优先**。

典型用途是节点在结果读取时定位生命周期观察者：独立运行时 `LifecycleObserver` 直接注册在节点 hub 上，图级调度时它位于图级 hub，`find` 会递归命中两者：

```python
from celestialflow.persist import LifecycleObserver

lifecycle = node.observers.find(LifecycleObserver)
db_path = lifecycle.db_path if lifecycle is not None else None
```

## 使用示例

### 注册与广播

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

### 嵌套 hub 与 find

```python
from celestialflow.observer import ObserverHub
from celestialflow.persist import LifecycleObserver

graph_hub = ObserverHub()
graph_hub.add_observer(LifecycleObserver())

node_hub = ObserverHub()
node_hub.add_observer(graph_hub)  # 节点共享图级观察者

found = node_hub.find(LifecycleObserver)
print(found is not None)  # True，find 会递归进入 graph_hub
```

## 装配场景

节点的观察者 hub 由 `BaseTaskNode` 持有，并通常嵌套图级 hub。在装配（`assembly/core_run.py`）阶段：

- `MetricsObserver` 被注册为写模型；
- `LifecycleObserver` / `LogObserver`（来自 `persist` 模块）被注册，自身再驱动 `LifecycleInlet` / `LogInlet` 与 spout 完成落盘；
- 启用上报时 `PushSnapshotHandler` / `PushInlet` 也会被注册。

这些均通过 `observers.add_observer(...)` 挂入 hub，节点只向 `hub.on_event(...)` 广播，感知不到具体观察者细节。

## 注意事项

1. **线程安全**：`add_observer` 可在运行期调用，读取侧无需加锁即可安全迭代快照。
2. **异常不逃逸**：单个观察者的异常被隔离在 hub 内，不会中断同批其他观察者，也不会返回给节点执行路径。
3. **本身也是 Observer**：`ObserverHub` 继承 `Observer`，可被注册进另一个 hub（也正因如此需要循环检测）。
4. **`find` 的优先级**：先本层后嵌套层；同名类型的多个实例只返回第一个命中的。
