# GraphEstimators

> 📅 最后更新日期: 2026/09/16

`graph/util_estimators.py` 提供基于任务图（DAG）的全局待处理任务数估算函数。

## 主要函数

### calc_global_pending

```python
def calc_global_pending(
    graph: OrderGraph,
    processed_map: dict[str, int],
    pending_map: dict[str, int],
    downstream_map: dict[str, dict[str, int]],
) -> dict[str, int]: ...
```

基于任务图（DAG）估算各节点全局待处理任务数量（偏保守 / 拥塞放大型）。

#### 核心思想

1. 每个节点"已见任务量"定义为 `seen = processed + pending`
2. 对每个上游-下游组合维护独立放大系数 `scale[u][w]`，表示上游 u 对下游 w 的预计输出量：

   ```
   scale[u][w] = total_u * output_u->w / max(1, proc_u)
   ```

   其中 `output_u->w / proc_u` 为 u 对 w 的产出比，取自 u 自身的单次快照（与 `proc_u` 同源一致），避免跨节点快照时间差的影响。
3. 递推估算每个节点的"预计总输入任务量 total"：

   ```
   total_v = external_v + sum(scale[u][v] for u in preds(v))
   ```

   其中 `external_v = max(0, seen_v - sum(output_u->v))` 为外部注入任务数，不参与上游放大。
4. 预计剩余任务数为 `max(pending_v, total_v - processed_v)`，至少保留当前观测到的 pending。

#### 算法特性

- **逐下游独立放大**：每个下游按上游对其的真实输出比例独立放大，fan-out 分流与 splitter 多倍输出均显式记录
- **产出比单侧化**：产出比由发送方自身快照计算，`proc=0` 时系数天然为 0，不会产生病态放大
- **偏保守估计**：上游堆积时对下游显式放大，适合监控、告警或瓶颈识别
- **输入要求**：任务图必须为有向无环图（DAG），否则抛出 `ValueError`

#### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `graph` | `OrderGraph` | 任务依赖图，节点需与 map 的 key 对应 |
| `processed_map` | `dict[str, int]` | 每个节点已完成的任务数量 |
| `pending_map` | `dict[str, int]` | 每个节点当前剩余的任务数量 |
| `downstream_map` | `dict[str, dict[str, int]]` | 每个节点实际发送给各下游的任务数量，形如 `{node: {downstream_name: count}}`，缺失节点或下游按 0 处理 |

#### 返回值

`dict[str, int]` — 各节点预计待处理任务数量。

## 使用示例

```python
from celestialflow.graph.util_order_graph import OrderGraph
from celestialflow.graph.util_estimators import calc_global_pending

# 构建一个简单的 DAG: A -> B -> C
graph = OrderGraph()
for u, v in [("A", "B"), ("B", "C")]:
    graph.add_edge(u, v)

# 输入观测数据
processed_map = {"A": 100, "B": 50, "C": 10}
pending_map = {"A": 0, "B": 50, "C": 90}

# 各节点实际发送给下游的任务数量
downstream_map = {"A": {"B": 100}, "B": {"C": 50}}

result = calc_global_pending(graph, processed_map, pending_map, downstream_map)
for node, pending in result.items():
    print(f"节点 {node}: 预计待处理 {pending} 个任务")
```

## 用途

- 由 `TaskGraph.collect_runtime_snapshot()` 调用，为监控面板提供 DAG 感知的全局剩余任务估算
- 辅助识别潜在拥塞节点