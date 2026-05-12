# graph/util_analysis.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import networkx as nx

if TYPE_CHECKING:
    from .core_graph import StageRuntime


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


def build_networkx_graph(
    out_edges: dict[str, list[str]],
    stage_runtime_dict: dict[str, StageRuntime],
) -> nx.DiGraph[str]:
    """
    从邻接表和阶段运行时信息构建 networkx 有向图

    :param out_edges: 邻接表 {stage_tag: [next_stage_tag, ...]}
    :param stage_runtime_dict: {stage_tag: StageRuntime}
    :return: 构建好的 networkx.DiGraph
    """
    G: nx.DiGraph[str] = nx.DiGraph()
    
    for tag, runtime in stage_runtime_dict.items():
        G.add_node(tag, mode=runtime.stage.get_stage_mode())
    for src, dsts in out_edges.items():
        for dst in dsts:
            G.add_edge(src, dst)
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


def find_source_nodes(G: nx.DiGraph[str]) -> list[str]:
    """
    找到有向图中的源节点（入度为0的节点）

    :param G: networkx 有向图（DiGraph）
    :return: 源节点列表
    """
    condensation = nx.condensation(G)

    source_scc_ids = [n for n, d in condensation.in_degree() if d == 0]
    sources = [next(iter(condensation.nodes[scc_id]['members'])) for scc_id in source_scc_ids]

    return sources