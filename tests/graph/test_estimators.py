from __future__ import annotations

import pytest

from celestialflow.graph.util_order_graph import OrderGraph
from celestialflow.graph.util_estimators import calc_global_pending
from celestialflow.runtime.util_estimators import calc_elapsed, calc_remaining
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
) -> tuple[OrderGraph, dict[str, int], dict[str, int]]:
    """构建线性链图 A->B->C...，并返回统一的 processed/pending 映射。"""
    graph = OrderGraph()
    for i, n in enumerate(nodes):
        graph.add_node(n)
        if i > 0:
            graph.add_edge(nodes[i - 1], n)
    pmap = {n: proc for n in nodes}
    pendmap = {n: pend for n in nodes}
    return graph, pmap, pendmap


def _make_graph(edges: dict[str, list[str]]) -> OrderGraph:
    """根据边定义构造用于分析的测试图（空邻接的键作为孤立节点保留）。"""
    graph = OrderGraph()
    for name in edges:
        graph.add_node(name)
    for u, targets in edges.items():
        for v in targets:
            graph.add_edge(u, v)
    return graph


class TestCalcGlobalPending:
    """calc_global_pending — 基于 DAG 传播估算各节点的全局待处理量。"""

    def test_single_node_no_preds(self):
        """单节点无上游时，估算值应退化为本节点当前 pending。"""
        graph = OrderGraph()
        graph.add_node("A")
        result = calc_global_pending(
            graph,
            processed_map={"A": 100},
            pending_map={"A": 50},
            downstream_map={},
        )
        assert result == {"A": 50}

    def test_single_node_all_zero(self):
        """单节点全零输入时应返回 0。"""
        graph = OrderGraph()
        graph.add_node("A")
        result = calc_global_pending(
            graph,
            processed_map={"A": 0},
            pending_map={"A": 0},
            downstream_map={},
        )
        assert result == {"A": 0}

    def test_linear_chain_three_nodes(self):
        """线性链 A->B->C 中，全局 pending 应沿链路逐级放大。"""
        graph, pmap, pendmap = _make_linear_chain(["A", "B", "C"])
        downstream = {"A": {"B": 150}, "B": {"C": 150}}
        result = calc_global_pending(graph, pmap, pendmap, downstream_map=downstream)
        # 手工推算（上游各发送 150，external=0）：
        # A: seen=150,total=150,scale[A][B]=150*150/100=225
        #    expect_pend=max(50,150-100)=50
        # B: seen=150,total=225,scale[B][C]=225*150/100=337.5
        #    expect_pend=max(50,225-100)=125
        # C: total=337.5
        #    expect_pend=max(50,337.5-100)=237.5 -> int(...) == 237
        assert result["A"] == 50
        assert result["B"] == 125
        assert result["C"] == 237

    def test_fan_out_one_to_many(self):
        """扇出 A->B, A->C 时，同层子节点应获得相同估算值。"""
        graph = _make_graph({"A": ["B", "C"]})
        pmap = {n: 100 for n in ("A", "B", "C")}
        pendmap = {n: 50 for n in ("A", "B", "C")}
        downstream = {"A": {"B": 150, "C": 150}}

        result = calc_global_pending(graph, pmap, pendmap, downstream_map=downstream)
        # A: seen=150,total=150,scale[A][B]=scale[A][C]=225, expect_pend=50
        # B/C: seen=150,total=225, expect_pend=max(50,225-100)=125
        # 扇出不会拆分放大，两个子节点各自独立继承同样的输出比例
        assert result["A"] == 50
        assert result["B"] == 125
        assert result["C"] == 125
        assert result["B"] == result["C"]

    def test_fan_in_many_to_one(self):
        """扇入 A->C, B->C 时，下游节点应聚合所有上游的放大结果。"""
        graph = _make_graph({"A": ["C"], "B": ["C"]})
        pmap = {"A": 100, "B": 100, "C": 200}
        pendmap = {"A": 50, "B": 50, "C": 100}
        downstream = {"A": {"C": 150}, "B": {"C": 150}}

        result = calc_global_pending(graph, pmap, pendmap, downstream_map=downstream)
        # A: seen=150,total=150,scale[A][C]=225, expect_pend=50
        # B: seen=150,total=150,scale[B][C]=225, expect_pend=50
        # C: seen=300, 上游各发 150 (external=0)
        #    total=225+225=450
        #    expect_pend=max(100,450-200)=250
        assert result["A"] == 50
        assert result["B"] == 50
        assert result["C"] == 250

    def test_diamond_structure(self):
        """菱形结构中，末端节点应同时吸收来自两路上游的放大。"""
        graph = _make_graph({"A": ["B", "C"], "B": ["D"], "C": ["D"]})
        pmap = {n: 100 for n in ("A", "B", "C", "D")}
        pendmap = {n: 50 for n in ("A", "B", "C", "D")}
        downstream = {
            "A": {"B": 150, "C": 150},
            "B": {"D": 75},
            "C": {"D": 75},
        }

        result = calc_global_pending(graph, pmap, pendmap, downstream_map=downstream)
        # A: total=150, scale[A][B]=scale[A][C]=225, expect_pend=50
        # B/C: total=225, scale[B][D]=scale[C][D]=225*75/100=168.75, expect_pend=125
        # D: seen=150, 上游各发 75 (external=0)
        #    total=168.75+168.75=337.5
        #    expect_pend=max(50,337.5-100)=237.5 -> int(...) == 237
        assert result["A"] == 50
        assert result["B"] == 125
        assert result["C"] == 125
        assert result["D"] == 237
        assert result["B"] == result["C"]

    def test_node_with_zero_processed(self):
        """单节点 processed=0 且 pending>0 时，应至少保留当前 pending。"""
        graph = OrderGraph()
        graph.add_node("A")
        result = calc_global_pending(
            graph,
            processed_map={"A": 0},
            pending_map={"A": 100},
            downstream_map={},
        )
        assert result["A"] == 100

    def test_all_nodes_zero_processed_still_propagates_pending(self):
        """即使全链路 processed=0，当前 pending 也会继续沿链路放大传播。"""
        graph, _, pendmap = _make_linear_chain(["A", "B", "C"], proc=0)
        downstream = {"A": {"B": 50}, "B": {"C": 50}}
        result = calc_global_pending(
            graph,
            {"A": 0, "B": 0, "C": 0},
            pendmap,
            downstream_map=downstream,
        )
        # A: seen=50,total=50,scale[A][B]=50*50/max(1,0)=2500, expect_pend=50
        # B: seen=50,total=2500,scale[B][C]=2500*50/max(1,0)=125000, expect_pend=2500
        # C: total=125000, expect_pend=125000
        assert result["A"] == 50
        assert result["A"] < result["B"] < result["C"]

    def test_uniform_distribution(self):
        """均匀输入下，线性链应保持严格递增的保守估算。"""
        graph, pmap, pendmap = _make_linear_chain(["A", "B", "C"])
        downstream = {"A": {"B": 150}, "B": {"C": 150}}
        result = calc_global_pending(graph, pmap, pendmap, downstream_map=downstream)
        assert result["A"] < result["B"] < result["C"]

    def test_bottleneck_node_large_pending(self):
        """下游瓶颈 pending 极大时，应显著推高该节点的估算值。"""
        graph = _make_graph({"A": ["B"]})
        pmap = {"A": 100, "B": 10}
        pendmap = {"A": 50, "B": 1000}
        downstream = {"A": {"B": 1010}}

        result = calc_global_pending(graph, pmap, pendmap, downstream_map=downstream)
        # A: seen=150,total=150,scale[A][B]=150*1010/100=1515, expect_pend=50
        # B: seen=1010,total=1515
        #    expect_pend=max(1000,1515-10)=1505
        assert result["A"] == 50
        assert result["B"] == 1505
        assert result["B"] > result["A"] * 10

    def test_result_type_is_dict_str_int(self):
        """返回值应为 dict[str, int]，键与节点名一一对应。"""
        graph = _make_graph({"X": ["Y"]})
        downstream = {"X": {"Y": 150}}
        result = calc_global_pending(
            graph,
            processed_map={"X": 100, "Y": 100},
            pending_map={"X": 50, "Y": 50},
            downstream_map=downstream,
        )
        assert isinstance(result, dict)
        assert set(result.keys()) == {"X", "Y"}
        for k, v in result.items():
            assert isinstance(k, str)
            assert isinstance(v, int)

    def test_no_negative_values(self):
        """所有返回值都应是非负整数。"""
        graph = _make_graph({"A": ["B", "C"], "B": ["D"], "C": ["D"]})
        downstream = {
            "A": {"B": 80, "C": 30},
            "B": {"D": 60},
            "C": {"D": 50},
        }
        result = calc_global_pending(
            graph,
            processed_map={"A": 100, "B": 50, "C": 20, "D": 10},
            pending_map={"A": 50, "B": 30, "C": 10, "D": 100},
            downstream_map=downstream,
        )
        for v in result.values():
            assert isinstance(v, int)
            assert v >= 0

    def test_upstream_no_data_downstream_has_pending(self):
        """上游完全无观测时，下游仍应至少保留自己的当前 pending。"""
        graph = _make_graph({"A": ["B"]})
        downstream = {"A": {"B": 60}}
        result = calc_global_pending(
            graph,
            processed_map={"A": 0, "B": 10},
            pending_map={"A": 0, "B": 50},
            downstream_map=downstream,
        )
        # A: seen=0,total=0,scale[A][B]=0*60/max(1,0)=0, expect_pend=0
        # B: seen=60,total=0
        #    expect_pend=max(50,0-10)=50
        assert "A" in result
        assert "B" in result
        assert result["A"] == 0
        assert result["B"] == 50

    def test_upstream_has_pending_only_no_processed(self):
        """上游仅有 pending 无 processed 时，仍会形成强放大系数。"""
        graph = _make_graph({"A": ["B"]})
        downstream = {"A": {"B": 150}}
        result = calc_global_pending(
            graph,
            processed_map={"A": 0, "B": 50},
            pending_map={"A": 200, "B": 100},
            downstream_map=downstream,
        )
        # A: seen=200,total=200,scale[A][B]=200*150/max(1,0)=30000,
        #    expect_pend=200
        # B: seen=150,total=30000
        #    expect_pend=max(100,30000-50)=29950
        assert result["A"] == 200
        assert result["B"] == 29950

    def test_graph_nodes_superset_of_maps(self):
        """图中额外节点缺失观测时，应按默认 0 参与传播。"""
        graph = _make_graph({"A": ["B"], "B": ["C"]})
        downstream = {"A": {"B": 0}, "B": {"C": 150}}
        result = calc_global_pending(
            graph,
            processed_map={"A": 100, "C": 100},
            pending_map={"A": 50, "C": 50},
            downstream_map=downstream,
        )
        # B 缺失观测，因此按 proc=0, pend=0 处理：
        # A: seen=150,total=150,scale[A][B]=150*0/100=0, expect_pend=50
        # B: seen=0,total=0,scale[B][C]=0, expect_pend=0
        # C: seen=150,total=0, expect_pend=max(50,0-100)=50
        assert "B" in result
        assert result["A"] == 50
        assert result["B"] == 0
        assert result["C"] == 50

    def test_empty_graph(self):
        """空图应返回空字典。"""
        graph = OrderGraph()
        result = calc_global_pending(graph, {}, {}, downstream_map={})
        assert result == {}


