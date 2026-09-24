# src/celestialflow/observability/core_observer_print.py

> 📅 最后更新日期: 2026/09/24

`core_observer_print.py` 提供了开箱即用的控制台观察者 `PrintObserver`。它继承 `BaseObserver`，把任务执行进度（启动、新增、成功、失败、重复、结束）以 `print` 输出到标准输出，便于本地调试与示例演示。

## PrintObserver

```python
from threading import Lock

from celestialflow.runtime.util_types import ValueWrapper
from celestialflow.observability.core_observer import BaseObserver


class PrintObserver(BaseObserver):
    def __init__(self, name: str) -> None: ...

    def on_start(self) -> None: ...
    def on_finish(self) -> None: ...
    def on_task_added(self, count: int) -> None: ...
    def on_task_success(self, count: int = 1) -> None: ...
    def on_task_fail(self, count: int = 1) -> None: ...
    def on_task_duplicate(self, count: int = 1) -> None: ...
```

### 构造参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | **必填**，输出前缀，用于区分不同节点的观察者（形如 `[name] ...`） |

构造函数内部会创建一把 `Lock`，并初始化四个线程安全的 `ValueWrapper` 计数器：

| 属性 | 类型 | 说明 |
|------|------|------|
| `total` | `ValueWrapper` | 已注入任务总数，由 `on_task_added` 累加 |
| `succeeded` | `ValueWrapper` | 成功任务数，由 `on_task_success` 累加 |
| `failed` | `ValueWrapper` | 失败任务数，由 `on_task_fail` 累加 |
| `duplicated` | `ValueWrapper` | 重复任务数，由 `on_task_duplicate` 累加 |
| `name` | `str` | 保存的输出前缀 |

### 回调行为

| 回调 | 行为 |
|------|------|
| `on_start()` | 打印 `[{name}] start total={total}` |
| `on_finish()` | 打印 `[{name}] finish total=..., succeeded=..., failed=..., duplicated=...` |
| `on_task_added(count)` | `total += count`，打印 `[{name}] total=...(+count)` |
| `on_task_success(count=1)` | `succeeded += count`，打印 `[{name}] succeeded=...(+count), total=...` |
| `on_task_fail(count=1)` | `failed += count`，打印 `[{name}] failed=...(+count), total=...` |
| `on_task_duplicate(count=1)` | `duplicated += count`，打印 `[{name}] duplicated=...(+count), total=...` |

> 所有计数均通过 `ValueWrapper` 在共享锁保护下读写，因此在 `thread` / `async` 执行模式下可安全调用。

## 使用示例

### 直接注册到节点

```python
from celestialflow import TaskExecutor, PrintObserver


def double(x: int) -> int:
    return x * 2


executor = TaskExecutor("Doubler", double, execution_mode="thread", max_workers=4)
executor.add_observer(PrintObserver("Doubler"))
executor.run([1, 2, 3])
# 控制台输出形如：
# [Doubler] total=3(+3)
# [Doubler] start total=3
# [Doubler] succeeded=1(+1), total=3
# ...
# [Doubler] finish total=3, succeeded=3, failed=0, duplicated=0
```

### 读取最终统计

```python
from celestialflow import TaskExecutor, PrintObserver


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

1. **`name` 为必填参数**：构造函数签名已改为 `__init__(self, name: str)`，不再允许无参构造。
2. **`total` 的口径**：`total` 仅统计经由 `put_task` / `run` 注入的任务。图模式下由上游节点下发的任务不会触发 `on_task_added`，因此非源节点的 `total` 会小于其实际处理量。
3. **回调顺序**：`run()` 会先注入全部任务再启动执行，因此 `on_task_added` 可能先于 `on_start` 到达。
4. **异常隔离**：回调中的异常由 `BaseObserver.__init_subclass__` 包装后交给 `observer_error()`，不会中断节点执行。
