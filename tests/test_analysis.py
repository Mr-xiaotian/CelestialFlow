import networkx as nx
import pytest

from celestialflow.graph.util_analysis import (
    build_networkx_graph,
    compute_node_levels,
    find_source_nodes,
)


# ========== 轻量 mock ==========
class _MockStage:
    def __init__(self, mode: str = "serial"):
        self._mode = mode

    def get_stage_mode(self) -> str:
        return self._mode


class _MockRuntime:
    def __init__(self, mode: str = "serial"):
        self.stage = _MockStage(mode)


def _make_graph(edges: dict[str, list[str]]) -> nx.DiGraph[str]:
    tags = set(edges.keys())
    for dsts in edges.values():
        tags.update(dsts)
    runtime = {t: _MockRuntime() for t in tags}
    return build_networkx_graph(edges, runtime)  # type: ignore[arg-type]


# =========================
# TestBuildNetworkxGraph
# =========================
class TestBuildNetworkxGraph:
    def test_linear(self):
        G = _make_graph({"A": ["B"], "B": ["C"], "C": []})
        assert len(G.nodes) == 3
        assert len(G.edges) == 2
        assert list(G.successors("A")) == ["B"]

    def test_cycle(self):
        G = _make_graph({"A": ["B"], "B": ["C"], "C": ["A"]})
        assert len(G.nodes) == 3
        assert len(G.edges) == 3
        assert "A" in G.successors("C")

    def test_isolated_node(self):
        G = _make_graph({"A": [], "B": []})
        assert len(G.nodes) == 2
        assert len(G.edges) == 0


# =========================
# TestComputeNodeLevels
# =========================
class TestComputeNodeLevels:
    def test_linear_dag(self):
        G = _make_graph({"A": ["B"], "B": ["C"], "C": []})
        levels = compute_node_levels(G)
        assert levels["A"] == 0
        assert levels["B"] == 1
        assert levels["C"] == 2

    def test_fan_out_dag(self):
        """A→{B,C}→D, B和C同层"""
        G = _make_graph({"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []})
        levels = compute_node_levels(G)
        assert levels["A"] == 0
        assert levels["B"] == levels["C"] == 1
        assert levels["D"] == 2

    def test_single_cycle(self):
        """A→B→C→A: 同一 SCC，共享层级"""
        G = _make_graph({"A": ["B"], "B": ["C"], "C": ["A"]})
        levels = compute_node_levels(G)
        assert levels["A"] == levels["B"] == levels["C"]

    def test_cycle_with_tail(self):
        """A→B→C→A, A→D: D 比环高一层"""
        G = _make_graph({"A": ["B", "D"], "B": ["C"], "C": ["A"], "D": []})
        levels = compute_node_levels(G)
        cycle_level = levels["A"]
        assert levels["B"] == cycle_level
        assert levels["C"] == cycle_level
        assert levels["D"] == cycle_level + 1

    def test_disconnected(self):
        """两条独立链各自从 0 开始"""
        G = _make_graph({"A": ["B"], "B": [], "X": ["Y"], "Y": []})
        levels = compute_node_levels(G)
        assert levels["A"] == 0
        assert levels["B"] == 1
        assert levels["X"] == 0
        assert levels["Y"] == 1


# =========================
# TestFindSourceNodes
# =========================
class TestFindSourceNodes:
    def test_linear_dag(self):
        G = _make_graph({"A": ["B"], "B": ["C"], "C": []})
        sources = find_source_nodes(G)
        assert len(sources) == 1
        assert sources[0] == "A"

    def test_multiple_sources(self):
        G = _make_graph({"A": ["C"], "B": ["C"], "C": []})
        sources = find_source_nodes(G)
        assert set(sources) == {"A", "B"}

    def test_pure_cycle(self):
        """纯环无 in_degree=0 节点，但整个 SCC 是一个 source"""
        G = _make_graph({"A": ["B"], "B": ["C"], "C": ["A"]})
        sources = find_source_nodes(G)
        assert len(sources) == 1
        assert sources[0] in {"A", "B", "C"}

    def test_wheel_topology(self):
        """Center→{R1,R2,R3}, R1→R2→R3→R1: center 是唯一 source"""
        G = _make_graph({
            "Center": ["R1", "R2", "R3"],
            "R1": ["R2"],
            "R2": ["R3"],
            "R3": ["R1"],
        })
        sources = find_source_nodes(G)
        assert sources == ["Center"]
