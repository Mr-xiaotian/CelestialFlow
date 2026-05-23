# TaskGraph

> 📅 最后更新日期: 2026/05/23

`TaskGraph` 是 CelestialFlow 的核心调度器，负责管理一组 `TaskStage` 节点的依赖关系、执行流程、资源分配和生命周期。

## 初始化

```python
class TaskGraph:
    def __init__(
        self,
        schedule_mode: str = "eager",
        log_level: str = "INFO",
    ):
        ...
```

### 参数说明

- **schedule_mode**: 调度模式。
  - `eager` (默认): 所有节点一次性启动，依赖关系通过数据流自动控制。适用于最大化并行度。
  - `staged`: 分层执行。仅适用于 DAG。按层级顺序逐层启动，上一层全部完成后才启动下一层。
- **log_level**: 全局日志级别（TRACE/DEBUG/INFO/SUCCESS/WARNING/ERROR/CRITICAL），默认为 `"INFO"`。

### 设置节点

```python
def set_stages(self, stages: list[TaskStage]):
    """
    设置任务图的节点。
    
    :param stages: 所有节点列表。
    """
```

## 核心功能

### 图构建与分析

- **自动构建**: 根据节点列表和节点间的连接关系, 自动遍历并构建整个图结构。
- **源节点自动计算**: 自动识别源节点（无入边的节点）。
- **DAG 检测**: 自动检测是否为有向无环图 (DAG)。
- **分层分析**: 如果是 DAG，会自动计算节点的层级，用于 `staged` 调度或可视化展示。

### 启动运行

```python
def start_graph(self, init_tasks_dict: dict[str, Iterable[Any]], put_termination_signal: bool = True):
    """
    启动任务图。
    
    :param init_tasks_dict: 初始任务数据，格式为 {stage_name: [task_data, ...]}
    :param put_termination_signal: 是否在初始任务后自动注入终止信号。
    """
```

示例：
```python
graph = TaskGraph(schedule_mode="eager")
graph.set_stages(stages=[stage_a, stage_b])
graph.start_graph({
    stage_a.get_name(): [1, 2, 3, 4, 5]
})
```

### 资源管理

- **队列管理**: 自动创建节点间的通信队列 (`TaskInQueue`, `TaskOutQueue`)。
- **优雅退出**: 确保所有节点在任务完成后正确退出。

### 监控与报告

- **运行时快照**: `collect_runtime_snapshot()` 收集每个节点的运行状态。
- **错误持久化**: 将运行时的错误日志持久化到本地 JSONL 文件 (`fallback/` 目录)。
- **Web 上报**: 集成 `TaskReporter`，将状态实时推送给 Web UI。

## 配置方法

### set_reporter

```python
def set_reporter(self, is_report: bool = False, host: str = "127.0.0.1", port: int = 5000):
    """
    设定报告器，用于向 Web UI 推送状态。

    :param is_report: 是否启用报告器
    :param host: Web 服务主机地址
    :param port: Web 服务端口
    """
```

### set_ctree

```python
def set_ctree(
    self,
    use_ctree: bool = False,
    host: str = "127.0.0.1",
    http_port: int = 7777,
    grpc_port: int = 7778,
    transport: str = "grpc",
):
    """
    设定 CelestialTree 客户端，用于事件追踪。

    :param use_ctree: 是否使用 CelestialTree
    :param host: 服务主机地址
    :param http_port: HTTP 端口
    :param grpc_port: gRPC 端口
    :param transport: 传输协议
    """
```

### set_graph_mode

```python
def set_graph_mode(self, stage_mode: str, execution_mode: str):
    """
    批量设置所有节点的运行模式。
    
    :param stage_mode: 节点运行模式 ('serial' 或 'thread')
    :param execution_mode: 节点内部执行模式 ('serial'、'thread' 或 'async')
    """
```

## 数据查询方法

### 状态查询

```python
# 获取节点状态字典
def get_status_dict(self) -> dict[str, dict[str, Any]]:
    """返回每个节点的实时状态。"""

# 获取图摘要
def get_graph_summary(self) -> dict[str, Any]:
    """返回全局统计（成功数、失败数、积压数等）。"""
```

### 错误查询

```python
# 按阶段获取失败任务
def get_fail_by_stage_dict(self) -> dict[str, list[Any]]:
    """返回 {stage_name: [failed_tasks]} 格式的字典。"""

# 按错误类型获取失败任务
def get_fail_by_error_dict(self) -> dict[str, list[Any]]:
    """返回 {error_type: [failed_tasks]} 格式的字典。"""
```

## 任务注入

### put_stage_queue

```python
def put_stage_queue(self, tasks_dict: dict[str, Iterable[Any]], put_termination_signal: bool = True):
    """
    动态向节点队列注入任务。

    :param tasks_dict: {stage_name: [tasks]}
    :param put_termination_signal: 是否注入终止信号
    """
```

示例：
```python
# 动态注入任务
graph.put_stage_queue({
    stage_a.get_tag(): [6, 7, 8]
})

# 注入终止信号
from celestialflow import TerminationSignal
graph.put_stage_queue({
    stage_a.get_tag(): [TerminationSignal()]
})
```


## 调度模式详解

### Eager 模式

- 所有节点立即启动
- 依赖关系通过队列流自动控制
- 最大化并行度
- 适用于大多数场景

### Staged 模式

- 按层级顺序逐层执行
- 上层全部完成后才启动下一层
- 仅适用于 DAG
- 适用于调试、性能分析、资源控制

## 注意事项

1. **非 DAG 图**: 对于有环图，注入终止信号可能导致死锁或提前退出，建议手动控制。
2. **未消费任务**: 停止时会收集所有队列中未消费的任务并记录为 `UnconsumedError`。
3. **Web 监控**: 需要先启动 Web 服务，再设置 `set_reporter(True)`。

## 示例

```python
from celestialflow import TaskStage, TaskGraph

# 创建节点
stage_a = TaskStage("A", func=process_a, execution_mode="thread", stage_mode="thread")
stage_b = TaskStage("B", func=process_b, execution_mode="serial", stage_mode="thread")
stage_c = TaskStage("C", func=process_c, execution_mode="serial", stage_mode="thread")

# 构建图
graph = TaskGraph(schedule_mode="eager", log_level="INFO")
graph.set_stages(stages=[stage_a, stage_b, stage_c])
graph.connect([stage_a], [stage_b, stage_c])

# 配置
graph.set_reporter(True, host="127.0.0.1", port=5005)

# 启动
graph.start_graph({
    stage_a.get_tag(): range(100)
})
```