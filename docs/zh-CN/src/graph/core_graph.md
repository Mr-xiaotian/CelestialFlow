# TaskGraph

> 📅 最后更新日期: 2026/08/19

`TaskGraph` 是 CelestialFlow 的核心调度器，负责管理一组 `TaskStage` 节点的依赖关系、执行流程、资源分配和生命周期。

> 注意：`TaskGraph` 是一次性对象。一次 `run()` 完成后，不保证当前实例可被安全重置并再次启动；如需重复执行同一流程，请重新创建新的 `TaskGraph` 和关联 `TaskStage`。

## 关键数据结构

`TaskGraph` 内部使用 `stage_dict: dict[str, TaskStage]` 维护所有节点的 Stage 映射。队列连接在 `connect()` 阶段直接建立。图分析基于内部维护的 `OrderGraph` 实例。

## 初始化

```python
class TaskGraph:
    def __init__(self, name: str, graph_mode: str = "serial"): ...
```

### 参数说明

- **name**: 任务图名称（必填）
- **graph_mode**: 图执行模式
  - `serial`（默认）: 串行执行，按节点注册顺序逐个执行
  - `thread`: 线程并发执行，每个节点在独立线程中启动
  - `async`: 异步并发执行，需要在已运行事件循环的上下文中调用（见 [`start_async`](#start_async)）

## 图构建

### set_stages

```python
def set_stages(self, stages: list[TaskStage]) -> None:
    """
    添加节点到任务图。注册节点并注入图级事件客户端。

    :param stages: 节点列表
    :raises DuplicateNodeError: 如果节点名称重复
    """
```

### connect

```python
def connect(self, from_stages: list[TaskStage], to_stages: list[TaskStage]) -> None:
    """
    建立超边连接：from_stages 中的每个节点连接到 to_stages 中的每个节点。
    操作的是 out_edges / in_edges 字典，队列连接在 connect() 内直接完成。
    """
```

## 配置方法

### set_reporter

```python
def set_reporter(self, reporter: ReporterProtocol) -> None:
    """
    设定任务图绑定的 reporter。

    :param reporter: reporter 实例
    """
```

### set_ctree

```python
def set_ctree(self, ctree_client: EventClient) -> None:
    """
    设置任务图共享的事件客户端。
    传入后会同步下发给当前图中的所有 stage。
    """
```

> 默认情况下，`TaskGraph` 会在内部使用 `LocalEventClient()` 生成本地递增事件 ID，因此即使没有安装 `celestialtree`，核心执行链路也可以正常工作。
>
> 如果你希望把事件上报到 CelestialTree，需要先额外安装 `celestialtree`，再自行构造对应客户端实例并传给 `set_ctree()`。

### set_graph_mode

```python
def set_graph_mode(self, graph_mode: str) -> None:
    """
    设置图执行模式，可选值为 'serial'、'thread' 或 'async'。
    """
```

### set_stage_execution_mode

```python
def set_stage_execution_mode(self, execution_mode: str) -> None:
    """
    批量设置所有节点的 execution_mode（'serial'、'thread' 或 'async'）。
    会触发 _build_analysis() 重建分析数据。
    """
```

## 启动执行

### run

```python
def run(
    self,
    init_tasks_dict: dict[str, Iterable[Any]],
    *,
    if_put_signal: bool = True,
) -> None:
    """
    运行任务图。流程：
    1. 注入初始任务到各节点
    2. if_put_signal=True 时自动向源节点注入终止信号
    3. 调用 start() 启动执行
    """
```

### run_async

```python
async def run_async(
    self,
    init_tasks_dict: dict[str, Iterable[Any]],
    *,
    if_put_signal: bool = True,
) -> None:
    """异步版本的 run()。"""
```

### restore_db

```python
def restore_db(
    self,
    db_path: str | Path,
    statuses: Iterable[str] | None = None,
    *,
    filter_by_error_type: bool = False,
    if_put_signal: bool = True,
) -> None:
    """
    从 sqlite 持久化库中读取任务，按 stage 分组后启动任务图。

    :param db_path: sqlite 数据库文件路径
    :param statuses: 记录状态过滤列表，默认 ``["failed", "pending"]``
    :param filter_by_error_type: 是否按各 stage 的 ``retry_exceptions`` 过滤
        ``error_type``，默认 ``False``
    :param if_put_signal: 是否注入终止信号，默认 True
    """
```

该方法内部调用 `load_tasks_grouped_by_stage()` 加载持久化任务记录，
通过 `stage.metrics.get_retry_error_type_names()` 过滤可恢复的错误类型，
最终复用 `start()` 执行。

### 生命周期约束

- `TaskGraph` 内部会在启动过程中建立运行期队列连接、前驱绑定、线程引用和状态快照。
- 这些运行时资源设计上服务于一次完整执行，不承诺在运行结束后被安全清空并复用。
- 如果需要重新跑同一套拓扑，推荐重新实例化图对象与节点对象，而不是再次调用同一实例的 `run()`。

```python
graph = TaskGraph(name="MyGraph", graph_mode="thread")
graph.set_stages(stages=[stage_a, stage_b])
graph.connect([stage_a], [stage_b])
graph.run({stage_a.get_name(): [1, 2, 3, 4, 5]})
```

### start

```python
def start(self) -> None:
    """
    启动任务图（同步入口）。
    根据 graph_mode 选择 _execute_stages_serial() 或 _execute_stages_thread()。
    """
```

### start_async

```python
async def start_async(self) -> None:
    """
    异步启动任务图。要求 graph_mode='async'，否则抛出 InvalidOptionError。
    """
```

### _execute_stages_serial / _execute_stages_thread / _execute_stages_async

```python
def _execute_stages_serial(self) -> None:
    """按节点注册顺序串行执行。"""


def _execute_stages_thread(self) -> None:
    """每个节点在独立线程中启动，最后统一 join。"""


async def _execute_stages_async(self) -> None:
    """全图并发执行。"""
```

### _execute_stage / _execute_stage_async

```python
def _execute_stage(self, stage: AnyTaskStage) -> None:
    """
    在同步图启动路径下执行单个节点。
    - async 节点走 asyncio.run(stage.start_async())
    - 其他节点走 stage.start()
    """


async def _execute_stage_async(self, stage: AnyTaskStage) -> None:
    """
    异步执行单个节点：async 走协程，其余走 asyncio.to_thread(stage.start)。
    """
```

## 运行时监控

### collect_runtime_snapshot

```python
def collect_runtime_snapshot(self) -> None:
    """
    收集所有节点的运行时快照，更新 status_dict。
    计算每个节点的 processed / pending / elapsed / remaining 及全局剩余时间。
    """
```

该方法遍历所有 stage 调用 `stage.snapshot(interval)` 采集各节点快照，然后计算 DAG 感知的全局 pending 估算值，并补充到每个节点的快照中。

下表列出完整快照中包含的所有字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 节点名称 |
| `func_name` | `str` | 函数名 |
| `execution_mode` | `str` | 执行模式 |
| `max_workers` | `int` | 最大并发工作数 |
| `status` | `StageStatus` | 运行状态 |
| `tasks_input` | `int` | 输入任务数 |
| `tasks_succeeded` | `int` | 成功数 |
| `tasks_failed` | `int` | 失败数 |
| `tasks_duplicated` | `int` | 重复数 |
| `tasks_processed` | `int` | 已处理数 |
| `tasks_pending` | `int` | 待处理数 |
| `total_tasks_pending` | `int` | 全局预计待处理数 |
| `elapsed_time` | `float` | 已消耗时间 |
| `remaining_time` | `float` | 预计剩余时间 |
| `total_remaining_time` | `float` | 全局预计剩余时间 |
| `task_avg_time` | `str` | 平均时间（格式化） |
| `start_time` | `float` | 启动时间戳 |

## 查询接口

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `get_graph_id()` | `str` | 获取当前任务图实例的唯一标识 |
| `get_status_snapshot()` | `dict` | 带统一时间戳的状态快照 |
| `get_graph_analysis()` | `dict` | 图分析信息（graphId, graphMode, name, startTime, className, isDAG, layersDict） |
| `get_structure_graph()` | `dict` | JSON 格式的图结构（nodes + edges + source_nodes） |
| `get_structure_list()` | `list[str]` | 带边框的格式化树形文本 |
| `get_order_graph()` | `OrderGraph` | 内部有序有向图实例 |
| `get_fallback_path()` | `Path` | 回退数据库文件的绝对路径，未设置时返回空 Path |
| `get_source_stages()` | `list[TaskStage]` | 源节点列表 |

### get_graph_analysis 说明

`get_graph_analysis()` 返回包含以下字段的字典：

```python
{
    "graphId": self.graph_id,
    "graphMode": self.graph_mode,
    "name": self.name,
    "startTime": self.start_time,
    "className": self.__class__.__name__,
    "isDAG": self.is_dag,
    "layersDict": self.layers_dict,
}
```

## 生命周期图

```mermaid
flowchart TD
    INIT[__init__] --> INIT_STATE[_init_state]
    INIT_STATE --> BUILD[set_stages + connect]
    BUILD --> PREPARE[_prepare_start]
    PREPARE --> START[start / start_async]
    START -->|serial| SER[_execute_stages_serial]
    START -->|thread| THR[_execute_stages_thread]
    START -->|async| ASY[_execute_stages_async]
    SER --> FINISH[_finish_start]
    THR --> FINISH
    ASY --> FINISH
    FINISH -->|drain_task_queue| DRAIN[收集未消费任务]
    DRAIN --> SNAP[collect_runtime_snapshot]
    SNAP --> END[图执行完成]

    SNAP --> STATUS[get_status_snapshot]

    RUN[run / run_async] -->|注入初始任务| PUT[stage.put_tasks]
    RUN -->|注入终止信号| SIGNAL[put_source_signal]
```

## 图执行模式详解

### serial 模式

```
按节点注册顺序同步执行 stage.start() → 数据通过队列流动 → 终止信号到达后停止
```

- 按注册顺序逐节点同步执行
- 默认模式
- 适用场景：调试、串行流水线

### thread 模式

```
为每个节点启动独立线程 → stage.start() → join 全部线程
```

- 最大化并行度
- 适用场景：CPU/IO 混合型并发流水线

### async 模式

```
异步执行所有节点（asyncio.gather）→ 需在已有事件循环中调用 start_async()
```

- 全图并发协程执行
- `serial` / `thread` 模式下的节点通过 `asyncio.to_thread` 在独立线程中运行，避免阻塞事件循环
- 适用场景：需要与其它异步系统集成

## 非 DAG 图的注意事项

对于有环图，若 `if_put_signal=True`，`run` 会发出 `RuntimeWarning`。终止信号可能导致部分节点在接收上游数据前就提前退出，建议：

```python
graph.run({"source": tasks}, if_put_signal=False)
# 后续通过 stage.put_tasks 或外部手动注入 TerminationSignal
```

## 未消费任务处理

`_finish_start()` 中通过遍历 `stage_dict` 调用每个 stage 的 `drain_task_queue()` 收集所有剩余任务，将其标记为 `UnconsumedError` 并通过 `fallback_inlet` 持久化到 sqlite 回退数据库（经由 `FallbackSpout` 写入回退存储）。
