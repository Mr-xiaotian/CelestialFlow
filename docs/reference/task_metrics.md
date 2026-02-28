# TaskMetrics

TaskMetrics 模块负责管理和统计任务执行过程中的各项指标，如输入任务数、成功数、失败数、重复任务数等。它通常作为 `TaskExecutor` 的一个组件存在。

## 初始化

```python
class TaskMetrics:
    def __init__(self, executor: "TaskExecutor"):
        self.executor = executor
        # ...
```

- **executor**: 绑定的任务执行器实例。`TaskMetrics` 会直接操作 executor 中的计数器（如 `task_counter`, `success_counter` 等）。

## 计数器管理

TaskMetrics 提供了一系列方法来安全地更新计数器（通常在多线程/多进程环境下使用锁）。

- `update_task_counter()`: 增加输入任务计数。
- `update_success_counter()`: 增加成功任务计数。
- `update_error_counter()`: 增加失败任务计数。
- `update_duplicate_counter()`: 增加重复任务计数。

## 状态查询

### is_tasks_finished

判断所有输入的任务是否都已处理完毕（成功 + 失败 + 重复 == 输入）。

```python
def is_tasks_finished(self) -> bool: ...
```

### get_counts

获取当前所有指标的快照字典。

```python
def get_counts(self) -> dict:
    return {
        "tasks_input": int,       # 输入任务总数
        "tasks_successed": int,   # 成功任务数
        "tasks_failed": int,      # 失败任务数
        "tasks_duplicated": int,  # 重复任务数
        "tasks_processed": int,   # 已处理总数 (成功+失败+重复)
        "tasks_pending": int,     # 待处理任务数 (输入-已处理)
    }
```

## 任务去重

如果 `TaskExecutor` 启用了 `enable_duplicate_check`，TaskMetrics 会维护一个 `processed_set` 集合来记录已处理任务的哈希值。

- `is_duplicate(task_hash)`: 检查任务是否已存在。
- `add_processed_set(task_hash)`: 将任务哈希添加到已处理集合。