class TestCalcGlobalPendingDetailed:
    """calc_global_pending — 利用逐下游真实输出量（downstream_map）的加权语义。"""

    def test_fan_in_weighted_by_real_output_ratios(self):
        """多上游 fan-in 应按各上游真实输出比例加权，而非等量均分。"""
        graph = _make_graph({"A": ["C"], "B": ["C"]})
        pmap = {"A": 100, "B": 100, "C": 100}
        pendmap = {"A": 500, "B": 0, "C": 50}

        # A: seen=600, total=600 ; B: seen=100, total=100
        # 真实输出 140/10: scale[A][C]=600*140/100=840, scale[B][C]=100*10/100=10
        # C: total=840+10=850, expect_pend=max(50, 850-100)=750
        result = calc_global_pending(
            graph, pmap, pendmap, downstream_map={"A": {"C": 140}, "B": {"C": 10}}
        )
        assert result["A"] == 500
        assert result["B"] == 0
        assert result["C"] == 750

        # 等量输出 75/75: scale[A][C]=450, scale[B][C]=75, total=525,
        #    expect_pend=425
        equal = calc_global_pending(
            graph, pmap, pendmap, downstream_map={"A": {"C": 75}, "B": {"C": 75}}
        )
        assert equal["C"] == 425
        assert result["C"] > equal["C"]

    def test_fan_out_per_downstream_ratios(self):
        """扇出对每个下游按独立输出比例放大，输出少的下游不随动。"""
        graph = _make_graph({"A": ["B", "C"]})
        pmap = {"A": 100, "B": 10, "C": 10}
        pendmap = {"A": 300, "B": 0, "C": 0}
        downstream = {"A": {"B": 40, "C": 10}}

        # A: seen=400, total=400
        #    scale[A][B]=400*40/100=160, scale[A][C]=400*10/100=40
        # B: total=160, expect_pend=max(0,160-10)=150
        # C: total=40,  expect_pend=max(0,40-10)=30
        result = calc_global_pending(graph, pmap, pendmap, downstream_map=downstream)
        assert result["A"] == 300
        assert result["B"] == 150
        assert result["C"] == 30

    def test_external_input_not_amplified_by_upstream_scale(self):
        """外部注入任务不应被上游 scale 放大。"""
        graph = _make_graph({"A": ["B"]})
        pmap = {"A": 10, "B": 100}
        pendmap = {"A": 90, "B": 0}

        # A: seen=100, total=100, scale[A][B]=100*40/max(1,10)=400
        # B: external=max(0,100-40)=60, total=60+400=460
        #    expect_pend=max(0, 460-100)=360
        result = calc_global_pending(
            graph, pmap, pendmap, downstream_map={"A": {"B": 40}}
        )
        assert result["A"] == 90
        assert result["B"] == 360

        # 若 100 全部视为上游输入: scale[A][B]=1000, total=1000
        #    expect_pend=max(0, 1000-100)=900（外部注入被错误放大）
        all_upstream = calc_global_pending(
            graph, pmap, pendmap, downstream_map={"A": {"B": 100}}
        )
        assert all_upstream["B"] == 900
        assert result["B"] < all_upstream["B"]

    def test_zero_processed_upstream_does_not_propagate(self):
        """上游 proc=0 未发送任何任务时，其 pending 不应放大下游。"""
        graph = _make_graph({"A": ["B"]})
        pmap = {"A": 0, "B": 5}
        pendmap = {"A": 100, "B": 5}
        # proc=0 且未发送(output=0)自洽：scale=0，下游不受上游 pending 影响
        downstream = {"A": {"B": 0}}

        result = calc_global_pending(graph, pmap, pendmap, downstream_map=downstream)
        # A: seen=100,total=100,scale[A][B]=100*0/max(1,0)=0, expect_pend=100
        # B: received=0, external=max(0,10-0)=10, total=10
        #    expect_pend=max(5,10-5)=5
        assert result["A"] == 100
        assert result["B"] == 5

    def test_single_upstream_without_external(self):
        """单上游且无外部注入时，上游输出量即等于已见任务量。"""
        graph = _make_graph({"A": ["B"]})
        pmap = {"A": 100, "B": 100}
        pendmap = {"A": 50, "B": 50}
        result = calc_global_pending(
            graph, pmap, pendmap, downstream_map={"A": {"B": 150}}
        )
        assert result == {"A": 50, "B": 125}

    def test_missing_downstream_data_treated_as_external(self):
        """缺失的逐下游数据按 0 处理，seen 整体归为外部注入。"""
        graph = _make_graph({"A": ["B"]})
        pmap = {"A": 100, "B": 100}
        pendmap = {"A": 50, "B": 50}
        # 数据缺失：A 未记录对 B 的输出 → 上游放大为 0，B 的 seen 视为外部注入
        result = calc_global_pending(graph, pmap, pendmap, downstream_map={})
        assert result == {"A": 50, "B": 50}

    def test_no_negative_values_with_downstream_map(self):
        """加权路径下所有返回值都应为非负整数。"""
        graph = _make_graph({"A": ["B", "C"], "B": ["D"], "C": ["D"]})
        pmap = {"A": 100, "B": 50, "C": 20, "D": 10}
        pendmap = {"A": 50, "B": 30, "C": 10, "D": 100}
        downstream = {
            "A": {"B": 60, "C": 40},
            "B": {"D": 2},
            "C": {"D": 1},
        }
        result = calc_global_pending(graph, pmap, pendmap, downstream_map=downstream)
        assert set(result.keys()) == {"A", "B", "C", "D"}
        for v in result.values():
            assert isinstance(v, int)
            assert v >= 0


