"""使用 OrderGraph 复现实验性 SCC / 凝聚图分析。"""

from __future__ import annotations

from collections import deque

from celestialflow.graph.util_graph import OrderGraph, get_condensation, source_nodes, tarjan_scc


def bfs_reachable(graph: OrderGraph, roots: list[str]) -> set[str]:
    """
    计算给定根节点集合在有向图中的可达节点集合。

    :param graph: 输入图。
    :param roots: BFS 起点列表。
    :return: 全部可达节点集合。
    """
    visited: set[str] = set()
    queue = deque(roots)
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        queue.extend(graph.successors(node))
    return visited


graph = OrderGraph.from_edges(
    {
        "A1": ["A2"],
        "A2": ["A3"],
        "A3": ["A1", "B1", "C1"],
        "B1": ["B2"],
        "B2": ["B3"],
        "B3": ["B4"],
        "B4": ["B1"],
        "C1": ["C2"],
        "C2": ["C1"],
    },
    ("A1", "A2", "A3", "B1", "B2", "B3", "B4", "C1", "C2"),
)

# 验证结构
print("节点:", list(graph.nodes))
print(
    "边:",
    [(src, dst) for src, targets in graph.out_edges.items() for dst in targets],
)
print()

# SCC 分析
sccs = tarjan_scc(graph)
print(f"SCC 数量: {len(sccs)}")
for i, scc in enumerate(sccs):
    print(f"  SCC {i}: {set(scc)}")

# 缩合图
condensation, _ = get_condensation(graph)
print(f"\n缩合图节点: {list(condensation.nodes)}")
print(
    f"缩合图边: {[(src, dst) for src, targets in condensation.out_edges.items() for dst in targets]}"
)

# Source SCC 代表点
sources = source_nodes(graph)
print(f"\n启动 BFS 的代表点: {sources}")

# 验证覆盖
visited = bfs_reachable(graph, sources)
print(f"BFS 覆盖: {visited}")
print(f"完全覆盖: {visited == set(graph.nodes)}")
