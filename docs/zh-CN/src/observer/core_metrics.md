# src/celestialflow/observer/core_metrics.py

> 📅 最后更新日期: 2026/10/09

`core_metrics.py` 定义了**图级指标观察者** `MetricsObserver`。它同时承担"写模型"与"只读视图"两种角色：作为观察者从事件中写入每个节点的计数、状态与运行起始时间，并通过只读视图暴露不可变的 `NodeMetrics` 快照。

## MetricsObserver

```python
class MetricsObserver(Observer):
    def __init__(self) -> None: ...

    def on_node_start(self, event: NodeStartEvent) -> None: ...
    def on_node_end(self, event: NodeEndEvent) -> None: ...
    def on_task_input(self, event: TaskInputEvent) -> None: ...
    def on_task_success(self, event: TaskSuccessEvent) -> None: ...
    def on_task_fail(self, event: TaskFailEvent) -> None: ...
    def on_task_skip(self, event: TaskSkipEvent) -> None: ...

    def get_node_metrics(self, node: str) -> NodeMetrics | None: ...
    def get_graph_metrics(self) -> dict[str, NodeMetrics]: ...
```

单个实例服务一个运行作用域：整张任务图，或独立运行的单节点。

## 事件写入逻辑

MetricsObserver 只关心以下事件以维护指标：

| 事件 | 写入行为 |
|------|---------|
| `on_node_start` | 将该节点状态置为 `RUNNING`，并记录墙钟起始时间 |
| `on_node_end` | 将该节点状态置为 `STOPPED` |
| `on_task_input` | 区分来源：`from_node is None` 时累加外部注入计数；否则同时累加接收方的上游计数与来源方的下游计数 |
| `on_task_success` | 累加该节点成功计数 |
| `on_task_fail` | 累加该节点失败计数 |
| `on_task_skip` | 累加该节点跳过计数 |

存储格随首个事件**按需建立**（`_ensure`，幂等），边计数亦由实际任务流向增量写入，因此不依赖建图期的结构事件；上游投递会同时写入接收方的上游计数与来源方的下游计数，无需在节点间共享计数器对象，也无需按节点类型特化统计逻辑。

## 只读视图

读取通过 `runtime.util_types.MetricsView` 协议暴露，返回不可变的 `NodeMetrics` 快照：

- `get_node_metrics(node)`：获取单个节点的指标快照；节点未登记时返回 `None`。
- `get_graph_metrics()`：返回全图所有节点的指标快照（`{node: NodeMetrics}`）。

`NodeMetrics` 是只读 DTO（`runtime.util_types`），字段如下：

| 字段 | 说明 |
|------|------|
| `node` | 节点名称 |
| `status` | 节点生命周期状态（`NodeStatus`） |
| `start_time` | 节点进入运行状态的墙钟时间（秒），未启动为 `0.0` |
| `external_input` | 外部注入任务数 |
| `upstream_input` | 上游提供任务数 |
| `input_total` | 输入总数（外部注入 + 上游提供） |
| `succeeded` / `failed` / `skipped` | 成功 / 失败 / 跳过任务数 |
| `processed` | 已处理数（成功 + 失败 + 跳过） |
| `pending` | 待处理数（`max(0, input_total - processed)`） |
| `upstream_counts` / `downstream_counts` | 各上游 / 下游节点的任务数量映射 |

## 使用示例

```python
from celestialflow.observer import ObserverHub, MetricsObserver


metrics = MetricsObserver()
hub = ObserverHub()
hub.add_observer(metrics)

# ... 任务图运行后 ...

for node_name, nm in metrics.get_graph_metrics().items():
    print(node_name, nm.succeeded, nm.failed, nm.skipped, nm.pending)
```

## 与节点 / 装配的关系

- `BaseTaskNode` **不再**自行持有计数与 `TaskMetrics`，节点计数统一由 `MetricsObserver` 依据事件维护。
- 装配阶段（`assembly/core_run.py`）创建 `MetricsObserver` 并注册到节点 `ObserverHub`，其只读视图交叉提供给 `LogInlet` 与快照处理器使用。

## 注意事项

1. **单作用域实例**：一个 `MetricsObserver` 服务一个运行作用域，避免在不同图 / 节点间复用导致计数串扰。
2. **线程安全**：内部所有存储访问都在 `_lock` 保护下进行。
3. **结构由事件驱动**：不依赖建图期结构事件，任何节点只要出现任务事件即可建立其存储格。