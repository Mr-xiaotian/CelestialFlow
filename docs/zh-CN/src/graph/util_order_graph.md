# src/celestialflow/graph/util_order_graph.py

> 📅 最后更新日期: 2026/10/30

`graph/util_order_graph.py` 提供最小图结构 `OrderGraph`，以及围绕它的一组基础图算法。

这个文件当前定位是：

- 为框架内部提供轻量、稳定顺序的图结构。
- 承担一部分图分析能力，减少对第三方图结构的耦合。
- 为 `TaskGraph` 与测试提供统一的图分析基础能力。

## 主要能力

### 图结构

`OrderGraph` 是最小有序有向图：

- 节点顺序按注册顺序稳定保存。
- 同时维护出边与入边邻接表。
- 只支持「加节点 / 加边」，不提供删除操作，因此 `_in` 与 `_out` 的键集合始终一致。
- `__repr__` 输出形如 `OrderGraph(nodes=4, edges=4)` 的摘要。

### 基础操作

| 成员 | 签名 | 说明 |
|------|------|------|
| `add_node` | `(name: str) -> None` | 添加节点，幂等；已存在时不做任何事 |
| `add_edge` | `(u: str, v: str) -> None` | 添加有向边，自动补齐端点节点并忽略重复边 |
| `nodes` | `-> list[str]` | 按注册顺序返回全部节点（拷贝） |
| `out_edges` | `-> dict[str, list[str]]` | 出边邻接表**引用视图**（与内部存储共享，调用方不应修改） |
| `in_edges` | `-> dict[str, list[str]]` | 入边邻接表**引用视图**（与内部存储共享，调用方不应修改） |
| `successors` | `(name: str) -> tuple[str, ...]` | 按插入顺序返回后继；未知节点返回空元组 |
| `predecessors` | `(name: str) -> tuple[str, ...]` | 按插入顺序返回前驱；未知节点返回空元组 |

### 图算法

| 函数 | 返回 | 说明 |
|------|------|------|
| `in_degree(graph)` | `dict[str, int]` | 每个节点的入度 |
| `is_dag(graph)` | `bool` | 使用 Kahn 算法判断是否为 DAG |
| `topo_sort(graph)` | `list[str] \| None` | 返回 Kahn 剥离顺序的拓扑序；含环时返回 `None` |
| `tarjan_scc(graph)` | `list[list[str]]` | 使用显式栈帧模拟递归的 Tarjan 算法计算强连通分量 |
| `node_to_scc_index(sccs)` | `dict[str, int]` | 节点 → SCC 索引映射 |
| `get_condensation(graph)` | `tuple[OrderGraph, list[list[str]]]` | 构建 SCC 凝聚图，SCC 节点命名为 `scc_0`、`scc_1` … |
| `source_sccs(graph)` | `list[list[str]]` | 凝聚图中入度为 0 的 SCC |
| `source_nodes(graph)` | `list[str]` | 从每个 Source SCC 中提取一个代表节点（`scc[0]`） |
| `compute_node_levels(graph)` | `dict[str, int]` | 计算节点层级，支持 DAG 和含环图 |

## 设计特点

### 内部存储

`OrderGraph` 在内部使用两份邻接表（`_in: dict[str, list[str]]` 与 `_out: dict[str, list[str]]`）共同表达节点集合与边集合。`add_node` / `add_edge` 不删除节点，节点遍历顺序由 Python `dict` 的插入序保证，节点集合与边集合因此始终保持稳定。

`add_edge(u, v)` 会先对两端调用 `add_node`，因此「先连边、后补节点」是合法用法；同一条边重复添加会被忽略（判断依据是 `v not in self._out[u]`），从而保持邻接表稳定。

### 为什么保留顺序

图分析本身未必要求固定遍历顺序，但在框架内部，稳定顺序通常更利于：

- 调试输出可复现。
- 测试结果更稳定。
- 层级分析和拓扑结果更贴近构图时的注册顺序。

### Tarjan 的非递归实现

