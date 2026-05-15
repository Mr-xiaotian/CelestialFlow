# GraphAnalysis

> 📅 最后更新日期: 2026/05/15

`graph/util_analysis.py` 提供基于 `networkx` 的图分析工具。

## 主要能力

- `build_networkx_graph(out_edges, stage_runtime_dict)`：从邻接表和阶段运行时信息构建 `networkx.DiGraph`。
- `compute_node_levels(G)`：对有向图做层级划分（支持 DAG 和含环图），返回 `node -> level` 映射。
- `find_source_nodes(G)`：找到有向图中的源节点（入度为 0 的节点），返回源节点列表。

## 使用场景

- TaskGraph 初始化后分析是否为 DAG。
- 生成 staged 调度所需的层信息。
- 自动识别源节点用于任务注入。
- 为拓扑可视化提供层级数据。
