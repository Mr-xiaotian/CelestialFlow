"""Tests for util_clone module."""

import pytest

from celestialflow.graph import TaskGraph
from celestialflow.stage import TaskExecutor, TaskStage
from celestialflow.runtime.util_event import LocalEventClient
from celestialflow.utils.util_clone import clone_executor, clone_graph, clone_stage


class TestUtilClone:
    """Tests for clone utilities: clone_executor, clone_stage, clone_graph."""

    # ── clone_executor ─────────────────────────────────────────────

    def test_clone_executor_same_attributes(self):
        """克隆后 name / func / execution_mode 与原对象相同。"""
        executor = TaskExecutor(
            name="test_exec",
            func=lambda x: x,
            execution_mode="thread",
            persist_result=True,
        )
        cloned = clone_executor(executor)

        assert cloned.get_name() == executor.get_name()
        assert cloned.func is executor.func
        assert cloned.execution_mode == executor.execution_mode
        assert cloned.persist_result == executor.persist_result

    def test_clone_executor_different_object(self):
        """克隆返回的是不同对象。"""
        executor = TaskExecutor(name="test_exec", func=lambda x: x)
        cloned = clone_executor(executor)

        assert cloned is not executor

    def test_clone_executor_independent(self):
        """修改克隆的 execution_mode 不影响原对象。"""
        executor = TaskExecutor(
            name="test_exec",
            func=lambda x: x,
            execution_mode="serial",
        )
        cloned = clone_executor(executor)

        cloned.set_execution_mode("thread")

        assert executor.execution_mode == "serial"
        assert cloned.execution_mode == "thread"

    # ── clone_stage ────────────────────────────────────────────────

    def test_clone_stage_same_attributes(self):
        """克隆后 name / func / execution_mode / stage_mode 应与原对象相同。"""
        stage = TaskStage(
            name="test_stage",
            func=lambda x: x,
            stage_mode="thread",
        )
        cloned = clone_stage(stage)

        assert cloned.get_name() == stage.get_name()
        assert cloned.func is stage.func
        assert cloned.execution_mode == stage.execution_mode
        assert cloned.stage_mode == stage.stage_mode

    def test_clone_stage_different_object(self):
        """克隆返回的是不同对象。"""
        stage = TaskStage(name="test_stage", func=lambda x: x)
        cloned = clone_stage(stage)

        assert cloned is not stage

    def test_clone_stage_independent(self):
        """修改克隆的 execution_mode 不影响原 stage。"""
        stage = TaskStage(
            name="test_stage",
            func=lambda x: x,
            execution_mode="serial",
        )
        cloned = clone_stage(stage)

        cloned.set_execution_mode("thread")

        assert stage.execution_mode == "serial"
        assert cloned.execution_mode == "thread"

    # ── clone_graph ────────────────────────────────────────────────

    def test_clone_graph_structure(self):
        """构造简单 DAG (A→B→C)，克隆后验证节点数、边连接、schedule_mode 一致。"""
        stage_a = TaskStage(name="A", func=lambda x: x)
        stage_b = TaskStage(name="B", func=lambda x: x)
        stage_c = TaskStage(name="C", func=lambda x: x)

        graph = TaskGraph("test_clone_graph_structure", schedule_mode="staged")
        graph.set_stages([stage_a, stage_b, stage_c])
        graph.connect([stage_a], [stage_b])
        graph.connect([stage_b], [stage_c])

        cloned = clone_graph(graph)

        # 源节点一致（同时触发 cloned 图的 _build_analysis）
        assert [s.get_name() for s in cloned.get_source_stages()] == \
               [s.get_name() for s in graph.get_source_stages()]

        # 通过有序图验证节点一致
        g1_graph = graph.get_order_graph()
        g2_graph = cloned.get_order_graph()
        assert set(g1_graph.nodes) == set(g2_graph.nodes)
        assert set(g1_graph.nodes) == {"A", "B", "C"}

        # 通过有序图验证边连接一致
        g1_edges = {(src, dst) for src, targets in g1_graph.out_edges.items() for dst in targets}
        g2_edges = {(src, dst) for src, targets in g2_graph.out_edges.items() for dst in targets}
        assert g1_edges == g2_edges
        assert g1_edges == {("A", "B"), ("B", "C")}

        # schedule_mode 保留
        assert cloned.schedule_mode == graph.schedule_mode

    def test_clone_graph_independent(self):
        """克隆图的节点修改不影响原图节点。"""
        stage_a = TaskStage(name="A", func=lambda x: x, execution_mode="serial")
        stage_b = TaskStage(name="B", func=lambda x: x, execution_mode="serial")

        graph = TaskGraph("test_clone_graph_independent", schedule_mode="eager")
        graph.set_stages([stage_a, stage_b])
        graph.connect([stage_a], [stage_b])

        cloned = clone_graph(graph)

        # 修改克隆图中节点 A 的 execution_mode
        cloned_stage_a = cloned.stage_dict["A"]
        cloned_stage_a.set_execution_mode("thread")

        # 原图节点不受影响
        assert stage_a.execution_mode == "serial"
        assert cloned_stage_a.execution_mode == "thread"

    def test_clone_graph_creates_independent_local_event_client(self):
        """默认本地事件客户端在克隆后应保持实例独立。"""
        graph = TaskGraph("test_clone_graph_event_client")
        cloned = clone_graph(graph)

        assert isinstance(graph.ctree_client, LocalEventClient)
        assert isinstance(cloned.ctree_client, LocalEventClient)
        assert cloned.ctree_client is not graph.ctree_client


# 运行方式：
#   python -m pytest tests/utils/test_utils_clone.py -v
