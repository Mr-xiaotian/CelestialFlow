# OrderGraph 与图算法工具

> 📅 最后更新日期: 2026/06/18

`graph/util_graph.py` 提供最小图结构 `OrderGraph`，以及围绕它的一组基础图算法。

这个文件当前定位是：

- 为框架内部提供轻量、稳定顺序的图结构。
- 承担一部分图分析能力，减少对第三方图结构的耦合。
- 为 `TaskGraph`、运行时估算和测试提供统一的图分析基础能力。

## 主要能力

### 图结构

- `OrderGraph`
  - 最小有序有向图。
  - 节点顺序按注册顺序稳定保存。
  - 同时维护出边与入边邻接表。

### 基础操作

- `add_node(name)`：添加节点，幂等。
- `add_edge(u, v)`：添加有向边，自动补齐端点节点并去重。
- `nodes`：按注册顺序返回全部节点。
- `out_edges`：返回出边邻接表拷贝。
- `in_edges`：返回入边邻接表拷贝。
- `successors(name)`：返回后继节点。
- `predecessors(name)`：返回前驱节点。
- `has_node(name)`：判断节点是否存在。
- `from_edges(out_edges, stage_names=None)`：从邻接表构建 `OrderGraph`。

### 图算法

- `in_degree(graph)`：计算每个节点的入度。
- `is_dag(graph)`：使用 Kahn 算法判断是否为 DAG。
- `topo_sort(graph)`：返回拓扑序；若存在环则返回 `None`。
- `tarjan_scc(graph)`：使用 Tarjan 算法计算强连通分量。
- `node_to_scc_index(sccs)`：构建节点到 SCC 索引的映射。
- `get_condensation(graph)`：构建 SCC 凝聚图。
- `source_sccs(graph)`：返回凝聚图中入度为 0 的强连通分量。
- `source_nodes(graph)`：从每个 Source SCC 中提取一个代表节点。
- `compute_node_levels(graph)`：计算节点层级，支持 DAG 和含环图。

## 设计特点

### 为什么不是 `list`

`OrderGraph` 的 `_nodes` 内部使用 `dict[str, None]` 而不是 `list[str]`，原因是它需要同时满足两件事：

- 节点存在性判断要快。
- 节点遍历顺序要稳定。

如果用 `list`，判重和查存在都是线性复杂度；如果用普通 `set`，虽然查存在快，但顺序不稳定。`dict` 在这里等价于一个“有序集合”，更适合这个场景。

### 为什么保留顺序

图分析本身未必要求固定遍历顺序，但在框架内部，稳定顺序通常更利于：

- 调试输出可复现。
- 测试结果更稳定。
- 层级分析和拓扑结果更贴近构图时的注册顺序。

## 层级计算说明

`compute_node_levels(graph)` 的处理思路是：

1. 先对原图做强连通分量分解。
2. 把每个 SCC 压缩成一个凝聚图节点。
3. 在凝聚图这个 DAG 上做拓扑传播。
4. 把 SCC 层级映射回原始节点。

因此：

- DAG 中的普通节点会按最长前驱路径得到层级。
- 含环图中，同一环内的节点共享同一个层级。

这套层级算法直接服务于当前 `TaskGraph` 的图分析过程，不再依赖外部图对象。

## 与 `TaskGraph` 的关系

`TaskGraph` 当前在 `_build_analysis()` 阶段直接基于 `OrderGraph` 完成：

- 源节点识别
- DAG 判定
- 节点层级计算
- 运行时全局 pending 估算所需的拓扑与前驱访问

## 使用示例

### 基础构图

```python
from celestialflow.graph.util_graph import OrderGraph, is_dag, topo_sort

graph = OrderGraph()
graph.add_edge("A", "B")
graph.add_edge("A", "C")
graph.add_edge("B", "D")
graph.add_edge("C", "D")

print(graph.nodes)                # ('A', 'B', 'C', 'D')
print(graph.successors("A"))     # ('B', 'C')
print(graph.predecessors("D"))   # ('B', 'C')
print(is_dag(graph))             # True
print(topo_sort(graph))          # ['A', 'B', 'C', 'D']
```

### 强连通分量与凝聚图

```python
from celestialflow.graph.util_graph import (
    OrderGraph,
    get_condensation,
    tarjan_scc,
)

graph = OrderGraph()
graph.add_edge("A", "B")
graph.add_edge("B", "C")
graph.add_edge("C", "A")
graph.add_edge("C", "D")

sccs = tarjan_scc(graph)
cond, _ = get_condensation(graph)

print(sccs)
print(cond.nodes)
print(cond.out_edges)
```

### 节点层级

```python
from celestialflow.graph.util_graph import OrderGraph, compute_node_levels

graph = OrderGraph()
graph.add_edge("Input", "Clean")
graph.add_edge("Clean", "Parse")
graph.add_edge("Parse", "Store")

levels = compute_node_levels(graph)
print(levels)
```

## 使用建议

- 如果你只需要轻量图结构和基础图算法，优先使用 `OrderGraph`。
- 如果你需要与 `TaskGraph` 的当前分析逻辑保持一致，优先使用这里的算法函数。
- 如果你需要导出给前端或日志使用的结构数据，应继续配合 `util_serialize.py`。