class TestPropertyBased:
    """属性验证：对称性、单调性等。"""

    def test_symmetric_linear_chains_same_estimate(self):
        """两条完全相同的独立线性链应得到完全相同的估算结果。"""
        graph = _make_graph(
            {"A1": ["B1"], "B1": ["C1"], "A2": ["B2"], "B2": ["C2"]}
        )

        pmap = {}
        pendmap = {}
        for prefix in ("A", "B", "C"):
            for suffix in ("1", "2"):
                name = prefix + suffix
                pmap[name] = 100
                pendmap[name] = 50
        downstream = {
            "A1": {"B1": 150},
            "B1": {"C1": 150},
            "A2": {"B2": 150},
            "B2": {"C2": 150},
        }

        result = calc_global_pending(graph, pmap, pendmap, downstream_map=downstream)
        assert result["A1"] == result["A2"]
        assert result["B1"] == result["B2"]
        assert result["C1"] == result["C2"]

    def test_monotonicity_increasing_pending(self):
        """增加 pending 不应减少全局 pending 估算值。"""
        graph = _make_graph({"A": ["B"]})

        # 基准
        r1 = calc_global_pending(
            graph,
            processed_map={"A": 100, "B": 100},
            pending_map={"A": 50, "B": 50},
            downstream_map={"A": {"B": 150}},
        )

        # pending 增加
        r2 = calc_global_pending(
            graph,
            processed_map={"A": 100, "B": 100},
            pending_map={"A": 100, "B": 100},
            downstream_map={"A": {"B": 200}},
        )

        # pending 大幅增加
        r3 = calc_global_pending(
            graph,
            processed_map={"A": 100, "B": 100},
            pending_map={"A": 200, "B": 200},
            downstream_map={"A": {"B": 300}},
        )

        assert r2["A"] >= r1["A"]
        assert r2["B"] >= r1["B"]
        assert r3["A"] >= r2["A"]
        assert r3["B"] >= r2["B"]

    def test_monotonicity_increasing_processed_reduces_estimate(self):
        """单节点上增加 processed 不应增加估算值，最多保持不变。"""
        graph = OrderGraph()
        graph.add_node("A")

        r1 = calc_global_pending(
            graph,
            processed_map={"A": 100},
            pending_map={"A": 100},
            downstream_map={},
        )

        # processed 增加，pending 和 elapsed 不变
        r2 = calc_global_pending(
            graph,
            processed_map={"A": 200},
            pending_map={"A": 100},
            downstream_map={},
        )

        assert r2["A"] <= r1["A"]