# src/celestialflow/observer/core_observer_print.py

> 📅 最后更新日期: 2026/10/09

`core_observer_print.py` 提供了开箱即用的控制台观察者 `PrintObserver`。它继承 `Observer`，把任务执行进度（启动、输入、成功、失败、跳过、结束）以 `print` 输出到标准输出，便于本地调试与示例演示。

## PrintObserver

```python
class PrintObserver(Observer):
    def __init__(self, name: str) -> None: ...

    def on_node_start(self, event: NodeStartEvent) -> None: ...
    def on_node_end(self, event: NodeEndEvent) -> None: ...
    def on_task_input(self, event: TaskInputEvent) -> None: ...
    def on_task_success(self, event: TaskSuccessEvent) -> None: ...
    def on_task_fail(self, event: TaskFailEvent) -> None: ...
    def on_task_skip(self, event: TaskSkipEvent) -> None: ...
```

### 构造参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | **必填**，输出前缀，用于区分不同节点的观察者（形如 `[name] ...`） |

构造函数内部会创建一把 `Lock`，并初始化四个线程安全的 `ValueWrapper` 计数器：

| 属性 | 类型 | 说明 |
|------|------|------|
| `total` | `ValueWrapper` | 已进入当前节点的任务总数（外部注入 + 上游下发），由 `on_task_input` 累加 |
| `succeeded` | `ValueWrapper` | 成功任务数，由 `on_task_success` 累加 |
| `failed` | `ValueWrapper` | 失败任务数，由 `on_task_fail` 累加 |
| `skipped` | `ValueWrapper` | 跳过任务数，由 `on_task_skip` 累加 |
| `name` | `str` | 保存的输出前缀 |

### 回调行为

| 回调 | 行为 |
|------|------|
| `on_node_start(event)` | 打印 `[{name}] start total={total}` |
| `on_node_end(event)` | `total += ...`，打印 `[{name}] finish total=..., skipped=..., succeeded=..., failed=...` |
| `on_task_input(event)` | `total += 1`，打印 `[{name}] total=...(+1)` |
| `on_task_success(event)` | `succeeded += 1`，打印 `[{name}] succeeded=...(+1), total=...` |
| `on_task_fail(event)` | `failed += 1`，打印 `[{name}] failed=...(+1), total=...` |
| `on_task_skip(event)` | `skipped += 1`，打印 `[{name}] skipped=...(+1), total=...` |

> 所有计数均通过 `ValueWrapper` 在共享锁保护下读写，因此在 `thread` / `async` 执行模式下可安全调用。

## 使用示例

### 直接注册到节点的观察者 hub

```python
from celestialflow.node import TaskExecutor
from celestialflow.observer import PrintObserver


def double(x: int) -> int:
    return x * 2


executor = TaskExecutor("Doubler", double, execution_mode="thread", max_workers=4)
executor.add_observer(PrintObserver("Doubler"))
executor.run([1, 2, 3])
# 控制台输出形如：
# [Doubler] total=3(+1)
# [Doubler] start total=3
# [Doubler] succeeded=1(+1), total=3
# ...
# [Doubler] finish total=3, skipped=0, succeeded=3, failed=0
```

### 读取最终统计

```python
from celestialflow.node import TaskExecutor
from celestialflow.observer import PrintObserver


def may_fail(x: int) -> int:
    if x % 2 == 0:
        raise ValueError(f"bad {x}")
    return x


executor = TaskExecutor("Odd", may_fail)
observer = PrintObserver("Odd")
executor.add_observer(observer)
executor.run([1, 2, 3, 4])

print(observer.succeeded.get(), observer.failed.get())
```

## 注意事项

1. **`name` 为必填参数**：构造函数签名为 `__init__(self, name: str)`，必须传入输出前缀。
2. **`total` 的口径**：`total` 统计所有进入当前节点的任务，**包含**外部注入与上游下发的任务（由 `on_task_input` 累加）。
3. **回调参数为事件对象**：与旧版基于 `count` 基本参数的观察者不同，所有回调都接收 `core_event.py` 中对应的只读事件 `dataclass`。
4. **异常隔离**：回调中的异常由 `ObserverHub` 捕获并交给该观察者的 `handle_exception`，不会中断节点执行。