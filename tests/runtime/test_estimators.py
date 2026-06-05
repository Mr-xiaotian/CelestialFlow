from __future__ import annotations

import networkx as nx
import pytest

from celestialflow.runtime.util_estimators import (
    calc_elapsed,
    calc_global_pending,
    calc_remaining,
)
from celestialflow.runtime.util_types import StageStatus


class TestCalcRemaining:
    """calc_remaining — 基于已处理/待处理/已耗时估算剩余时间。"""

    def test_normal_case(self):
        """正常计算：processed=100, pending=50, elapsed=10 -> 5.0。"""
        result = calc_remaining(100, 50, 10)
        assert result == 5.0

    def test_pending_zero_returns_zero(self):
        """pending=0 时剩余时间为 0。"""
        result = calc_remaining(100, 0, 10)
        assert result == 0

    def test_processed_zero_returns_zero(self):
        """processed=0 时无法计算速度，返回 0。"""
        result = calc_remaining(0, 100, 10)
        assert result == 0

    def test_all_zero_returns_zero(self):
        """全部为 0 时返回 0。"""
        result = calc_remaining(0, 0, 0)
        assert result == 0

    def test_float_inputs(self):
        """浮点数输入应保持同样的比例关系。"""
        result = calc_remaining(50.0, 10.0, 3.5)
        assert result == pytest.approx(0.7)

    def test_processed_zero_float(self):
        """processed 为 0.0 时同样返回 0。"""
        result = calc_remaining(0.0, 50.0, 10.0)
        assert result == 0

    def test_pending_zero_float(self):
        """pending 为 0.0 时同样返回 0。"""
        result = calc_remaining(50.0, 0.0, 10.0)
        assert result == 0


class TestCalcElapsed:
    """calc_elapsed — 根据节点状态和上一轮 pending 决定是否累加耗时。"""

    def test_running_with_pending(self):
        """RUNNING 且上一轮 pending>0 时累加 interval。"""
        result = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=10.0, last_pending=5, interval=2.0
        )
        assert result == 12.0

    def test_running_without_pending(self):
        """RUNNING 且上一轮 pending=0 时保持原值。"""
        result = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=10.0, last_pending=0, interval=2.0
        )
        assert result == 10.0

    def test_stopped_with_pending(self):
        """STOPPED 且上一轮 pending>0 时仍会补记一个 interval。"""
        result = calc_elapsed(
            StageStatus.STOPPED, last_elapsed=15.0, last_pending=3, interval=5.0
        )
        assert result == 20.0

    def test_stopped_without_pending(self):
        """STOPPED 且上一轮 pending=0 时不再累加。"""
        result = calc_elapsed(
            StageStatus.STOPPED, last_elapsed=15.0, last_pending=0, interval=5.0
        )
        assert result == 15.0

    def test_not_started_returns_zero(self):
        """NOT_STARTED 会直接重置为 0。"""
        result = calc_elapsed(
            StageStatus.NOT_STARTED, last_elapsed=100.0, last_pending=50, interval=10.0
        )
        assert result == 0

    def test_consecutive_calls_simulate_time_progression(self):
        """连续调用时，仅在上一轮有 pending 时累加耗时。"""
        # 第1次：刚启动，还没有 pending 快照 → 不累加
        e1 = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=0.0, last_pending=0, interval=1.0
        )
        assert e1 == 0.0

        # 第2次：上一轮有 pending → 累加
        e2 = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=e1, last_pending=100, interval=1.0
        )
        assert e2 == 1.0

        # 第3次：继续累加
        e3 = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=e2, last_pending=80, interval=1.0
        )
        assert e3 == 2.0

        # 第4次：pending 变为 0 → 不累加
        e4 = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=e3, last_pending=0, interval=1.0
        )
        assert e4 == 2.0

    def test_not_started_then_running(self):
        """NOT_STARTED 重置后，切换到 RUNNING 可重新开始累计。"""
        # 状态从 NOT_STARTED 开始
        e1 = calc_elapsed(
            StageStatus.NOT_STARTED, last_elapsed=5.0, last_pending=10, interval=2.0
        )
        assert e1 == 0

        # 切换到 RUNNING
        e2 = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=e1, last_pending=10, interval=2.0
        )
        assert e2 == 2.0



