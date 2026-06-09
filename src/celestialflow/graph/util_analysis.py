# graph/util_analysis.py
from __future__ import annotations

import networkx as nx
from ..stage.util_types import AnyTaskStage


# ======== (图论分析) ========
def build_networkx_graph(
    out_edges: dict[str, list[str]],
    stage_dict: dict[str, AnyTaskStage],
) -> nx.DiGraph[str]:
    """
    从邻接表和阶段运行时信息构建 networkx 有向图

    :param out_edges: 邻接表 {stage_name: [next_stage_name, ...]}
    :param stage_dict: {stage_name: AnyTaskStage}
    :return: 构建好的 networkx.DiGraph
    """
    G: nx.DiGraph[str] = nx.DiGraph()

    for stage_name, stage in stage_dict.items():
        G.add_node(stage_name, mode=stage.get_stage_mode())
    for src, dsts in out_edges.items():
        for dst in dsts:
            G.add_edge(src, dst)
    return G


def find_source_nodes(G: nx.DiGraph[str]) -> list[str]:
    """
    找到有向图中的源节点（入度为0的节点）

    :param G: networkx 有向图（DiGraph）
    :return: 源节点列表
    """
    condensation = nx.condensation(G)

    source_scc_ids = [n for n, d in condensation.in_degree() if d == 0]
    sources = [
        next(iter(condensation.nodes[scc_id]["members"])) for scc_id in source_scc_ids
    ]

    return sources


def compute_node_levels(G: nx.DiGraph[str]) -> dict[str, int]:
    """
    计算有向图中每个节点的层级（最早执行阶段）
    先将图缩合为 SCC 缩合图（condensation），再对缩合图做拓扑层级划分，
    同一 SCC 内的节点共享层级。支持 DAG 和含环图。

    :param G: networkx 有向图（DiGraph）
    :return: dict[node] = level (int)
    """
    condensation = nx.condensation(G)

    scc_level: dict[int, int] = dict.fromkeys(condensation.nodes, 0)
    for node in nx.topological_sort(condensation):
        for succ in condensation.successors(node):
            scc_level[succ] = max(scc_level[succ], scc_level[node] + 1)

    level: dict[str, int] = {}
    for scc_id, data in condensation.nodes(data=True):
        lv = scc_level[scc_id]
        for original_node in data["members"]:
            level[original_node] = lv

    return level
