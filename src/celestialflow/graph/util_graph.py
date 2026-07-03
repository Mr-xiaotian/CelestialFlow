from __future__ import annotations

from collections import deque
from collections.abc import Iterable


class OrderGraph:
    """用于内部图分析辅助函数的最小有序有向图。"""

    def __init__(self) -> None:
        # 用 dict 充当有序集合，保证节点遍历顺序稳定。
        self._nodes: dict[str, None] = {}
        self._in: dict[str, list[str]] = {}
        self._out: dict[str, list[str]] = {}

    def add_node(self, name: str) -> None:
        """
        如果节点不存在，则添加节点。

        :param name: 节点名称。
        :return: ``None``。
        """
        if name not in self._nodes:
            self._nodes[name] = None
            self._out.setdefault(name, [])
            self._in.setdefault(name, [])

    def add_edge(self, u: str, v: str) -> None:
        """
        添加一条有向边，并自动补全缺失端点节点。

        重复边会被忽略，以保持邻接表稳定。

        :param u: 上游节点名称。
        :param v: 下游节点名称。
        :return: ``None``。
        """
        self.add_node(u)
        self.add_node(v)
        if v not in self._out[u]:
            self._out[u].append(v)
            self._in[v].append(u)
        elif u not in self._in[v]:
            self._in[v].append(u)

    @property
    def nodes(self) -> tuple[str, ...]:
        """
        按插入顺序返回全部节点名称。

        :return: 稳定顺序的节点序列。
        """
        return tuple(self._nodes)

    @property
    def out_edges(self) -> dict[str, list[str]]:
        """
        返回出边邻接表的深拷贝视图。

        :return: ``{node: [successor, ...]}``。
        """
        return {k: list(v) for k, v in self._out.items()}

    @property
    def in_edges(self) -> dict[str, list[str]]:
        """
        返回入边邻接表的深拷贝视图。

        :return: ``{node: [predecessor, ...]}``。
        """
        return {k: list(v) for k, v in self._in.items()}

    def has_node(self, name: str) -> bool:
        """
        判断节点是否存在。

        :param name: 节点名称。
        :return: 若节点存在则返回 ``True``。
        """
        return name in self._nodes

    def successors(self, name: str) -> tuple[str, ...]:
        """
        按插入顺序返回后继节点。

        :param name: 节点名称。
        :return: 后继节点名称序列。
        """
        return tuple(self._out.get(name, ()))

    def predecessors(self, name: str) -> tuple[str, ...]:
        """
        按插入顺序返回前驱节点。

        :param name: 节点名称。
        :return: 前驱节点名称序列。
        """
        return tuple(self._in.get(name, ()))

    @classmethod
    def from_edges(
        cls,
        out_edges: dict[str, list[str]],
        stage_names: Iterable[str] | None = None,
    ) -> OrderGraph:
        """
        从邻接数据构建图。

        ``stage_names`` 用于保留那些未出现在出边邻接表中的孤立节点。

        :param out_edges: 出边邻接表。
        :param stage_names: 可选的显式节点名称集合。
        :return: 构建后的 :class:`OrderGraph`。
        """
        g = cls()
        if stage_names is not None:
            for name in stage_names:
                g.add_node(name)
        for u, targets in out_edges.items():
            for v in targets:
                g.add_edge(u, v)
        return g

    def __repr__(self) -> str:
        n = len(self._nodes)
        e = sum(len(t) for t in self._out.values())
        return f"OrderGraph(nodes={n}, edges={e})"


# ==================== 功能函数 ====================


def in_degree(graph: OrderGraph) -> dict[str, int]:
    """
    计算每个节点的入度。

    :param graph: 输入图。
    :return: ``{node: in_degree}``。
    """
    return {name: len(graph.in_edges.get(name, ())) for name in graph.nodes}


def is_dag(graph: OrderGraph) -> bool:
    """
    使用 Kahn 算法判断图是否为 DAG。

    :param graph: 输入图。
    :return: 若全部节点都能被拓扑剥离，则返回 ``True``。
    """
    deg = in_degree(graph)
    queue = deque(n for n, d in deg.items() if d == 0)
    visited = 0

    # 逐步剥离入度为 0 的节点；若能访问完全部节点，则说明图无环。
    while queue:
        u = queue.popleft()
        visited += 1
        for v in graph.successors(u):
            deg[v] -= 1
            if deg[v] == 0:
                queue.append(v)

    return visited == len(graph.nodes)


