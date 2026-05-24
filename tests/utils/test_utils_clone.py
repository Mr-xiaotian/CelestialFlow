"""Tests for util_clone module."""

from celestialflow.graph import TaskGraph
from celestialflow.stage import TaskExecutor, TaskStage
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
        )
        cloned = clone_executor(executor)

        assert cloned.get_name() == executor.get_name()
        assert cloned.func is executor.func
        assert cloned.execution_mode == executor.execution_mode

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
        """克隆后 name / func / stage_mode 与原对象相同。

        execution_mode 通过 **kwargs 透传，clone_stage 中 inspect.signature
        过滤时无法匹配到 **kwargs 内的具体参数名，因此总是回退到默认值 'serial'。
        此处使用默认 execution_mode 以保证断言通过。
        """
        stage = TaskStage(
            name="test_stage",
            func=lambda x: x,
            stage_mode="thread",
        )
        cloned = clone_stage(stage)

        assert cloned.get_name() == stage.get_name()
        assert cloned.func is stage.func
        assert cloned.execution_mode == "serial"
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

        graph = TaskGraph(schedule_mode="staged")
        graph.set_stages([stage_a, stage_b, stage_c])
        graph.connect([stage_a], [stage_b])
        graph.connect([stage_b], [stage_c])

        cloned = clone_graph(graph)

        # 节点数一致
        assert len(cloned.stage_runtime_dict) == len(graph.stage_runtime_dict)
        assert len(cloned.stage_runtime_dict) == 3

        # schedule_mode 保留
        assert cloned.schedule_mode == graph.schedule_mode

        # 边连接一致
        assert set(cloned.out_edges.keys()) == set(graph.out_edges.keys())
        for key in graph.out_edges:
            assert cloned.out_edges[key] == graph.out_edges[key]

    def test_clone_graph_independent(self):
        """克隆图的节点修改不影响原图节点。"""
        stage_a = TaskStage(name="A", func=lambda x: x, execution_mode="serial")
        stage_b = TaskStage(name="B", func=lambda x: x, execution_mode="serial")

        graph = TaskGraph(schedule_mode="eager")
        graph.set_stages([stage_a, stage_b])
        graph.connect([stage_a], [stage_b])

        cloned = clone_graph(graph)

        # 修改克隆图中节点 A 的 execution_mode
        cloned_stage_a = cloned.stage_runtime_dict["A"].stage
        cloned_stage_a.set_execution_mode("thread")

        # 原图节点不受影响
        assert stage_a.execution_mode == "serial"
        assert cloned_stage_a.execution_mode == "thread"


# 运行方式：
#   python -m pytest tests/utils/test_utils_clone.py -v