def _make_linear_chain(
    nodes: list[str],
    proc: int = 100,
    pend: int = 50,
) -> tuple[nx.DiGraph[str], dict[str, int], dict[str, int]]:
    """构建线性链图 A->B->C...，并返回统一的 processed/pending 映射。"""
    G = nx.DiGraph()
    for i, n in enumerate(nodes):
        G.add_node(n)
        if i > 0:
            G.add_edge(nodes[i - 1], n)
    pmap = {n: proc for n in nodes}
    pendmap = {n: pend for n in nodes}
    return G, pmap, pendmap


class TestCalcGlobalPending:
    """calc_global_pending — 基于 DAG 传播估算各节点的全局待处理量。"""

    def test_single_node_no_preds(self):
        """单节点无上游时，估算值应退化为本节点当前 pending。"""
        G = nx.DiGraph()
        G.add_node("A")
        result = calc_global_pending(
            G,
            processed_map={"A": 100},
            pending_map={"A": 50},
        )
        assert result == {"A": 50}

    def test_single_node_all_zero(self):
        """单节点全零输入时应返回 0。"""
        G = nx.DiGraph()
        G.add_node("A")
        result = calc_global_pending(
            G,
            processed_map={"A": 0},
            pending_map={"A": 0},
        )
        assert result == {"A": 0}

    def test_linear_chain_three_nodes(self):
        """线性链 A->B->C 中，全局 pending 应沿链路逐级放大。"""
        G, pmap, pendmap = _make_linear_chain(["A", "B", "C"])
        result = calc_global_pending(G, pmap, pendmap)
        # 手工推算：
        # A: seen=150,total=150,scale=150/max(1,100)=1.5,
        #    expect_pend=max(50,150-100)=50
        # B: seen=150,total=150*1.5=225,scale=225/100=2.25,
        #    expect_pend=max(50,225-100)=125
        # C: seen=150,total=150*2.25=337.5,scale=337.5/100=3.375,
        #    expect_pend=max(50,337.5-100)=237.5 -> int(...) == 237
        assert result["A"] == 50
        assert result["B"] == 125
        assert result["C"] == 237

    def test_fan_out_one_to_many(self):
        """扇出 A->B, A->C 时，同层子节点应获得相同估算值。"""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("A", "C")])
        pmap = {n: 100 for n in ("A", "B", "C")}
        pendmap = {n: 50 for n in ("A", "B", "C")}

        result = calc_global_pending(G, pmap, pendmap)
        # A: seen=150,total=150,scale=1.5, expect_pend=50
        # B/C: seen=150,total=150*1.5=225, expect_pend=max(50,225-100)=125
        # 扇出不会拆分上游 scale，两个子节点各自独立继承同样的放大系数
        assert result["A"] == 50
        assert result["B"] == 125
        assert result["C"] == 125
        assert result["B"] == result["C"]

    def test_fan_in_many_to_one(self):
        """扇入 A->C, B->C 时，下游节点应聚合所有上游的放大结果。"""
        G = nx.DiGraph()
        G.add_edges_from([("A", "C"), ("B", "C")])
        pmap = {"A": 100, "B": 100, "C": 200}
        pendmap = {"A": 50, "B": 50, "C": 100}

        result = calc_global_pending(G, pmap, pendmap)
        # A: seen=150,total=150,scale=1.5, expect_pend=50
        # B: seen=150,total=150,scale=1.5, expect_pend=50
        # C: seen=300,k=2,obs_each=150
        #    total=150*1.5 + 150*1.5 = 450
        #    scale=450/max(1,200)=2.25
        #    expect_pend=max(100,450-200)=250
        assert result["A"] == 50
        assert result["B"] == 50
        assert result["C"] == 250

    def test_diamond_structure(self):
        """菱形结构中，末端节点应同时吸收来自两路上游的放大。"""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])
        pmap = {n: 100 for n in ("A", "B", "C", "D")}
        pendmap = {n: 50 for n in ("A", "B", "C", "D")}

        result = calc_global_pending(G, pmap, pendmap)
        # A: seen=150,total=150,scale=1.5, expect_pend=50
        # B/C: seen=150,total=150*1.5=225,scale=2.25, expect_pend=125
        # D: seen=150,k=2,obs_each=75
        #    total=75*2.25 + 75*2.25 = 337.5
        #    expect_pend=max(50,337.5-100)=237.5 -> int(...) == 237
        assert result["A"] == 50
        assert result["B"] == 125
        assert result["C"] == 125
        assert result["D"] == 237
        assert result["B"] == result["C"]

    def test_node_with_zero_processed(self):
        """单节点 processed=0 且 pending>0 时，应至少保留当前 pending。"""
        G = nx.DiGraph()
        G.add_node("A")
        result = calc_global_pending(
            G,
            processed_map={"A": 0},
            pending_map={"A": 100},
        )
        assert result["A"] == 100

    def test_all_nodes_zero_processed_still_propagates_pending(self):
        """即使全链路 processed=0，当前 pending 也会继续沿链路放大传播。"""
        G, _, pendmap = _make_linear_chain(["A", "B", "C"], proc=0)
        result = calc_global_pending(
            G, {"A": 0, "B": 0, "C": 0}, pendmap
        )
        # A: seen=50,total=50,scale=50/max(1,0)=50, expect_pend=50
        # B: seen=50,total=50*50=2500,scale=2500, expect_pend=2500
        # C: seen=50,total=50*2500=125000, expect_pend=125000
        assert result["A"] == 50
        assert result["A"] < result["B"] < result["C"]

    def test_uniform_distribution(self):
        """均匀输入下，线性链应保持严格递增的保守估算。"""
        G, pmap, pendmap = _make_linear_chain(["A", "B", "C"])
        result = calc_global_pending(G, pmap, pendmap)
        assert result["A"] < result["B"] < result["C"]

    def test_bottleneck_node_large_pending(self):
        """下游瓶颈 pending 极大时，应显著推高该节点的估算值。"""
        G = nx.DiGraph()
        G.add_edge("A", "B")
        pmap = {"A": 100, "B": 10}
        pendmap = {"A": 50, "B": 1000}

        result = calc_global_pending(G, pmap, pendmap)
        # A: seen=150,total=150,scale=1.5, expect_pend=50
        # B: seen=1010,total=1010*1.5=1515
        #    scale=1515/max(1,10)=151.5
        #    expect_pend=max(1000,1515-10)=1505
        assert result["A"] == 50
        assert result["B"] == 1505
        assert result["B"] > result["A"] * 10

    def test_result_type_is_dict_str_int(self):
        """返回值应为 dict[str, int]，键与节点名一一对应。"""
        G = nx.DiGraph()
        G.add_edge("X", "Y")
        result = calc_global_pending(
            G,
            processed_map={"X": 100, "Y": 100},
            pending_map={"X": 50, "Y": 50},
        )
        assert isinstance(result, dict)
        assert set(result.keys()) == {"X", "Y"}
        for k, v in result.items():
            assert isinstance(k, str)
            assert isinstance(v, int)

    def test_no_negative_values(self):
        """所有返回值都应是非负整数。"""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])
        result = calc_global_pending(
            G,
            processed_map={"A": 100, "B": 50, "C": 20, "D": 10},
            pending_map={"A": 50, "B": 30, "C": 10, "D": 100},
        )
        for v in result.values():
            assert isinstance(v, int)
            assert v >= 0

    def test_upstream_no_data_downstream_has_pending(self):
        """上游完全无观测时，下游仍应至少保留自己的当前 pending。"""
        G = nx.DiGraph()
        G.add_edge("A", "B")
        result = calc_global_pending(
            G,
            processed_map={"A": 0, "B": 10},
            pending_map={"A": 0, "B": 50},
        )
        # A: seen=0,total=0,scale=0/max(1,0)=0, expect_pend=0
        # B: seen=60,total=60*scale(A)=0
        #    expect_pend=max(50,0-10)=50
        assert "A" in result
        assert "B" in result
        assert result["A"] == 0
        assert result["B"] == 50

    def test_upstream_has_pending_only_no_processed(self):
        """上游仅有 pending 无 processed 时，仍会形成强放大系数。"""
        G = nx.DiGraph()
        G.add_edge("A", "B")
        result = calc_global_pending(
            G,
            processed_map={"A": 0, "B": 50},
            pending_map={"A": 200, "B": 100},
        )
        # A: seen=200,total=200,scale=200/max(1,0)=200, expect_pend=200
        # B: seen=150,total=150*200=30000
        #    expect_pend=max(100,30000-50)=29950
        assert result["A"] == 200
        assert result["B"] == 29950

    def test_graph_nodes_superset_of_maps(self):
        """图中额外节点缺失观测时，应按默认 0 参与传播。"""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        result = calc_global_pending(
            G,
            processed_map={"A": 100, "C": 100},
            pending_map={"A": 50, "C": 50},
        )
        # B 缺失观测，因此按 proc=0, pend=0 处理：
        # A: seen=150,total=150,scale=1.5, expect_pend=50
        # B: seen=0,total=0*1.5=0,scale=0, expect_pend=0
        # C: seen=150,total=150*0=0, expect_pend=max(50,0-100)=50
        assert "B" in result
        assert result["A"] == 50
        assert result["B"] == 0
        assert result["C"] == 50

    def test_empty_graph(self):
        """空图应返回空字典。"""
        G = nx.DiGraph()
        result = calc_global_pending(G, {}, {})
        assert result == {}


