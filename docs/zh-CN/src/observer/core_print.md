# src/celestialflow/observer/core_print.py

> 📅 最后更新日期: 2026/11/13

`core_print.py` 提供了开箱即用的控制台观察者 `PrintObserver`。它继承 `Observer`，在统一的 `on_event` 中按事件类型更新计数，并把任务执行进度（启动、输入、成功、失败、跳过、结束）以 `print` 输出到标准输出，便于本地调试与示例演示。

## PrintObserver

```python
class PrintObserver(Observer):
    def __init__(self, name: str) -> None: ...

    def on_event(self, event: Event) -> None: ...
```

### 构造参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | **必填**，输出前缀，用于区分不同节点的观察者（形如 `[name] ...`） |

构造函数内部会创建一把 `Lock`，并让四个线程安全的 `ValueWrapper` 计数器共享它：

| 属性 | 类型 | 说明 |
|------|------|------|
| `total` | `ValueWrapper` | 已进入当前节点的任务总数（外部注入 + 上游下发），由 `TaskInputEvent` 累加 |
| `succeeded` | `ValueWrapper` | 成功任务数，由 `TaskSuccessEvent` 累加 |
| `failed` | `ValueWrapper` | 失败任务数，由 `TaskFailEvent` 累加 |
| `skipped` | `ValueWrapper` | 跳过任务数，由 `TaskSkipEvent` 累加 |
| `name` | `str` | 保存的输出前缀 |

### 事件处理

`on_event` 用 `match` 分派；`TaskRetryEvent`、终止信号事件、图级事件等均落入 `case _: pass`，既不计数也不打印。

| 事件 | 行为 |
|------|------|
| `NodeStartEvent` | 打印 `[{name}] start total={total}` |
| `NodeEndEvent` | 打印 `[{name}] finish total=..., skipped=..., succeeded=..., failed=...`（不修改任何计数器） |
| `TaskInputEvent` | `total += 1`，打印 `[{name}] total=...(+1)` |
| `TaskSuccessEvent` | `succeeded += 1`，打印 `[{name}] succeeded=...(+1), total=...` |
| `TaskFailEvent` | `failed += 1`，打印 `[{name}] failed=...(+1), total=...` |
| `TaskSkipEvent` | `skipped += 1`，打印 `[{name}] skipped=...(+1), total=...` |

> 所有计数均通过共享同一把锁的 `ValueWrapper` 读写，因此在 `thread` / `async` 执行模式下可安全调用。

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
# [Doubler] total=1(+1)
# [Doubler] total=2(+1)
# [Doubler] total=3(+1)
# [Doubler] start total=3
# [Doubler] succeeded=1(+1), total=3
# ...
# [Doubler] finish total=3, skipped=0, succeeded=3, failed=0
```

> 节点在 `run()` 中先经 `put_task()` 注入任务再启动，因此 `NodeStartEvent` 打印的 `total` 已包含启动前注入的任务数；终止信号由 `put_signal()` 发出的是 `TerminationInputEvent`，不计入 `total`。

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

### 手动投递事件

```python
from celestialflow.observer import PrintObserver, TaskInputEvent, TaskSuccessEvent

observer = PrintObserver("Manual")
observer.on_event(
    TaskInputEvent(node="Manual", task="x", task_repr="'x'", input_id=1)
)
observer.on_event(
    TaskSuccessEvent(
        node="Manual",
        task="x",
        task_repr="'x'",
        result="xx",
        result_repr="'xx'",
        elapsed=0.01,
        task_id=1,
        success_id=2,
    )
)
print(observer.total.get(), observer.succeeded.get())  # 1 1
```

## 注意事项

1. **`name` 为必填参数**：构造函数签名为 `__init__(self, name: str)`，必须传入输出前缀。
2. **`total` 的口径**：`total` 统计所有进入当前节点的任务，**包含**外部注入与上游下发的任务（由 `TaskInputEvent` 累加）。
3. **单一事件入口**：只覆写 `on_event`，通过 `match` 分派；不再存在 `on_node_start` / `on_task_success` 等逐个回调。
4. **异常隔离**：`on_event` 中的异常由 `ObserverHub` 捕获并交给该观察者的 `handle_exception`，不会中断节点执行。
