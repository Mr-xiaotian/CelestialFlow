# GraphAnalysis

> 📅 最后更新日期: 2026/05/28

`graph/util_analysis.py` 提供基于 `networkx` 的图分析工具。

## 主要能力

- `build_networkx_graph(out_edges, stage_dict)`：从邻接表和 Stage 映射构建 `networkx.DiGraph`。
- `compute_node_levels(G)`：对有向图做层级划分（支持 DAG 和含环图），返回 `node -> level` 映射。
- `find_source_nodes(G)`：找到有向图中的源节点（入度为 0 的节点），返回源节点列表。

## 使用示例

以下示例展示图分析工具的各函数用法。

```python
import networkx as nx
from celestialflow import TaskGraph, TaskStage
from celestialflow.graph.util_analysis import (
    build_networkx_graph,
    compute_node_levels,
    find_source_nodes,
)

# 1. 构建一个有 DAG 的 TaskGraph
s1 = TaskStage("A", func=lambda x: x + 1)
s2 = TaskStage("B", func=lambda x: x * 2)
s3 = TaskStage("C", func=lambda x: x - 1)
s4 = TaskStage("D", func=lambda x: x ** 2)

graph = TaskGraph()
graph.set_stages([s1, s2, s3, s4])
graph.connect([s1], [s2])
graph.connect([s1], [s3])
graph.connect([s2], [s4])
graph.connect([s3], [s4])

# 2. 构建 networkx DiGraph
G = build_networkx_graph(graph.out_edges, graph.stage_dict)
print(f"节点数: {G.number_of_nodes()}")  # 4
print(f"边数: {G.number_of_edges()}")    # 4
print(f"节点属性: {dict(G.nodes(data=True))}")

# 3. 计算节点层级
levels = compute_node_levels(G)
print(f"节点层级: {levels}")
for node, lv in sorted(levels.items(), key=lambda x: x[1]):
    print(f"  层级 {lv}: {node}")

# 4. 查找源节点（入度为 0）
sources = find_source_nodes(G)
print(f"源节点: {sources}")  # ['A']
```

### 与 TaskGraph 的 get_graph_analysis 结合

```python
from celestialflow import TaskGraph, TaskStage

# 构建图并执行后获取分析信息
graph = TaskGraph()
s1 = TaskStage("X", func=lambda x: x)
s2 = TaskStage("Y", func=lambda x: x * 2)
graph.set_stages([s1, s2])
graph.connect([s1], [s2])

analysis = graph.get_graph_analysis()
print(f"是否为 DAG: {analysis['isDAG']}")  # True
print(f"调度模式: {analysis['scheduleMode']}")  # eager
print(f"层级分布: {analysis['layersDict']}")
print(f"邻接表: {analysis['out_edges']}")

# 获取 networkx 图
nx_graph = graph.get_networkx_graph()
print(f"类型: {type(nx_graph).__name__}")  # DiGraph
```

## 使用场景

- TaskGraph 初始化后分析是否为 DAG。
- 生成 staged 调度所需的层信息。
- 自动识别源节点用于任务注入。
- 为拓扑可视化提供层级数据。