class TestPropertyBased:
    """属性验证：对称性、单调性等。"""

    def test_symmetric_linear_chains_same_estimate(self):
        """两条完全相同的独立线性链应得到完全相同的估算结果。"""
        G = nx.DiGraph()
        G.add_edges_from([("A1", "B1"), ("B1", "C1")])
        G.add_edges_from([("A2", "B2"), ("B2", "C2")])

        pmap = {}
        pendmap = {}
        for prefix in ("A", "B", "C"):
            for suffix in ("1", "2"):
                name = prefix + suffix
                pmap[name] = 100
                pendmap[name] = 50

        result = calc_global_pending(G, pmap, pendmap)
        assert result["A1"] == result["A2"]
        assert result["B1"] == result["B2"]
        assert result["C1"] == result["C2"]

    def test_monotonicity_increasing_pending(self):
        """增加 pending 不应减少全局 pending 估算值。"""
        G = nx.DiGraph()
        G.add_edge("A", "B")

        # 基准
        r1 = calc_global_pending(
            G,
            processed_map={"A": 100, "B": 100},
            pending_map={"A": 50, "B": 50},
        )

        # pending 增加
        r2 = calc_global_pending(
            G,
            processed_map={"A": 100, "B": 100},
            pending_map={"A": 100, "B": 100},
        )

        # pending 大幅增加
        r3 = calc_global_pending(
            G,
            processed_map={"A": 100, "B": 100},
            pending_map={"A": 200, "B": 200},
        )

        assert r2["A"] >= r1["A"]
        assert r2["B"] >= r1["B"]
        assert r3["A"] >= r2["A"]
        assert r3["B"] >= r2["B"]

    def test_monotonicity_increasing_processed_reduces_estimate(self):
        """单节点上增加 processed 不应增加估算值，最多保持不变。"""
        G = nx.DiGraph()
        G.add_node("A")

        r1 = calc_global_pending(
            G,
            processed_map={"A": 100},
            pending_map={"A": 100},
        )

        # processed 增加，pending 和 elapsed 不变
        r2 = calc_global_pending(
            G,
            processed_map={"A": 200},
            pending_map={"A": 100},
        )

        assert r2["A"] <= r1["A"]
