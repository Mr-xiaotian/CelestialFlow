# GraphEstimators

> 📅 最后更新日期: 2026/08/31

`graph/util_estimators.py` 提供基于任务图（DAG）的全局待处理任务数估算函数。

## 主要函数

### calc_global_pending

```python
def calc_global_pending(
    graph: OrderGraph,
    processed_map: dict[str, int],
    pending_map: dict[str, int],
) -> dict[str, int]: ...
```

基于任务图（DAG）估算各节点全局待处理任务数量（偏保守 / 拥塞放大型）。

#### 核心思想

1. 每个节点"已见任务量"定义为 `seen = processed + pending`
2. 下游节点当前已见任务平均来自其所有上游节点（多上游等贡献假设）
3. 使用拓扑序在 DAG 上递推估算每个节点的"预计总输入任务量 total"，并据此计算放大系数 `scale`
4. 预计剩余任务数至少保留当前观测到的 pending

#### 算法特性

- **多上游等贡献假设**：不区分不同上游的真实产出比例
- **偏保守估计**：使用 `processed` 作为放大基准，系统早期或严重堆积时产生较大估计值
- **输入要求**：任务图必须为有向无环图（DAG），否则抛出 `ValueError`

#### 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `graph` | `OrderGraph` | 任务依赖图，节点需与 map 的 key 对应 |
| `processed_map` | `dict[str, int]` | 每个节点已完成的任务数量 |
| `pending_map` | `dict[str, int]` | 每个节点当前剩余的任务数量 |

#### 返回值

`dict[str, int]` — 各节点预计待处理任务数量。

## 使用示例

```python
from celestialflow.graph.util_order_graph import OrderGraph
from celestialflow.graph.util_estimators import calc_global_pending

# 构建一个简单的 DAG: A -> B -> C
graph = OrderGraph.from_edges({"A": ["B"], "B": ["C"]}, ("A", "B", "C"))

# 输入观测数据
processed_map = {"A": 100, "B": 50, "C": 10}
pending_map = {"A": 0, "B": 50, "C": 90}

result = calc_global_pending(graph, processed_map, pending_map)
for node, pending in result.items():
    print(f"节点 {node}: 预计待处理 {pending} 个任务")
```

## 用途

- 由 `TaskGraph.collect_runtime_snapshot()` 调用，为监控面板提供 DAG 感知的全局剩余任务估算
- 辅助识别潜在拥塞节点
