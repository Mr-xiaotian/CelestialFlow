# graph/analysis.py
import networkx as nx
from networkx import is_directed_acyclic_graph
from typing import Dict, Any, List


# ======== (图论分析) ========
def format_networkx_graph(structure_graph: List[Dict[str, Any]]) -> nx.DiGraph:
    """
    将结构图（由 build_structure_graph 生成）转换为 networkx 有向图（DiGraph）

    :param structure_graph: JSON 格式的任务结构图，List[Dict]
    :return: 构建好的 networkx.DiGraph
    """
    G = nx.DiGraph()

    def add_node_and_edges(node: Dict[str, Any]):
        node_id = f'{node["name"]}[{node["func_name"]}]'
        G.add_node(node_id, **{"mode": node.get("stage_mode")})

        for child in node.get("next_stages", []):
            child_id = f'{child["name"]}[{child["func_name"]}]'
            G.add_edge(node_id, child_id)
            # 递归添加子节点
            add_node_and_edges(child)

    for root in structure_graph:
        add_node_and_edges(root)

    return G


def compute_node_levels(G: nx.DiGraph) -> Dict[str, int]:
    """
    计算 DAG 中每个节点的层级（最早执行阶段）
    前提：图必须是有向无环图（DAG）

    :param G: networkx 有向图（DiGraph）
    :return: dict[node] = level (int)
    """
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("该图不是 DAG，无法进行层级划分")

    level = {node: 0 for node in G.nodes}  # 初始层级为 0

    for node in nx.topological_sort(G):  # 按拓扑顺序遍历
        for succ in G.successors(node):
            level[succ] = max(level[succ], level[node] + 1)

    return level
