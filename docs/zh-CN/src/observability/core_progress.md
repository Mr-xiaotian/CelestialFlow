# TaskProgress

> 📅 最后更新日期: 2026/06/11

`TaskProgress` 继承 `BaseObserver`，基于 `tqdm` 提供任务进度的可视化显示。

## 功能

- **动态更新**: 通过 `on_tasks_added` 支持动态增加总任务数，适应流式任务或任务分裂场景。
- **生命周期管理**: 在 `on_start` 时创建进度条，在 `on_finish` 时关闭。
- **事件驱动**: 通过 `on_task_success/fail/duplicate` 更新进度。

## 接口

```python
class TaskProgress(BaseObserver):
    _bar: tqdm[Any]

    def on_start(self, name: str, total: int) -> None:
        # 创建 tqdm 进度条
    def on_task_success(self, count: int = 1) -> None:
        # 更新进度
    def on_task_fail(self, count: int = 1) -> None:
        # 更新进度
    def on_task_duplicate(self, count: int = 1) -> None:
        # 更新进度
    def on_tasks_added(self, count: int) -> None:
        # 增加总任务数并刷新
    def on_finish(self) -> None:
        # 关闭进度条
```

## 使用

```python
from celestialflow import TaskExecutor, TaskProgress

executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)
```

不需要进度条时，不添加 observer 即可，无需 Null 实现。

## 使用示例

### TaskProgress 与 TaskExecutor 配合使用

```python
from celestialflow import TaskExecutor, TaskProgress


def slow_task(n: int) -> int:
    """模拟一个耗时任务"""
    import time
    time.sleep(0.05)
    return n * n


# 1. 创建执行器，线程模式运行
executor = TaskExecutor(
    "计算平方",
    slow_task,
    execution_mode="thread",
    max_workers=10,
)

# 2. 添加进度条观察者
executor.add_observer(TaskProgress())

# 3. 启动执行器处理 100 个任务
executor.start(range(100))
print("所有任务已完成！")
```

### 动态添加任务的进度条

当任务在运行过程中可能动态增多时（如任务分裂场景），`TaskProgress` 会自动扩展进度条总量：

```python
from celestialflow import TaskExecutor, TaskProgress


def dynamic_task(n: int) -> list[int]:
    """根据输入值动态产生新任务"""
    if n % 10 == 0:
        return [n + 1, n + 2]
    return [n]


executor = TaskExecutor("动态任务", dynamic_task, execution_mode="thread")

progress = TaskProgress()
executor.add_observer(progress)

# 初始 20 个任务，运行中会动态增加
executor.start(range(20))
```
