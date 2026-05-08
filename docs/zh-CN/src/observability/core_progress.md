# TaskProgress

> 📅 最后更新日期: 2026/05/08

`TaskProgress` 继承 `BaseObserver`，基于 `tqdm` 提供任务进度的可视化显示。

## 功能

- **动态更新**: 通过 `on_tasks_added` 支持动态增加总任务数，适应流式任务或任务分裂场景。
- **生命周期管理**: 在 `on_start` 时创建进度条，在 `on_finish` 时关闭。
- **事件驱动**: 通过 `on_task_success/fail/duplicate` 更新进度。

## 接口

```python
class TaskProgress(BaseObserver):
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
