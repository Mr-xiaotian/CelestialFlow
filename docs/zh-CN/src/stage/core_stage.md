# TaskStage

> 📅 最后更新日期: 2026/05/23

`TaskStage` 是构建 `TaskGraph` 的基本单元。它继承自 `TaskExecutor`，并增加了图结构相关的连接能力与 `stage_mode` 控制逻辑。

## 继承关系

`TaskExecutor` -> `TaskStage`

`TaskStage` 继承了 `TaskExecutor` 的所有核心能力（执行模式、重试、指标监控等），并添加了节点间的连接逻辑。

## 核心概念

- **Stage Mode**: 节点在任务图中的调度逻辑模式。
  - `serial`: 串行模式，在主进程中运行。
  - `thread`: 线程模式，在主进程中以独立线程运行。
- **Execution Mode**: 节点内部处理任务的并发模式（`serial`, `thread`, `async`）。
- **拓扑关系**: 节点间的上下游连接关系由 `TaskGraph` 管理，`TaskStage` 自身不存储邻接表。

## 初始化

```python
class TaskStage(TaskExecutor):
    def __init__(
        self,
        name: str,
        func: Callable[..., Any],
        stage_mode: str = "serial",
        **kwargs: Any,
    ):
        """
        :param name: 节点名称（唯一标识）
        :param func: 执行函数
        :param stage_mode: 在图中的运行模式 ('serial' 或 'thread')
        :param kwargs: 透传给 TaskExecutor 的参数 (execution_mode, max_workers, max_retries 等)
        """
```

示例：
```python
stage_a = TaskStage("StageA", func=process_a, execution_mode="thread", stage_mode="thread")
stage_b = TaskStage("StageB", func=process_b, execution_mode="serial", stage_mode="thread")

# 创建图并连接节点
graph = TaskGraph()
graph.set_stages(stages=[stage_a, stage_b])
graph.connect([stage_a], [stage_b])
```

## 配置方法

### set_stage_mode

```python
def set_stage_mode(self, stage_mode: str):
    """
    设置节点在任务图中的执行模式。
    :param stage_mode: 'serial' 或 'thread'
    :raises StageModeError: 如果模式不支持
    """
```

### set_execution_mode

```python
def set_execution_mode(self, execution_mode: str):
    """
    设置节点内部的任务处理模式。

    :param execution_mode: 'serial', 'thread' 或 'async'
    :raises ExecutionModeError: 如果模式不支持
    """
```

### set_name

```python
def set_name(self, name: str):
    """
    设置节点名称。
    """
```

## 状态管理

`TaskStage` 使用 `StageStatus` 枚举维护生命周期：

- `NOT_STARTED` (0): 初始状态。
- `RUNNING` (1): 已启动，正在监听队列。
- `STOPPED` (2): 已正常停止或异常退出。

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

- **thread 模式**: 节点在独立线程中启动。
- **serial 模式**: 节点在主进程中串行运行（通常用于调试）。

### start_stage

当 `TaskGraph` 启动时，会调用此方法启动节点。

```python
def start_stage(
    self,
    input_queue: TaskInQueue,
    output_queue: TaskOutQueue,
    fail_queue: ThreadQueue[Any],
    log_queue: ThreadQueue[Any],
):
    """
    启动节点执行，根据 execution_mode 选择调度器。

    :param input_queue: 输入队列
    :param output_queue: 输出队列
    :param fail_queue: 失败队列
    :param log_queue: 日志队列
    """
```

1. 初始化环境（`Inlet`, `Queue`）。
2. 记录启动日志。
3. 标记状态为 `RUNNING`。
4. 进入 `TaskDispatch` 循环处理任务。
5. 完成后清理资源并标记 `STOPPED`。

## 状态快照

```python
def get_summary(self) -> dict[str, Any]:
    """
    获取当前节点的状态摘要。
    返回包含 class_name, name, func_name, execution_mode, stage_mode 的字典。
    """
```

## 执行模式限制

在 `TaskStage` 中，`execution_mode` 的可用值受限：

```python
# 有效模式
valid_modes = ("serial", "thread", "async")

# 注意：stage_mode 和 execution_mode 是独立的配置
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

1. **名称唯一性**: 在同一个 `TaskGraph` 中，每个 `TaskStage` 的 `name` 必须唯一，否则会抛出 `DuplicateNodeError`。
2. **异步支持**: 如果 `execution_mode` 设置为 `async`，则 `func` 必须是一个协程函数。
3. **资源清理**: 节点停止时会自动释放客户端连接和闭包资源。
