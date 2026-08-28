# BaseObserver

> 📅 最后更新日期: 2026/08/26

`BaseObserver` 是执行器生命周期观察者的基类，定义了 `TaskExecutor` 在运行过程中会广播的事件接口。

## BaseObserver

```python
class BaseObserver:
    def on_start(self, _name: str, _total: int) -> None: ...
    def on_task_success(self, _count: int = 1) -> None: ...
    def on_task_fail(self, _count: int = 1) -> None: ...
    def on_task_duplicate(self, _count: int = 1) -> None: ...
    def on_tasks_added(self, _count: int) -> None: ...
    def on_finish(self) -> None: ...

    def observer_error(self, method_name: str, exception: Exception) -> None: ...
```

所有方法默认空实现（不是 ABC），子类按需覆写。

### 事件说明

| 事件 | 触发时机 | 参数 |
|------|----------|------|
| `on_start` | 执行器开始运行 | `_name`: 执行器全名, `_total`: 固定为 0（实际任务数通过 `on_tasks_added` 通知） |
| `on_task_success` | 单个任务成功 | `count`: 成功数量（默认 1） |
| `on_task_fail` | 单个任务失败 | `count`: 失败数量（默认 1） |
| `on_task_duplicate` | 检测到重复任务 | `count`: 重复数量（默认 1） |
| `on_tasks_added` | 新任务加入队列 | `count`: 新增任务数 |
| `on_finish` | 执行器结束运行 | 无 |
| `observer_error` | 观察者回调抛出异常时 | `method_name`: 异常回调名, `exception`: 捕获的异常 |

### 自动异常包装机制

`BaseObserver` 通过 `__init_subclass__` 在子类创建时自动包装所有覆写的回调方法（`on_start`、`on_task_success`、`on_task_fail`、`on_task_duplicate`、`on_tasks_added`、`on_finish`）：

- 包装器捕获回调中抛出的所有 `Exception`，调用 `observer_error(method_name, exception)` 后返回 `None`，异常不会逃逸到框架。
- 注意：`observer_error` 自身不会被包装，子类覆写它时若抛出异常会照常向外传播。

### 触发机制

事件并非通过统一的 `_notify()` 分发，而是由框架在具体位置直接调用：

- `TaskMetrics.on_start(name, total)` → 广播 `on_start`（由 `TaskExecutor._prepare_start()` 调用，`total` 固定传 `0`）
- `TaskMetrics.add_task_count(count)` → 广播 `on_tasks_added`
- `TaskMetrics.add_success_count(count)` / `add_fail_count(count)` / `add_duplicate_count(count)` → 分别广播对应回调
- `TaskMetrics.on_finish()` → 广播 `on_finish`

观察者通过 `executor.add_observer(observer)` 注册（内部存入 `TaskMetrics._observers`）。当 observer 列表为空时，广播循环为空操作。

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
executor.run([1, 2, 3])
```

### Observer 管理

```python
executor.add_observer(observer)  # 注册观察者
executor.remove_observer(observer)  # 移除观察者
```

## 已有实现

| 类 | 说明 |
|---|------|
| （无内置实现） | 用户可按需继承 `BaseObserver` 实现自定义观察者 |
