# graph/util_analysis.py
from __future__ import annotations

from typing import Any

import networkx as nx


# ======== (图论分析) ========
def format_networkx_graph(structure_graph: list[dict[str, Any]]) -> nx.DiGraph[str]:
    """
    将结构图（由 build_structure_graph 生成）转换为 networkx 有向图（DiGraph）

    :param structure_graph: JSON 格式的任务结构图，list[dict]
    :return: 构建好的 networkx.DiGraph
    """
    G: nx.DiGraph[str] = nx.DiGraph()

    def add_node_and_edges(node: dict[str, Any]) -> None:
        """
        递归添加节点及其边到有向图中。

        :param node: 节点字典，包含 name、func_name、next_stages 等字段
        """
        node_id = f"{node['name']}[{node['func_name']}]"
        G.add_node(node_id, **{"mode": node.get("stage_mode")})

        for child in node.get("next_stages", []):
            child_id = f"{child['name']}[{child['func_name']}]"
            G.add_edge(node_id, child_id)
            # 递归添加子节点
            add_node_and_edges(child)

    for root in structure_graph:
        add_node_and_edges(root)

    return G


def compute_node_levels(G: nx.DiGraph[str]) -> dict[str, int]:
    """
    计算有向图中每个节点的层级（最早执行阶段）
    先将图缩合为 SCC 缩合图（condensation），再对缩合图做拓扑层级划分，
    同一 SCC 内的节点共享层级。支持 DAG 和含环图。

    :param G: networkx 有向图（DiGraph）
    :return: dict[node] = level (int)
    """
    condensation = nx.condensation(G)

    scc_level: dict[int, int] = {node: 0 for node in condensation.nodes}
    for node in nx.topological_sort(condensation):
        for succ in condensation.successors(node):
            scc_level[succ] = max(scc_level[succ], scc_level[node] + 1)

    level: dict[str, int] = {}
    for scc_id, data in condensation.nodes(data=True):
        lv = scc_level[scc_id]
        for original_node in data["members"]:
            level[original_node] = lv

    return level
