"""Tests for util_clone module."""

from celestialflow.graph import TaskGraph
from celestialflow import TaskExecutor, TaskRouter, TaskSplitter
from celestialflow.runtime.util_event import LocalEventClient
from celestialflow.benchmark.util_clone import clone_graph, clone_node


class TestUtilClone:
    """Tests for clone utilities: clone_node and clone_graph."""

    # ── clone_node ─────────────────────────────────────────────────

    def test_clone_node_executor_same_attributes(self):
        """克隆后 name / func / execution_mode 与原对象相同。"""
        executor = TaskExecutor(
            name="test_exec",
            func=lambda x: x,
            execution_mode="thread",
        )
        cloned = clone_node(executor)

        assert cloned.get_name() == executor.get_name()
        assert cloned.func is executor.func
        assert cloned.execution_mode == executor.execution_mode

    def test_clone_node_executor_different_object(self):
        """克隆返回的是不同对象。"""
        executor = TaskExecutor(name="test_exec", func=lambda x: x)
        cloned = clone_node(executor)

        assert cloned is not executor

    def test_clone_node_executor_independent(self):
        """修改克隆的 execution_mode 不影响原对象。"""
        executor = TaskExecutor(
            name="test_exec",
            func=lambda x: x,
            execution_mode="serial",
        )
        cloned = clone_node(executor)

        cloned.set_execution_mode("thread")

        assert executor.execution_mode == "serial"
        assert cloned.execution_mode == "thread"

    def test_clone_node_splitter_same_attributes(self):
        """TaskSplitter 克隆后应保留核心属性与重试配置。"""
        splitter = TaskSplitter(
            name="splitter",
            func=lambda task: [task, task + 1],
            execution_mode="thread",
        )
        splitter.set_retry_exceptions(ValueError)

        cloned = clone_node(splitter)

        assert isinstance(cloned, TaskSplitter)
        assert cloned.get_name() == splitter.get_name()
        assert cloned.func is splitter.func
        assert cloned.execution_mode == splitter.execution_mode
        assert cloned.retry_exceptions == splitter.retry_exceptions

    def test_clone_node_router_same_attributes(self):
        """TaskRouter 克隆后应保留核心属性与重试配置。"""
        router = TaskRouter(
            name="router",
            func=lambda task: {"done": task},
            execution_mode="thread",
        )
        router.set_retry_exceptions(RuntimeError)

        cloned = clone_node(router)

        assert isinstance(cloned, TaskRouter)
        assert cloned.get_name() == router.get_name()
        assert cloned.func is router.func
        assert cloned.execution_mode == router.execution_mode
        assert cloned.retry_exceptions == router.retry_exceptions

    # ── graph node cloning via clone_node ────────────────────────────

    def test_clone_graph_node_same_attributes(self):
        """作为图节点使用时，clone_node 仍应保留核心属性。"""
        node = TaskExecutor(name="test_node", func=lambda x: x)
        cloned = clone_node(node)

        assert cloned.get_name() == node.get_name()
        assert cloned.func is node.func
        assert cloned.execution_mode == node.execution_mode

    def test_clone_graph_node_different_object(self):
        """作为图节点使用时，克隆返回的仍应是独立对象。"""
        node = TaskExecutor(name="test_node", func=lambda x: x)
        cloned = clone_node(node)

        assert cloned is not node

    def test_clone_graph_node_independent(self):
        """作为图节点使用时，修改克隆对象不应影响原对象。"""
        node = TaskExecutor(
            name="test_node",
            func=lambda x: x,
            execution_mode="serial",
        )
        cloned = clone_node(node)

        cloned.set_execution_mode("thread")

        assert node.execution_mode == "serial"
        assert cloned.execution_mode == "thread"

    # ── clone_graph ────────────────────────────────────────────────

    def test_clone_graph_structure(self):
        """构造简单 DAG (A→B→C)，克隆后验证节点数、边连接一致。"""
        node_a = TaskExecutor(name="A", func=lambda x: x)
        node_b = TaskExecutor(name="B", func=lambda x: x)
        node_c = TaskExecutor(name="C", func=lambda x: x)

        graph = TaskGraph("test_clone_graph_structure")
        graph.set_nodes([node_a, node_b, node_c])
        graph.connect([node_a], [node_b])
        graph.connect([node_b], [node_c])

        cloned = clone_graph(graph)

        # 源节点一致（同时触发 cloned 图的 _build_analysis）
        assert cloned.get_source_nodes() == graph.get_source_nodes()

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

    def test_clone_graph_independent(self):
        """克隆图的节点修改不影响原图节点。"""
        node_a = TaskExecutor(name="A", func=lambda x: x, execution_mode="serial")
        node_b = TaskExecutor(name="B", func=lambda x: x, execution_mode="serial")

        graph = TaskGraph("test_clone_graph_independent")
        graph.set_nodes([node_a, node_b])
        graph.connect([node_a], [node_b])

        cloned = clone_graph(graph)

        # 修改克隆图中节点 A 的 execution_mode
        cloned_node_a = cloned.node_dict["A"]
        cloned_node_a.set_execution_mode("thread")

        # 原图节点不受影响
        assert node_a.execution_mode == "serial"
        assert cloned_node_a.execution_mode == "thread"

    def test_clone_graph_creates_independent_local_event_client(self):
        """默认本地事件客户端在克隆后应保持实例独立。"""
        graph = TaskGraph("test_clone_graph_event_client")
        cloned = clone_graph(graph)

        assert isinstance(graph.ctree_client, LocalEventClient)
        assert isinstance(cloned.ctree_client, LocalEventClient)
        assert cloned.ctree_client is not graph.ctree_client

    def test_clone_graph_keeps_disconnected_nodes(self):
        """非连通节点也应被完整克隆。"""
        node_a = TaskExecutor(name="A", func=lambda x: x)
        node_b = TaskExecutor(name="B", func=lambda x: x)
        node_c = TaskExecutor(name="C", func=lambda x: x)

        graph = TaskGraph("test_clone_graph_disconnected")
        graph.set_nodes([node_a, node_b, node_c])
        graph.connect([node_a], [node_b])

        cloned = clone_graph(graph)

        assert set(cloned.get_nodes()) == {"A", "B", "C"}
        assert cloned.get_edges() == {"A": ["B"], "B": [], "C": []}

    def test_clone_graph_keeps_cycle_without_source_nodes(self):
        """thread 模式下的无源环图也应能被克隆。"""
        node_a = TaskExecutor(name="A", func=lambda x: x)
        node_b = TaskExecutor(name="B", func=lambda x: x)

        graph = TaskGraph("test_clone_graph_cycle", graph_mode="thread")
        graph.set_nodes([node_a, node_b])
        graph.connect([node_a], [node_b])
        graph.connect([node_b], [node_a])

        cloned = clone_graph(graph)

        assert cloned.graph_mode == "thread"
        assert set(cloned.get_nodes()) == {"A", "B"}
        assert cloned.get_edges() == {"A": ["B"], "B": ["A"]}

    def test_clone_graph_keeps_builtin_node_types(self):
        """混合内置节点类型的图应保留节点类别与结构。"""
        splitter = TaskSplitter("splitter", lambda task: [task, task + 1])
        router = TaskRouter(
            "router",
            lambda task: {"even": task} if task % 2 == 0 else {"odd": task},
        )
        even = TaskExecutor("even", lambda task: task)
        odd = TaskExecutor("odd", lambda task: task)

        graph = TaskGraph("test_clone_graph_builtin_nodes")
        graph.set_nodes([splitter, router, even, odd])
        graph.connect([splitter], [router])
        graph.connect([router], [even, odd])

        cloned = clone_graph(graph)

        assert isinstance(cloned.node_dict["splitter"], TaskSplitter)
        assert isinstance(cloned.node_dict["router"], TaskRouter)
        assert isinstance(cloned.node_dict["even"], TaskExecutor)
        assert isinstance(cloned.node_dict["odd"], TaskExecutor)
        assert cloned.get_edges() == {
            "splitter": ["router"],
            "router": ["even", "odd"],
            "even": [],
            "odd": [],
        }


# 运行方式：
#   python -m pytest tests/utils/test_utils_clone.py -v
