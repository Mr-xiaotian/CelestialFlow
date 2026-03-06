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
- **log_level**: 全局日志级别。

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
    
    :param init_tasks_dict: 初始任务数据，格式为 {stage_instance: [task_data, ...]}
    :param put_termination_signal: 是否在初始任务后自动注入终止信号。
    """
```

### 资源管理

- **进程管理**: 自动创建和管理子进程（对于 `process` 模式的 Stage）。
- **队列管理**: 自动创建节点间的通信队列 (`TaskQueue`)。
- **优雅退出**: 确保所有子进程在任务完成后正确退出，或者在异常时被强制终止。

### 监控与报告

- **运行时快照**: `collect_runtime_snapshot()` 收集每个节点的运行状态（处理数、积压数、速率等）。
- **错误持久化**: 将运行时的错误日志持久化到本地 JSONL 文件 (`fallback/` 目录)。
- **Web 上报**: 集成 `TaskReporter`，将状态实时推送给 Web UI。

## 辅助方法

- `test_methods(...)`: 用于性能测试，对比不同执行模式（serial vs process）下的耗时。
- `get_graph_topology()`: 获取拓扑结构数据。
- `get_status_dict()`: 获取实时状态字典。