`tarjan_scc()` 用显式栈帧 `frames: list[tuple[node, successors, next_pos]]` 模拟递归 DFS，避免深链图触发 Python 递归上限（默认约 1000 层）。输出与递归版完全等价，SCC 列表顺序为凝聚图的逆拓扑序。

## 层级计算说明

`compute_node_levels(graph)` 的处理思路是：

1. 先对原图做强连通分量分解。
2. 把每个 SCC 压缩成一个凝聚图节点。
3. 在凝聚图这个 DAG 上做拓扑传播（`level[succ] = max(level[succ], level[node] + 1)`）。
4. 把 SCC 层级映射回原始节点。

因此：

- DAG 中的普通节点会按最长前驱路径得到层级，源节点层级为 `0`。
- 含环图中，同一环内的节点共享同一个层级。
- 凝聚图按构造必然是 DAG；若 `topo_sort(cond) is None`，函数会抛出 `ValueError("condensation graph must be a DAG")`（防御性分支）。

这套层级算法直接服务于当前 `TaskGraph` 的图分析过程，不再依赖外部图对象。

## 与 `TaskGraph` 的关系

`TaskGraph` 在 `_build_analysis()` 阶段直接基于 `OrderGraph` 完成：

- 源节点识别（`source_nodes()`）
- DAG 判定（`is_dag()`）
- 节点层级计算（`compute_node_levels()`，再用 `runtime.util_format.cluster_by_value_sorted` 聚合为 `{层级: [节点名]}`）

需要注意语义差异：本模块的 `is_dag(graph)` 是**模块级函数**，参数是 `OrderGraph`；`TaskGraph` 上的同名成员是**无参方法** `graph.is_dag()`。两者不要混用。`TaskGraph` 的分析结果采用「惰性 + `_analysis_dirty` 脏标记」缓存，因此这里传入的始终是完整的 `self.order_graph`。

## 使用示例

### 基础构图

```python
from celestialflow.graph.util_order_graph import OrderGraph, is_dag, topo_sort

graph = OrderGraph()
graph.add_edge("A", "B")
graph.add_edge("A", "C")
graph.add_edge("B", "D")
graph.add_edge("C", "D")

print(graph.nodes)  # ['A', 'B', 'C', 'D']
print(graph.successors("A"))  # ('B', 'C')
print(graph.predecessors("D"))  # ('B', 'C')
print(is_dag(graph))  # True
print(topo_sort(graph))  # ['A', 'B', 'C', 'D']
print(graph)  # OrderGraph(nodes=4, edges=4)
```

### 强连通分量与凝聚图

```python
from celestialflow.graph.util_order_graph import (
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

print(sccs)  # 含环的 A/B/C 被归入同一 SCC，D 单独成组
print(cond.nodes)  # ['scc_0', 'scc_1']
print(cond.out_edges)  # 跨 SCC 的边已去重
```

### 节点层级

```python
from celestialflow.graph.util_order_graph import OrderGraph, compute_node_levels

graph = OrderGraph()
graph.add_edge("Input", "Clean")
graph.add_edge("Clean", "Parse")
graph.add_edge("Parse", "Store")

levels = compute_node_levels(graph)
print(levels)  # Input=0, Clean=1, Parse=2, Store=3（字典键顺序不保证与注册顺序一致）
```

### 源节点与环

```python
from celestialflow.graph.util_order_graph import (
    OrderGraph,
    compute_node_levels,
    source_nodes,
)

graph = OrderGraph()
graph.add_edge("A", "B")
graph.add_edge("B", "C")
graph.add_edge("C", "B")  # B <-> C 构成环

print(source_nodes(graph))  # ['A']
print(compute_node_levels(graph))  # A=0，B 与 C 同属一个环，层级都为 1
```

## 使用建议

- 如果你只需要轻量图结构和基础图算法，优先使用 `OrderGraph`。
- 如果你需要与 `TaskGraph` 的当前分析逻辑保持一致，优先使用这里的算法函数。
- `out_edges` / `in_edges` 返回的是内部字典本身，需要修改时请先 `dict(...)` 拷贝。
- 如果你需要导出可打印的图结构文本，应配合 `persist.util_render` 中的 `render_structure_list`。
