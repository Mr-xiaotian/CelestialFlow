# TaskStage

`TaskStage` 是构建 `TaskGraph` 的基本单元。它继承自 `TaskExecutor`，并增加了图结构相关的连接能力。

## 继承关系

`TaskExecutor` -> `TaskStage`

`TaskStage` 保留了 `TaskExecutor` 的所有执行能力（执行模式、重试、缓存等），并添加了节点间的连接逻辑。

## 关键概念

- **Next Stages**: 后续节点列表。当前节点的输出会进入后续节点的输入队列。
- **Prev Stages**: 前置节点列表。当前节点的输入来自前置节点的输出。
- **Stage Mode**: 节点在图中的运行模式。
  - `serial`: 串行模式，在主进程中运行。
  - `process`: 并行模式，在独立子进程中运行。

## 初始化

```python
class TaskStage(TaskExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ...
```

参数与 `TaskExecutor` 一致。主要区别在于 `TaskStage` 的 `execution_mode` 只能是 `thread` 或 `serial`（`process` 模式由 `stage_mode` 控制）。

## 图构建方法

### set_graph_context

设置节点在图中的上下文信息。

```python
def set_graph_context(
    self,
    next_stages: List[TaskStage] = None,
    stage_mode: str = None,
    stage_name: str = None,
):
    """
    设置链式上下文（仅限组成 graph 时）

    :param next_stages: 后续节点列表
    :param stage_mode: 当前节点执行模式，可以是 'serial'（串行）或 'process'（并行）
    :param stage_name: 当前节点名称
    """
```

示例：
```python
stage_a = TaskStage(func=process_a, execution_mode="thread")
stage_b = TaskStage(func=process_b, execution_mode="serial")

# 连接节点
stage_a.set_graph_context(
    next_stages=[stage_b],
    stage_mode="process",  # 在独立进程中运行
    stage_name="StageA"
)

stage_b.set_graph_context(
    next_stages=[],
    stage_mode="process",
    stage_name="StageB"
)
```

### 连接管理

```python
# 设置下游节点
def set_next_stages(self, next_stages: List[TaskStage]):
    """
    设置后续节点列表，并为后续节点添加本节点为前置节点。
    """

# 添加上游节点（通常由 set_next_stages 自动调用）
def add_prev_stages(self, prev_stage: TaskStage):
    """
    添加前置节点。
    会自动处理计数器的级联（如 split_counter）。
    """
```

### 模式设置

```python
# 设置节点运行模式
def set_stage_mode(self, stage_mode: str):
    """
    设置当前节点在 graph 中的执行模式。
    :param stage_mode: 'serial' 或 'process'
    """

# 获取节点运行模式
def get_stage_mode(self) -> str:
    """
    获取当前节点在 graph 中的执行模式。
    """
```

### 名称设置

```python
def set_stage_name(self, name: str = None):
    """
    设置当前节点名称。
    注意：名称变更后，标签（tag）会失效并重新生成。
    """
```

## 状态管理

`TaskStage` 使用 `StageStatus` 枚举管理运行状态：

- `NOT_STARTED` (0): 未启动
- `RUNNING` (1): 运行中
- `STOPPED` (2): 已停止

### 状态方法

```python
# 标记运行
def mark_running(self) -> None:
    """标记：stage 正在运行。"""

# 标记停止
def mark_stopped(self) -> None:
    """标记：stage 已停止（正常结束时在 finally 里调用）。"""

# 获取状态
def get_status(self) -> StageStatus:
    """读取当前状态（返回 StageStatus 枚举）。"""
```

## 运行机制

当 `TaskGraph` 启动时，每个 `TaskStage` 会根据 `stage_mode` 决定运行方式：

- **process 模式**: 节点被包装在一个独立 `Process` 中启动，与其他节点隔离。
- **serial 模式**: 节点在主进程中运行（通常用于调试）。

### start_stage

```python
def start_stage(
    self,
    input_queues: TaskInQueue,
    output_queues: TaskOutQueue,
    fail_queue: MPQueue,
    log_queue: MPQueue,
):
    """
    启动节点执行。

    :param input_queues: 输入队列
    :param output_queues: 输出队列
    :param fail_queue: 失败队列
    :param log_queue: 日志队列
    """
```

节点会持续从 `input_queues` 获取任务，执行（利用 `TaskExecutor` 的逻辑），并将结果放入 `output_queues`。

## 状态快照

```python
def get_summary(self) -> dict:
    """
    获取当前节点的状态快照。
    包括：name, func_name, class_name, execution_mode, stage_mode
    """
```

## 执行模式限制

在 `TaskStage` 中，`execution_mode` 的可用值受限：

```python
# 有效模式
valid_modes = ("thread", "serial")

# 注意：process 模式由 stage_mode 控制，不是 execution_mode
```

## 继承扩展

创建自定义 Stage 时，可以重写以下方法：

```python
class MyStage(TaskStage):
    def get_args(self, task):
        """自定义参数提取"""
        return (task.data,)

    def process_result(self, task, result):
        """自定义结果处理"""
        return {"data": result, "metadata": task.metadata}
```

## 注意事项

1. **进程模式**: `stage_mode="process"` 时，确保函数可 pickle（避免 lambda、嵌套函数等）。
2. **计数器级联**: 当上游是 `TaskSplitter` 或 `TaskRouter` 时，计数器会自动级联。
3. **状态共享**: 使用 `multiprocessing.Value` 实现，支持跨进程状态查询。
4. **标签唯一性**: 标签由 `名称[函数名]` 组成，用于日志追踪和图拓扑标识。