# TaskStage

`TaskStage` 是构建 `TaskGraph` 的基本单元。它继承自 `TaskExecutor`，并增加了图结构相关的连接能力。

## 继承关系

`TaskExecutor` -> `TaskStage`

`TaskStage` 保留了 `TaskExecutor` 的所有执行能力（执行模式、重试、缓存等），并添加了节点间的连接逻辑。

## 关键概念

- **Next Stages**: 后续节点列表。当前节点的输出会进入后续节点的输入队列。
- **Prev Stages**: 前置节点列表。当前节点的输入来自前置节点的输出。
- **Stage Mode**: 节点在图中的运行模式。
  - `serial`: 串行模式（通常指在当前进程/线程中顺序执行，但在 Graph 中较少见，除非是纯串行链）。
  - `process`: 并行模式。在 `TaskGraph` 中，每个设置为 `process` 模式的 Stage 都会在一个独立的子进程中运行。

## 初始化

```python
class TaskStage(TaskExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ...
```

参数与 `TaskExecutor` 一致。

## 图构建方法

通常不由用户直接调用，而是通过 `TaskChain`, `TaskCross` 等结构自动调用，或者手动构建图时使用。

### set_graph_context

设置节点在图中的上下文信息。

```python
def set_graph_context(
    self,
    next_stages: List[TaskStage] = None,
    stage_mode: str = None,
    stage_name: str = None,
):
    ...
```

### 连接管理

- `set_next_stages(stages)`: 设置下游。
- `add_prev_stages(stage)`: 添加上游。会自动处理计数器的级联（如 `split_counter`）。

## 运行机制

当 `TaskGraph` 启动时，每个 `TaskStage`（如果是 `process` 模式）会被包装在一个 `Process` 中启动。
它会持续从 `input_queues` 获取任务，执行（利用 `TaskExecutor` 的逻辑），并将结果放入 `output_queues`。
