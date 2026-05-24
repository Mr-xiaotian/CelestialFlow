from __future__ import annotations

import networkx as nx
import pytest

from celestialflow.runtime.util_estimators import (
    calc_elapsed,
    calc_global_remain_equal_pred,
    calc_remaining,
)
from celestialflow.runtime.util_types import StageStatus


class TestCalcRemaining:
    """calc_remaining — 基于已处理/待处理/已耗时估算剩余时间"""

    def test_normal_case(self):
        """正常计算：processed=100, pending=50, elapsed=10 → 5.0"""
        result = calc_remaining(100, 50, 10)
        assert result == 5.0

    def test_pending_zero_returns_zero(self):
        """pending=0 → 剩余时间为 0（无事可做）"""
        result = calc_remaining(100, 0, 10)
        assert result == 0

    def test_processed_zero_returns_zero(self):
        """processed=0 → 无法计算速度，返回 0"""
        result = calc_remaining(0, 100, 10)
        assert result == 0

    def test_all_zero_returns_zero(self):
        """全部为 0 → 返回 0"""
        result = calc_remaining(0, 0, 0)
        assert result == 0

    def test_float_inputs(self):
        """浮点数输入验证：10.0/50.0*3.5 = 0.7"""
        result = calc_remaining(50.0, 10.0, 3.5)
        assert result == pytest.approx(0.7)

    def test_processed_zero_float(self):
        """processed 为 0.0（float）同样被视为 falsy"""
        result = calc_remaining(0.0, 50.0, 10.0)
        assert result == 0

    def test_pending_zero_float(self):
        """pending 为 0.0（float）同样被视为 falsy"""
        result = calc_remaining(50.0, 0.0, 10.0)
        assert result == 0


class TestCalcElapsed:
    """calc_elapsed — 根据节点状态和活跃标志累加耗时"""

    def test_running_with_pending(self):
        """RUNNING + pending>0 → 累加 interval"""
        result = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=10.0, last_pending=5, interval=2.0
        )
        assert result == 12.0

    def test_running_without_pending(self):
        """RUNNING + pending=0 → 不累加，保持原值"""
        result = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=10.0, last_pending=0, interval=2.0
        )
        assert result == 10.0

    def test_stopped_with_pending(self):
        """STOPPED + pending>0 → 仍累加（之前活跃过）"""
        result = calc_elapsed(
            StageStatus.STOPPED, last_elapsed=15.0, last_pending=3, interval=5.0
        )
        assert result == 20.0

    def test_stopped_without_pending(self):
        """STOPPED + pending=0 → 不累加"""
        result = calc_elapsed(
            StageStatus.STOPPED, last_elapsed=15.0, last_pending=0, interval=5.0
        )
        assert result == 15.0

    def test_not_started_returns_zero(self):
        """NOT_STARTED → 始终返回 0（忽略其他参数）"""
        result = calc_elapsed(
            StageStatus.NOT_STARTED, last_elapsed=100.0, last_pending=50, interval=10.0
        )
        assert result == 0

    def test_consecutive_calls_simulate_time_progression(self):
        """连续多次调用模拟时序推进"""
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
        """NOT_STARTED 重置为 0 后，切换到 RUNNING 重新计时"""
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


# ── helpers for DAG tests ────────────────────────────────────────────


def _make_linear_chain(
    nodes: list[str],
    proc: int = 100,
    pend: int = 50,
    elapsed: float = 10.0,
) -> tuple[nx.DiGraph[str], dict[str, int], dict[str, int], dict[str, float]]:
    """构建线性链图 A→B→C→... 并返回统一的 maps"""
    G = nx.DiGraph()
    for i, n in enumerate(nodes):
        G.add_node(n)
        if i > 0:
            G.add_edge(nodes[i - 1], n)
    pmap = {n: proc for n in nodes}
    pendmap = {n: pend for n in nodes}
    emap = {n: elapsed for n in nodes}
    return G, pmap, pendmap, emap


