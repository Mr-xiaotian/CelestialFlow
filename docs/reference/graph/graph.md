# TaskGraph

`TaskGraph` 是 CelestialFlow 的核心调度器，负责管理一组 `TaskStage` 节点的依赖关系、执行流程、资源分配和生命周期。

## 初始化

```python
class TaskGraph:
    def __init__(
        self,
        root_stages: List[TaskStage],
        schedule_mode: str = "eager",
        log_level: str = "SUCCESS",
    ):
        ...
```

### 参数说明

- **root_stages**: 任务图的入口节点列表（根节点）。支持多根节点（森林结构）。
- **schedule_mode**: 调度模式。
  - `eager` (默认): 所有节点一次性启动，依赖关系通过数据流自动控制。适用于最大化并行度。
  - `staged`: 分层执行。仅适用于 DAG。按层级顺序逐层启动，上一层全部完成后才启动下一层。
- **log_level**: 全局日志级别（TRACE/DEBUG/SUCCESS/INFO/WARNING/ERROR/CRITICAL）。

## 核心功能

### 图构建与分析

- **自动构建**: 根据 `root_stages` 和节点间的连接关系 (`next_stages`), 自动遍历并构建整个图结构。
- **DAG 检测**: 自动检测是否为有向无环图 (DAG)。
- **分层分析**: 如果是 DAG，会自动计算节点的层级，用于 `staged` 调度或可视化展示。

### 启动运行

```python
def start_graph(self, init_tasks_dict: dict, put_termination_signal: bool = True):
    """
    启动任务图。
    
    :param init_tasks_dict: 初始任务数据，格式为 {stage_tag: [task_data, ...]}
    :param put_termination_signal: 是否在初始任务后自动注入终止信号。
    """
```

示例：
```python
graph = TaskGraph([stage_a, stage_b])
graph.start_graph({
    stage_a.get_tag(): [1, 2, 3, 4, 5]
})
```

### 资源管理

- **进程管理**: 自动创建和管理子进程（对于 `process` 模式的 Stage）。
- **队列管理**: 自动创建节点间的通信队列 (`TaskInQueue`, `TaskOutQueue`)。
- **优雅退出**: 确保所有子进程在任务完成后正确退出，或者在异常时被强制终止。

### 监控与报告

- **运行时快照**: `collect_runtime_snapshot()` 收集每个节点的运行状态（处理数、积压数、速率等）。
- **错误持久化**: 将运行时的错误日志持久化到本地 JSONL 文件 (`fallback/` 目录)。
- **Web 上报**: 集成 `TaskReporter`，将状态实时推送给 Web UI。

## 配置方法

### set_reporter

```python
def set_reporter(self, is_report=False, host="127.0.0.1", port=5000):
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
    use_ctree=False,
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778,
    transport="grpc",
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

    :param stage_mode: 节点运行模式 ('serial' 或 'process')
    :param execution_mode: 节点内部执行模式 ('serial' 或 'thread')
    """
```

### set_log_level

```python
def set_log_level(self, level="SUCCESS"):
    """
    设置全局日志级别。
    """
```

## 数据查询方法

### 状态查询

```python
# 获取节点状态字典
def get_status_dict(self) -> Dict[str, dict]:
    """返回每个节点的实时状态。"""

# 获取图摘要
def get_graph_summary(self) -> dict:
    """返回全局统计（成功数、失败数、积压数等）。"""
```

### 拓扑查询

```python
# 获取拓扑信息
def get_graph_topology(self) -> dict:
    """返回 isDAG, schedule_mode, layers_dict 等信息。"""

# 获取结构 JSON
def get_structure_json(self) -> List[dict]:
    """返回图结构的 JSON 表示。"""

# 获取结构列表
def get_structure_list(self) -> List[str]:
    """返回格式化的结构列表。"""
```

### NetworkX 图

```python
def get_networkx_graph(self):
    """
    获取任务图的 networkx 有向图（DiGraph）。
    可用于复杂图分析。
    """
```

### 错误查询

```python
# 按阶段获取失败任务
def get_fail_by_stage_dict(self):
    """返回 {stage_tag: [failed_tasks]} 格式的字典。"""

# 按错误类型获取失败任务
def get_fail_by_error_dict(self):
    """返回 {error_type: [failed_tasks]} 格式的字典。"""

# 获取 fallback 文件路径
def get_fallback_path(self) -> str:
    """返回错误日志文件路径。"""
```

### 追踪查询

```python
# 获取输入追踪
def get_stage_input_trace(self, stage_tag: str) -> str:
    """获取指定节点的输入事件追踪（需要启用 ctree）。"""

# 获取错误追踪
def get_error_trace(self, error_id):
    """获取指定错误的追踪信息。"""
```

## 任务注入

### put_stage_queue

```python
def put_stage_queue(self, tasks_dict: dict, put_termination_signal=True):
    """
    动态向节点队列注入任务。

    :param tasks_dict: {stage_tag: [tasks]}
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

## 辅助方法

### test_methods

用于性能测试，对比不同执行模式下的耗时。

```python
def test_methods(self, init_tasks_dict, test_cases=None):
    """
    测试不同执行模式组合的性能。
    """
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

1. **非 DAG 图**: 对于有环图，不建议自动注入终止信号，应通过 Web 界面手动控制。
2. **进程清理**: 异常情况下，框架会强制终止子进程并记录日志。
3. **未消费任务**: 停止时会收集未消费的任务并记录为错误。
4. **Web 监控**: 需要先启动 Web 服务，再设置 `set_reporter(True)`。

## 示例

```python
from celestialflow import TaskStage, TaskGraph

# 创建节点
stage_a = TaskStage(func=process_a, execution_mode="thread")
stage_b = TaskStage(func=process_b, execution_mode="serial")
stage_c = TaskStage(func=process_c, execution_mode="serial")

# 构建图
stage_a.set_graph_context([stage_b, stage_c], stage_mode="process", stage_name="A")
stage_b.set_graph_context([], stage_mode="process", stage_name="B")
stage_c.set_graph_context([], stage_mode="process", stage_name="C")

# 创建图并配置
graph = TaskGraph([stage_a], schedule_mode="eager", log_level="INFO")
graph.set_reporter(True, host="127.0.0.1", port=5005)

# 启动
graph.start_graph({
    stage_a.get_tag(): range(100)
})
```