def tarjan_scc(graph: OrderGraph) -> list[list[str]]:
    """
    使用 Tarjan 算法计算强连通分量。

    返回的 SCC 列表顺序为凝聚图的逆拓扑序，这与之前使用的
    NetworkX condensation 行为保持一致。

    :param graph: 输入图。
    :return: SCC 节点分组列表。
    """
    out = graph.out_edges
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    sccs: list[list[str]] = []

    def strongconnect(v: str) -> None:
        nonlocal index
        indices[v] = lowlink[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)

        # 深度优先遍历并在回溯时更新 lowlink，用于识别 SCC 根节点。
        for w in out.get(v, []):
            if w not in indices:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], indices[w])

        if lowlink[v] == indices[v]:
            scc: list[str] = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == v:
                    break
            sccs.append(scc)

    for v in graph.nodes:
        if v not in indices:
            strongconnect(v)

    return sccs


def node_to_scc_index(sccs: list[list[str]]) -> dict[str, int]:
    """
    构建节点到 SCC 索引的映射。

    :param sccs: 强连通分量列表。
    :return: ``{node: scc_index}``。
    """
    return {node: i for i, scc in enumerate(sccs) for node in scc}


def get_condensation(graph: OrderGraph) -> tuple[OrderGraph, list[list[str]]]:
    """
    构建 SCC 凝聚图。

    凝聚图节点命名为 ``scc_0``, ``scc_1`` ...，并自动去重跨 SCC 边。

    :param graph: 输入图。
    :return: ``(condensation_graph, sccs)``。
    """
    sccs = tarjan_scc(graph)
    mapping = node_to_scc_index(sccs)
    k = len(sccs)

    cond = OrderGraph()
    # 先显式注册全部 SCC 节点，这样孤立 SCC 也能被保留下来。
    for i in range(k):
        cond.add_node(f"scc_{i}")

    # 再把跨 SCC 的边压缩进凝聚图，并在此处完成去重。
    seen: set[tuple[int, int]] = set()
    for u, targets in graph.out_edges.items():
        for v in targets:
            su, sv = mapping[u], mapping[v]
            if su != sv:
                key = (su, sv)
                if key not in seen:
                    seen.add(key)
                    cond.add_edge(f"scc_{su}", f"scc_{sv}")

    return cond, sccs


def source_sccs(graph: OrderGraph) -> list[list[str]]:
    """
    返回凝聚图中入度为 0 的 SCC。

    :param graph: 输入图。
    :return: Source SCC 分组列表。
    """
    sccs = tarjan_scc(graph)
    if not sccs:
        return []

    mapping = node_to_scc_index(sccs)
    k = len(sccs)
    scc_in_deg = [0] * k

    for u, targets in graph.out_edges.items():
        for v in targets:
            su, sv = mapping[u], mapping[v]
            if su != sv:
                scc_in_deg[sv] += 1

    return [sccs[i] for i, d in enumerate(scc_in_deg) if d == 0]


def source_nodes(graph: OrderGraph) -> list[str]:
    """
    从每个 Source SCC 中返回一个代表节点。

    :param graph: 输入图。
    :return: 代表性源节点列表。
    """
    return [scc[0] for scc in source_sccs(graph)]


def topo_sort(graph: OrderGraph) -> list[str] | None:
    """
    若图是 DAG，则返回一个拓扑序。

    :param graph: 输入图。
    :return: 拓扑序；若图中存在环则返回 ``None``。
    """
    if not is_dag(graph):
        return None

    deg = in_degree(graph)
    queue = deque(n for n, d in deg.items() if d == 0)
    result: list[str] = []

    # 这里同样使用 Kahn 剥离顺序，使结果尽量贴近节点注册顺序。
    while queue:
        u = queue.popleft()
        result.append(u)
        for v in graph.successors(u):
            deg[v] -= 1
            if deg[v] == 0:
                queue.append(v)

    return result


def compute_node_levels(graph: OrderGraph) -> dict[str, int]:
    """
    计算每个节点的最早执行层级。

    算法先构建 SCC 凝聚图，再在该 DAG 上逐层传播 level。
    同一 SCC 内的节点共享同一个层级。

    :param graph: 输入图。
    :return: ``{node: level}``。
    """
    cond, sccs = get_condensation(graph)
    cond_order = topo_sort(cond)
    if cond_order is None:
        raise ValueError("condensation graph must be a DAG")

    # 凝聚图一定是 DAG，因此可以安全地逐层传播 level。
    scc_level: dict[str, int] = dict.fromkeys(cond.nodes, 0)
    for node in cond_order:
        for succ in cond.out_edges.get(node, []):
            scc_level[succ] = max(scc_level[succ], scc_level[node] + 1)

    level: dict[str, int] = {}
    for i, scc in enumerate(sccs):
        lv = scc_level[f"scc_{i}"]
        for original_node in scc:
            level[original_node] = lv

    return level
