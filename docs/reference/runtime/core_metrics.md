# TaskMetrics

TaskMetrics 模块负责管理和统计任务执行过程中的各项指标，如输入任务数、成功数、失败数、重复任务数等。它通常作为 `TaskExecutor` 的一个组件存在。

## 初始化

```python
class TaskMetrics:
    def __init__(
        self,
        execution_mode: str,
        max_retries: int = 1,
        enable_duplicate_check: bool = False,
    ):
        ...
```

- **execution_mode**: 任务执行模式，可选值为 `"thread"` 或 `"async"` 等。用于选择计数器的实现方式。
- **max_retries**: 最大重试次数，默认值为 1。
- **enable_duplicate_check**: 是否启用重复任务检查，默认值为 False。

## 计数器管理

TaskMetrics 提供了一系列方法来安全地更新计数器（通常在多线程/多进程环境下使用锁）。

### 初始化与重置

```python
def init_counter(self) -> None:
    """初始化计数器（按 execution_mode 选择实现）。"""

def reset_counter(self) -> None:
    """重置所有计数器为零。"""

def reset_state(self) -> None:
    """重置统计状态（清空重试时间记录和已处理任务集合）。"""
```

### 计数器操作

```python
def add_task_count(self, add_count: int = 1):
    """增加输入任务计数。"""

def add_success_count(self, count: int = 1):
    """线程安全地增加成功任务计数。"""

async def add_success_count_async(self, count: int = 1):
    """异步更新成功任务计数器。"""

def add_error_count(self, count: int = 1):
    """线程安全地增加失败任务计数。"""

def add_duplicate_count(self, count: int = 1):
    """线程安全地增加重复任务计数。"""
```

### 计数器级联

```python
def append_task_counter(self, counter) -> None:
    """添加外部计数器到任务总数计数器（用于跨 Stage 级联统计）。"""
```

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

### 单项查询

```python
def get_task_count(self) -> int:
    """获取当前的任务总数。"""

def get_success_count(self) -> int:
    """获取当前的成功任务数。"""

def get_error_count(self) -> int:
    """获取当前的失败任务数。"""

def get_duplicate_count(self) -> int:
    """获取当前的重复任务数。"""
```

## 任务去重

如果启用了 `enable_duplicate_check`，TaskMetrics 会维护一个 `processed_set` 集合来记录已处理任务的哈希值。

```python
def is_duplicate(self, task_hash: str) -> bool:
    """检查任务是否已存在。"""

def add_processed_set(self, task_hash: str) -> None:
    """将任务哈希添加到已处理集合。"""

def discard_processed_set(self, task_hash: str) -> None:
    """从已处理集合中移除任务（用于重试时重新允许处理）。"""
```

## 重试管理

TaskMetrics 管理任务的重试逻辑，包括可重试异常类型和重试次数跟踪。

### 异常配置

```python
def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """添加需要重试的异常类型。"""
```

### 重试判断

```python
def is_retry_able(self, task_hash: str, exception: Exception) -> bool:
    """
    检查任务是否可重试。
    基于异常类型和当前重试次数判断。
    """
```

### 重试计数

```python
def get_retry_time(self, task_hash: str) -> int:
    """获取任务的重试次数（不存在则返回 0）。"""

def add_retry_time(self, task_hash: str, retry_time: int = 1) -> int:
    """增加任务的重试次数，返回新的重试次数。"""

def pop_retry_time(self, task_hash: str) -> int | None:
    """弹出并返回任务的重试次数（成功或最终失败后调用）。"""
```

## 执行模式设置

```python
def set_execution_mode(self, execution_mode: str) -> None:
    """设置任务执行模式并重新初始化计数器。"""
```
