# BaseObserver / CallbackObserver

> 📅 最后更新日期: 2026/05/28

`BaseObserver` 是执行器生命周期观察者的基类，定义了 `TaskExecutor` 在运行过程中会广播的事件接口。`CallbackObserver` 是轻量级实现，通过回调函数接收事件。

## BaseObserver

```python
class BaseObserver:
    def on_start(self, _name: str, _total: int) -> None: ...
    def on_task_success(self, _count: int = 1) -> None: ...
    def on_task_fail(self, _count: int = 1) -> None: ...
    def on_task_duplicate(self, _count: int = 1) -> None: ...
    def on_tasks_added(self, _count: int) -> None: ...
    def on_finish(self) -> None: ...
```

所有方法默认空实现（不是 ABC），子类按需覆写。

### 事件说明

| 事件 | 触发时机 | 参数 |
|------|----------|------|
| `on_start` | 执行器开始运行 | `_name`: 执行器名称, `_total`: 初始任务总数 |
| `on_task_success` | 单个任务成功 | `count`: 成功数量（默认 1） |
| `on_task_fail` | 单个任务失败 | `count`: 失败数量（默认 1） |
| `on_task_duplicate` | 检测到重复任务 | `count`: 重复数量（默认 1） |
| `on_tasks_added` | 新任务加入队列 | `count`: 新增任务数 |
| `on_finish` | 执行器结束运行 | 无 |

### 使用方式

```python
from celestialflow import BaseObserver, TaskExecutor

class MyObserver(BaseObserver):
    def on_task_success(self, count=1):
        print(f"成功: {count}")

    def on_task_fail(self, count=1):
        print(f"失败: {count}")

executor = TaskExecutor("Test", my_func)
executor.add_observer(MyObserver())
executor.start(tasks)
```

### Observer 管理

```python
executor.add_observer(observer)     # 注册观察者
executor.remove_observer(observer)  # 移除观察者
```

执行器内部通过 `_notify(method_name, *args, **kwargs)` 向所有已注册的观察者广播事件。当 observer 列表为空时，等效于无观察者（不需要 Null 实现）。

## CallbackObserver

轻量级观察者，通过关键字参数传入回调函数，无需定义子类。

```python
class CallbackObserver(BaseObserver):
    def __init__(self, **callbacks):
        for name, fn in callbacks.items():
            setattr(self, name, fn)
```

### 使用方式

```python
from celestialflow import CallbackObserver, TaskExecutor

observer = CallbackObserver(
    on_task_success=lambda count=1: print(f"成功: {count}"),
    on_finish=lambda: print("完成"),
)

executor = TaskExecutor("Test", my_func)
executor.add_observer(observer)
executor.start(tasks)
```

只需覆写关心的事件，其余走 `BaseObserver` 的默认空实现。

## 已有实现

| 类 | 说明 |
|---|------|
| `TaskProgress` | 基于 tqdm 的进度条显示（见 `core_progress.md`） |
| `CallbackObserver` | 回调函数式观察者 |
