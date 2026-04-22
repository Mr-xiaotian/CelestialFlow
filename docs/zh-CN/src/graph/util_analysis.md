# GraphAnalysis

`graph/util_analysis.py` 提供基于 `networkx` 的图分析工具。

## 主要能力

- `format_networkx_graph(structure_graph)`：将序列化后的结构 JSON 转换为 `networkx.DiGraph`。
- `compute_node_levels(G)`：对 DAG 做层级划分，返回 `node -> level` 映射。

## 使用场景

- TaskGraph 初始化后分析是否为 DAG。
- 生成 staged 调度所需的层信息。
- 为拓扑可视化提供层级数据。
