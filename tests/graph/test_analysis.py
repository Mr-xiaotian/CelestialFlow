from __future__ import annotations

from celestialflow.graph.util_graph import OrderGraph, compute_node_levels, source_nodes


def _make_graph(edges: dict[str, list[str]]) -> OrderGraph:
    """根据边定义构造用于分析的测试图。"""
    stage_names = set(edges.keys())
    for dsts in edges.values():
        stage_names.update(dsts)
    return OrderGraph.from_edges(edges, stage_names)


# ====================
# TestBuildOrderGraph
# ====================
class TestBuildOrderGraph:
    def test_linear(self):
        """测试线性结构的图构建"""
        graph = _make_graph({"A": ["B"], "B": ["C"], "C": []})
        assert len(graph.nodes) == 3
        assert sum(len(targets) for targets in graph.out_edges.values()) == 2
        assert list(graph.successors("A")) == ["B"]

    def test_cycle(self):
        """测试包含环的图构建"""
        graph = _make_graph({"A": ["B"], "B": ["C"], "C": ["A"]})
        assert len(graph.nodes) == 3
        assert sum(len(targets) for targets in graph.out_edges.values()) == 3
        assert "A" in graph.successors("C")

    def test_isolated_node(self):
        """测试包含孤立节点的图构建"""
        graph = _make_graph({"A": [], "B": []})
        assert len(graph.nodes) == 2
        assert sum(len(targets) for targets in graph.out_edges.values()) == 0


# =========================
# TestComputeNodeLevels
# =========================
class TestComputeNodeLevels:
    def test_linear_dag(self):
        """测试线性 DAG 的层级计算"""
        graph = _make_graph({"A": ["B"], "B": ["C"], "C": []})
        levels = compute_node_levels(graph)
        assert levels["A"] == 0
        assert levels["B"] == 1
        assert levels["C"] == 2

    def test_fan_out_dag(self):
        """测试扇出 DAG 的层级计算：A→{B,C}→D, B和C同层"""
        graph = _make_graph({"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []})
        levels = compute_node_levels(graph)
        assert levels["A"] == 0
        assert levels["B"] == levels["C"] == 1
        assert levels["D"] == 2

    def test_single_cycle(self):
        """测试简单环的层级计算：同一 SCC 共享层级"""
        graph = _make_graph({"A": ["B"], "B": ["C"], "C": ["A"]})
        levels = compute_node_levels(graph)
        assert levels["A"] == levels["B"] == levels["C"]

    def test_cycle_with_tail(self):
        """测试带尾巴的环层级计算：D 比环高一层"""
        graph = _make_graph({"A": ["B", "D"], "B": ["C"], "C": ["A"], "D": []})
        levels = compute_node_levels(graph)
        cycle_level = levels["A"]
        assert levels["B"] == cycle_level
        assert levels["C"] == cycle_level
        assert levels["D"] == cycle_level + 1

    def test_disconnected(self):
        """测试不连通图的层级计算：各部分独立从 0 开始"""
        graph = _make_graph({"A": ["B"], "B": [], "X": ["Y"], "Y": []})
        levels = compute_node_levels(graph)
        assert levels["A"] == 0
        assert levels["B"] == 1
        assert levels["X"] == 0
        assert levels["Y"] == 1


# =========================
# TestFindSourceNodes
# =========================
class TestFindSourceNodes:
    def test_linear_dag(self):
        """测试线性 DAG 的源节点查找"""
        graph = _make_graph({"A": ["B"], "B": ["C"], "C": []})
        sources = source_nodes(graph)
        assert len(sources) == 1
        assert sources[0] == "A"

    def test_multiple_sources(self):
        """测试多源节点的查找"""
        graph = _make_graph({"A": ["C"], "B": ["C"], "C": []})
        sources = source_nodes(graph)
        assert set(sources) == {"A", "B"}

    def test_pure_cycle(self):
        """测试纯环的源节点查找：SCC 作为 source 返回其中一个代表点"""
        graph = _make_graph({"A": ["B"], "B": ["C"], "C": ["A"]})
        sources = source_nodes(graph)
        assert len(sources) == 1
        assert sources[0] in {"A", "B", "C"}

    def test_wheel_topology(self):
        """测试轮状拓扑的源节点查找：Center 是唯一 source"""
        graph = _make_graph(
            {
                "Center": ["R1", "R2", "R3"],
                "R1": ["R2"],
                "R2": ["R3"],
                "R3": ["R1"],
            }
        )
        sources = source_nodes(graph)
        assert sources == ["Center"]