class TestCalcGlobalRemainEqualPred:
    """calc_global_remain_equal_pred — DAG 传播算法核心测试"""

    # ── 1. 单节点 ─────────────────────────────────────────────────

    def test_single_node_no_preds(self):
        """单节点无上下游，直接基于自身数据计算剩余时间"""
        G = nx.DiGraph()
        G.add_node("A")
        result = calc_global_remain_equal_pred(
            G,
            processed_map={"A": 100},
            pending_map={"A": 50},
            elapsed_map={"A": 10.0},
        )
        assert result == {"A": 5.0}

    def test_single_node_all_zero(self):
        """单节点全零数据 → 返回 0"""
        G = nx.DiGraph()
        G.add_node("A")
        result = calc_global_remain_equal_pred(
            G,
            processed_map={"A": 0},
            pending_map={"A": 0},
            elapsed_map={"A": 0.0},
        )
        assert result == {"A": 0.0}

    # ── 2. 线性链 A→B→C ───────────────────────────────────────────

    def test_linear_chain_three_nodes(self):
        """线性链 A→B→C：scale 沿链逐级放大"""
        # 手工推算：
        # A: seen=150,total=150,scale=1.5, expect_pend=max(50,50)=50, rem=5.0
        # B: seen=150,obs_each=150,total=150*1.5=225,scale=2.25, expect_pend=max(50,125)=125, rem=12.5
        # C: seen=150,obs_each=150,total=150*2.25=337.5,scale=3.375, expect_pend=max(50,237.5)=237.5, rem=23.75
        G, pmap, pendmap, emap = _make_linear_chain(["A", "B", "C"])
        result = calc_global_remain_equal_pred(G, pmap, pendmap, emap)
        assert result["A"] == 5.0
        assert result["B"] == 12.5
        assert result["C"] == 23.75

    # ── 3. 扇出 A→B, A→C ──────────────────────────────────────────

    def test_fan_out_one_to_many(self):
        """扇出 A→B, A→C：等贡献假设下 B 和 C 收到相同预测负载"""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("A", "C")])
        pmap = {n: 100 for n in ("A", "B", "C")}
        pendmap = {n: 50 for n in ("A", "B", "C")}
        emap = {n: 10.0 for n in ("A", "B", "C")}

        result = calc_global_remain_equal_pred(G, pmap, pendmap, emap)
        # A: 5.0, B: 12.5, C: 12.5
        assert result["A"] == 5.0
        assert result["B"] == 12.5
        assert result["C"] == 12.5
        # 两个子节点相同
        assert result["B"] == result["C"]

    # ── 4. 扇入 A→C, B→C ──────────────────────────────────────────

    def test_fan_in_many_to_one(self):
        """扇入 A→C, B→C：多上游合并计算"""
        G = nx.DiGraph()
        G.add_edges_from([("A", "C"), ("B", "C")])
        # C 的 proc=200, pend=100 是因为它聚合了两个上游的输出
        pmap = {"A": 100, "B": 100, "C": 200}
        pendmap = {"A": 50, "B": 50, "C": 100}
        emap = {"A": 10.0, "B": 10.0, "C": 20.0}

        result = calc_global_remain_equal_pred(G, pmap, pendmap, emap)
        # A: seen=150, total=150, scale=1.5, expect_pend=50, rem=5.0
        # B: seen=150, total=150, scale=1.5, expect_pend=50, rem=5.0
        # C: seen=300, k=2, obs_each=150, total=150*1.5+150*1.5=450,
        #    scale=450/200=2.25, expect_pend=max(100,250)=250, rem=250/200*20=25.0
        assert result["A"] == 5.0
        assert result["B"] == 5.0
        assert result["C"] == 25.0

    # ── 5. 菱形结构 ───────────────────────────────────────────────

    def test_diamond_structure(self):
        """菱形 A→B, A→C, B→D, C→D：两级传播验证"""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])
        pmap = {n: 100 for n in ("A", "B", "C", "D")}
        pendmap = {n: 50 for n in ("A", "B", "C", "D")}
        emap = {n: 10.0 for n in ("A", "B", "C", "D")}

        result = calc_global_remain_equal_pred(G, pmap, pendmap, emap)
        # A: 5.0, B: 12.5, C: 12.5, D: 23.75
        assert result["A"] == 5.0
        assert result["B"] == 12.5
        assert result["C"] == 12.5
        assert result["D"] == 23.75
        # B 和 C 同级，应相等
        assert result["B"] == result["C"]

    # ── 6. 空 processed 节点 ───────────────────────────────────────

    def test_node_with_zero_processed(self):
        """processed=0 的节点：expected_remain_time=0（无历史速度）"""
        G = nx.DiGraph()
        G.add_node("A")
        result = calc_global_remain_equal_pred(
            G,
            processed_map={"A": 0},
            pending_map={"A": 100},
            elapsed_map={"A": 5.0},
        )
        # proc=0 → calc_remaining(0, expect_pend, 5.0) = 0
        assert result["A"] == 0.0

    # ── 7. 所有节点 processed=0 ────────────────────────────────────

    def test_all_nodes_zero_processed(self):
        """所有节点 processed=0 → 全部返回 0"""
        G, _, pendmap, emap = _make_linear_chain(["A", "B", "C"], proc=0)
        result = calc_global_remain_equal_pred(
            G, {"A": 0, "B": 0, "C": 0}, pendmap, emap
        )
        assert all(v == 0.0 for v in result.values())

    # ── 8. 均匀分布 ────────────────────────────────────────────────

    def test_uniform_distribution(self):
        """每个节点 processed=pending=100, elapsed=10 → 验证一致性"""
        G, pmap, pendmap, emap = _make_linear_chain(["A", "B", "C"])
        result = calc_global_remain_equal_pred(G, pmap, pendmap, emap)
        # 上坡验证：A < B < C
        assert result["A"] < result["B"] < result["C"]

    # ── 9. 瓶颈节点 ────────────────────────────────────────────────

    def test_bottleneck_node_large_pending(self):
        """下游节点 pending 远大于上游 processed → scale 放大"""
        G = nx.DiGraph()
        G.add_edge("A", "B")
        pmap = {"A": 100, "B": 10}
        pendmap = {"A": 50, "B": 1000}
        emap = {"A": 10.0, "B": 1.0}

        result = calc_global_remain_equal_pred(G, pmap, pendmap, emap)
        # A: seen=150, total=150, scale=1.5, expect_pend=50, rem=5.0
        # B: seen=1010, obs_each=1010, total=1010*1.5=1515,
        #    scale=1515/10=151.5, expect_pend=max(1000,1505)=1505,
        #    rem=1505/10*1=150.5
        assert result["A"] == 5.0
        assert result["B"] == 150.5
        # B 的预估时间远大于 A
        assert result["B"] > result["A"] * 10

    # ── 10. 返回值类型验证 ─────────────────────────────────────────

    def test_result_type_is_dict_str_float(self):
        """返回值是 dict[str, float]，键与节点名一一对应"""
        G = nx.DiGraph()
        G.add_edge("X", "Y")
        result = calc_global_remain_equal_pred(
            G,
            processed_map={"X": 100, "Y": 100},
            pending_map={"X": 50, "Y": 50},
            elapsed_map={"X": 10.0, "Y": 10.0},
        )
        assert isinstance(result, dict)
        assert set(result.keys()) == {"X", "Y"}
        for k, v in result.items():
            assert isinstance(k, str)
            assert isinstance(v, float)

    # ── 11. 无负值 ─────────────────────────────────────────────────

    def test_no_negative_values(self):
        """所有返回的时间值 >= 0"""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")])
        result = calc_global_remain_equal_pred(
            G,
            processed_map={"A": 100, "B": 50, "C": 20, "D": 10},
            pending_map={"A": 50, "B": 30, "C": 10, "D": 100},
            elapsed_map={"A": 10.0, "B": 5.0, "C": 2.0, "D": 1.0},
        )
        for v in result.values():
            assert v >= 0.0

    # ── 12. 上游无数据 ─────────────────────────────────────────────

    def test_upstream_no_data_downstream_has_pending(self):
        """上游 processed=0 但下游有 pending → 不崩溃，下游正常计算"""
        G = nx.DiGraph()
        G.add_edge("A", "B")
        result = calc_global_remain_equal_pred(
            G,
            processed_map={"A": 0, "B": 10},
            pending_map={"A": 0, "B": 50},
            elapsed_map={"A": 0.0, "B": 5.0},
        )
        # A: seen=0, total=0, scale=0.0, rem=0
        # B: seen=60, obs_each=60, total=60*0.0=0.0, scale=0.0,
        #    expect_pend=max(50,-10)=50, rem=50/10*5=25.0
        assert "A" in result
        assert "B" in result
        assert result["A"] == 0.0
        assert result["B"] == 25.0

    # ── 13. 上游无数据但放大型 ─────────────────────────────────────

    def test_upstream_has_pending_only_no_processed(self):
        """上游 proc=0 但有 pending：scale 放大，但下游 rem 仍有意义"""
        G = nx.DiGraph()
        G.add_edge("A", "B")
        result = calc_global_remain_equal_pred(
            G,
            processed_map={"A": 0, "B": 50},
            pending_map={"A": 200, "B": 100},
            elapsed_map={"A": 5.0, "B": 10.0},
        )
        # A: seen=200, total=200, scale=200.0, expect_pend=max(200,200)=200, rem=calc_remaining(0,200,5)=0
        # B: seen=150, obs_each=150, total=150*200=30000, scale=30000/50=600,
        #    expect_pend=max(100,29950)=29950, rem=29950/50*10=5990.0
        assert result["A"] == 0.0
        assert result["B"] == 5990.0

    # ── 14. 图中存在额外节点（图大于 map）──────────────────────────

    def test_graph_nodes_superset_of_maps(self):
        """图中节点超过 map 中的节点 → 缺失节点默认 0"""
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        # 只提供 A 和 C 的数据，B 缺失
        result = calc_global_remain_equal_pred(
            G,
            processed_map={"A": 100, "C": 100},
            pending_map={"A": 50, "C": 50},
            elapsed_map={"A": 10.0, "C": 10.0},
        )
        # B 使用默认值 proc=0, pend=0, elapsed=0
        # A: 5.0
        # B: seen=0, obs_each=0 (from A scale=1.5), total=0*1.5=0, scale=0.0, expect_pend=0, rem=0
        # C: seen=150, obs_each=150 (from B scale=0.0!!)... wait
        # Actually B has scale=0.0/max(1,0)=0.0, so C gets 150*0.0=0.0 total
        # expect_pend=max(50, -100)=50, rem=50/100*10=5.0
        assert "B" in result
        assert result["A"] == 5.0
        assert result["C"] == 5.0
        assert result["B"] == 0.0

    # ── 15. 空图 ───────────────────────────────────────────────────

    def test_empty_graph(self):
        """空图 → 返回空字典"""
        G = nx.DiGraph()
        result = calc_global_remain_equal_pred(G, {}, {}, {})
        assert result == {}


