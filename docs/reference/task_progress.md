# TaskProgress

TaskProgress 模块基于 `tqdm` 提供了任务进度的可视化显示。

## 功能

- **动态更新**: 支持动态增加总任务数 (`add_total`)，适应流式任务或任务分裂场景。
- **多模式支持**: 
  - 普通模式: 使用标准 `tqdm`。
  - 异步模式: 使用 `tqdm.asyncio`，适用于 `async` 执行模式。
- **Null模式**: `NullTaskProgress` 用于关闭进度条显示时的空实现，避免代码中充斥 `if show_progress` 判断。

## 使用

在 `TaskExecutor` 或 `TaskStage` 中初始化：

```python
self.task_progress = TaskProgress(
    total_tasks=0,  # 初始通常为0，随任务输入动态增加
    desc="Processing",
    mode="normal"
)
```

更新进度：

```python
self.task_progress.update(1)
```

动态增加总数：

```python
self.task_progress.add_total(100)
```
