# TaskMetrics

> 📅 最后更新日期: 2026/05/24

TaskMetrics 模块负责管理和统计任务执行过程中的各项指标，如输入任务数、成功数、失败数、重复任务数等。它通常作为 `TaskExecutor` 的一个组件存在。

## 初始化

```python
class TaskMetrics:
    def __init__(
        self,
        execution_mode: str,
        enable_duplicate_check: bool = False,
    ):
        """
        :param execution_mode: 任务执行模式，可选 "serial", "thread", "async"
        :param enable_duplicate_check: 是否启用重复任务检查，默认 False
        """
```

- **execution_mode**: 决定计数器的线程安全实现（thread 模式下使用 `Lock`）
- **enable_duplicate_check**: 控制是否维护 `processed_set` 用于去重

## 计数器管理

TaskMetrics 内部维护四个核心计数器：

| 计数器 | 类型 | 用途 |
|--------|------|------|
| `task_counter` | `SumCounter` | 总输入任务数（支持级联） |
| `success_counter` | `ValueWrapper` | 成功任务数 |
| `error_counter` | `ValueWrapper` | 失败任务数 |
| `duplicate_counter` | `ValueWrapper` | 重复任务数 |

在 `thread` 模式下，三个 `ValueWrapper` 共用同一把 `Lock`，减少锁开销。

### 初始化与重置

```python
def reset_counter(self) -> None:
    """重置所有计数器为零。"""

def reset_state(self) -> None:
    """重置统计状态（清空 processed_set）。"""
```

### 计数器操作

```python
def add_task_count(self, add_count: int = 1):
    """线程安全地增加输入任务计数。"""

def add_success_count(self, count: int = 1):
    """线程安全地增加成功任务计数。"""

def add_error_count(self, count: int = 1):
    """线程安全地增加失败任务计数。"""

def add_duplicate_count(self, count: int = 1):
    """线程安全地增加重复任务计数。"""
```

### 计数器级联

```python
def append_task_counter(self, counter: ValueWrapper) -> None:
    """添加外部计数器到 task_counter（用于跨 Stage 级联统计）。"""
```

级联用于 `TaskStage.prev_bindings()` — 每个下游节点将上游的成功计数器注册到自己的 `task_counter`，实现"上游产出 = 下游输入"的计数一致性。

## 状态查询

### is_tasks_finished

判断所有输入任务是否都已处理完毕。

```python
def is_tasks_finished(self) -> bool:
    """
    比较 task_counter.value 与 processed (success + error + duplicate) 是否相等。
    """
```

### get_counts

获取当前所有指标的快照字典。

```python
def get_counts(self) -> dict[str, int]:
    return {
        "tasks_input": int,       # 输入任务总数
        "tasks_succeeded": int,   # 成功任务数
        "tasks_failed": int,      # 失败任务数
        "tasks_duplicated": int,  # 重复任务数
        "tasks_processed": int,   # 已处理总数
        "tasks_pending": int,     # 待处理任务数
    }
```

### 单项查询

```python
def get_task_count(self) -> int: ...
def get_success_count(self) -> int: ...
def get_error_count(self) -> int: ...
def get_duplicate_count(self) -> int: ...
```

## 任务去重

当 `enable_duplicate_check=True` 时，维护 `processed_set: set[bytes]` 记录已处理任务的哈希值。

```python
def is_duplicate(self, task_hash: bytes) -> bool:
    """
    原子操作：检查并标记重复。
    - 如果哈希不在集合中，加入集合并返回 False
    - 如果已存在，返回 True
    """

def add_processed_set(self, task_hash: bytes) -> None:
    """将任务哈希加入已处理集合（仅当 enable_duplicate_check=True 时生效）。"""
```

## 重试管理

```python
def add_retry_exceptions(self, *exceptions: type[Exception]) -> None:
    """添加需要重试的异常类型。"""
```

异常类型以 `tuple` 形式存储在 `self.retry_exceptions` 中，`TaskDispatch._worker` 通过 `isinstance(exception, self.retry_exceptions)` 判断是否重试。

## 执行模式设置
## 使用示例

以下示例展示 `TaskMetrics` 的完整用法，包括初始化、计数器操作、去重检查、重试异常配置和状态查询。

```python
from celestialflow.runtime import TaskMetrics

# 1. 初始化指标管理器（开启去重检查）
metrics = TaskMetrics(
    execution_mode="serial",
    enable_duplicate_check=True,
)

# 2. 添加可重试异常类型
metrics.add_retry_exceptions(ConnectionError, TimeoutError)

# 3. 模拟任务处理过程
# 收到 5 个输入任务
metrics.add_task_count(5)

# 处理成功 3 个
metrics.add_success_count(3)

# 处理失败 1 个
metrics.add_error_count(1)

# 检测到重复任务 1 个
metrics.add_duplicate_count(1)

# 4. 查询各计数器的值
print(f"任务总数: {metrics.get_task_count()}")         # 5
print(f"成功数: {metrics.get_success_count()}")        # 3
print(f"失败数: {metrics.get_error_count()}")          # 1
print(f"重复数: {metrics.get_duplicate_count()}")      # 1

# 5. 获取完整快照字典
counts = metrics.get_counts()
print(f"已处理: {counts['tasks_processed']}")          # 3+1+1 = 5
print(f"待处理: {counts['tasks_pending']}")            # 0
print(f"全部完成: {metrics.is_tasks_finished()}")      # True

# 6. 去重检查示例（需要 enable_duplicate_check=True）
task_hash = b"\x00\x01\x02"
print(f"首次检查: {metrics.is_duplicate(task_hash)}")   # False（首次加入）
print(f"重复检查: {metrics.is_duplicate(task_hash)}")   # True（已存在）

# 7. 重置计数器
metrics.reset_counter()
print(f"重置后任务数: {metrics.get_task_count()}")      # 0

# 8. 切换执行模式（重新初始化线程安全策略）
metrics.set_execution_mode("thread")
print(f"新模式: {metrics.execution_mode}")
```

### 计数器级联

```python
from celestialflow.runtime import TaskMetrics
from celestialflow.runtime.util_types import ValueWrapper

# 创建主指标和子指标
parent_metrics = TaskMetrics(execution_mode="serial")
child_counter = ValueWrapper(value=10)

# 将子计数器级联到父级 task_counter
parent_metrics.append_task_counter(child_counter)
parent_metrics.add_task_count(5)  # 自己新增 5

print(f"总任务数 (5 + 10) : {parent_metrics.get_task_count()}")  # 15
```

### set_execution_mode

```python
def set_execution_mode(self, execution_mode: str) -> None:
    """设置任务执行模式并重新初始化计数器（切换线程安全策略）。"""
```