class TestPropertyBased:
    """属性验证：对称性、单调性等"""

    def test_symmetric_linear_chains_same_estimate(self):
        """两条完全相同的独立线性链应有相同的估算结果"""
        G = nx.DiGraph()
        G.add_edges_from([("A1", "B1"), ("B1", "C1")])
        G.add_edges_from([("A2", "B2"), ("B2", "C2")])

        pmap = {}
        pendmap = {}
        emap = {}
        for prefix in ("A", "B", "C"):
            for suffix in ("1", "2"):
                name = prefix + suffix
                pmap[name] = 100
                pendmap[name] = 50
                emap[name] = 10.0

        result = calc_global_remain_equal_pred(G, pmap, pendmap, emap)
        assert result["A1"] == result["A2"]
        assert result["B1"] == result["B2"]
        assert result["C1"] == result["C2"]

    def test_monotonicity_increasing_pending(self):
        """增加 pending 不应减少预估时间"""
        G = nx.DiGraph()
        G.add_edge("A", "B")

        # 基准
        r1 = calc_global_remain_equal_pred(
            G,
            processed_map={"A": 100, "B": 100},
            pending_map={"A": 50, "B": 50},
            elapsed_map={"A": 10.0, "B": 10.0},
        )

        # pending 增加
        r2 = calc_global_remain_equal_pred(
            G,
            processed_map={"A": 100, "B": 100},
            pending_map={"A": 100, "B": 100},
            elapsed_map={"A": 10.0, "B": 10.0},
        )

        # pending 大幅增加
        r3 = calc_global_remain_equal_pred(
            G,
            processed_map={"A": 100, "B": 100},
            pending_map={"A": 200, "B": 200},
            elapsed_map={"A": 10.0, "B": 10.0},
        )

        assert r2["A"] >= r1["A"]
        assert r2["B"] >= r1["B"]
        assert r3["A"] >= r2["A"]
        assert r3["B"] >= r2["B"]

    def test_monotonicity_increasing_processed_reduces_estimate(self):
        """增加 processed（已完成更多）不应增加预估时间（应该减少或不变）"""
        G = nx.DiGraph()
        G.add_node("A")

        r1 = calc_global_remain_equal_pred(
            G,
            processed_map={"A": 100},
            pending_map={"A": 100},
            elapsed_map={"A": 10.0},
        )

        # processed 增加，pending 和 elapsed 不变
        r2 = calc_global_remain_equal_pred(
            G,
            processed_map={"A": 200},
            pending_map={"A": 100},
            elapsed_map={"A": 10.0},
        )

        assert r2["A"] <= r1["A"]
