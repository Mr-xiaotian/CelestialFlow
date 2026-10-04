"""``MetricsObserver`` 单元测试。"""

from celestialflow.observer import (
    NodeEndEvent,
    NodeStartEvent,
    TaskFailEvent,
    TaskInputEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
)
from celestialflow.reporter import MetricsObserver
from celestialflow.runtime.util_types import NodeStatus


def _external_input(node: str) -> TaskInputEvent:
    """构造外部注入任务输入事件。"""
    return TaskInputEvent(
        node=node, task=1, task_repr="(1)", input_id=1, source="external"
    )


def _upstream_input(node: str, from_node: str) -> TaskInputEvent:
    """构造上游投递任务输入事件。"""
    return TaskInputEvent(
        node=node,
        task=1,
        task_repr="(1)",
        input_id=2,
        source="upstream",
        from_node=from_node,
    )


class TestMetricsObserverStorage:
    def test_on_node_added_creates_zeroed_snapshot(self):
        """``on_node_added`` 应建立以 0 初始化的节点快照。"""
        observer = MetricsObserver()
        observer.on_node_added("a")

        metrics = observer.get_node_metrics("a")
        assert metrics is not None
        assert metrics.status == NodeStatus.NOT_STARTED
        assert metrics.start_time == 0.0
        assert metrics.input_total == 0
        assert metrics.upstream_counts == {}
        assert metrics.downstream_counts == {}

    def test_unknown_node_returns_none(self):
        """未登记节点的读取应返回 ``None``。"""
        assert MetricsObserver().get_node_metrics("ghost") is None

    def test_on_node_connected_presets_zero_slots(self):
        """``on_node_connected`` 应以 0 预置两侧边计数槽位。"""
        observer = MetricsObserver()
        observer.on_node_connected("a", "b")

        a = observer.get_node_metrics("a")
        b = observer.get_node_metrics("b")
        assert a is not None and b is not None
        assert a.downstream_counts == {"b": 0}
        assert b.upstream_counts == {"a": 0}


class TestMetricsObserverEvents:
    def test_external_input_counted(self):
        """外部输入只增加接收方计数。"""
        observer = MetricsObserver()
        observer.on_node_added("a")

        observer.on_task_input(_external_input("a"))

        metrics = observer.get_node_metrics("a")
        assert metrics is not None
        assert metrics.external_input == 1
        assert metrics.input_total == 1

    def test_upstream_input_updates_both_sides(self):
        """上游投递同时写接收方上游计数与来源方下游计数。"""
        observer = MetricsObserver()
        observer.on_task_input(_upstream_input("dst", "src"))

        dst = observer.get_node_metrics("dst")
        src = observer.get_node_metrics("src")
        assert dst is not None and src is not None
        assert dst.upstream_counts == {"src": 1}
        assert dst.upstream_input == 1
        assert src.downstream_counts == {"dst": 1}

    def test_success_fail_skip_counts(self):
        """成功/失败/跳过事件分别写入对应计数。"""
        observer = MetricsObserver()
        observer.on_node_added("a")

        observer.on_task_success(
            TaskSuccessEvent("a", 1, "(1)", 2, "(2)", 0.0, 1, 2)
        )
        observer.on_task_fail(TaskFailEvent("a", 1, "(1)", ValueError("x"), 1, 2))
        observer.on_task_skip(TaskSkipEvent("a", 1, "(1)", 1, 2))

        metrics = observer.get_node_metrics("a")
        assert metrics is not None
        assert metrics.succeeded == 1
        assert metrics.failed == 1
        assert metrics.skipped == 1
        assert metrics.processed == 3

    def test_node_status_transitions(self):
        """节点启停事件应维护运行状态。"""
        observer = MetricsObserver()
        observer.on_node_start(NodeStartEvent("a", "serial", 1))
        running = observer.get_node_metrics("a")
        assert running is not None
        assert running.status == NodeStatus.RUNNING
        assert running.start_time > 0.0

        observer.on_node_end(NodeEndEvent("a", "serial", 1, 0.0))
        stopped = observer.get_node_metrics("a")
        assert stopped is not None
        assert stopped.status == NodeStatus.STOPPED


class TestMetricsObserverGraphView:
    def test_cells_are_isolated_between_nodes(self):
        """不同节点的存储格互不影响。"""
        observer = MetricsObserver()
        observer.on_node_added("a")
        observer.on_node_added("b")

        observer.on_task_success(
            TaskSuccessEvent("a", 1, "(1)", 2, "(2)", 0.0, 1, 2)
        )

        a = observer.get_node_metrics("a")
        b = observer.get_node_metrics("b")
        assert a is not None and b is not None
        assert a.succeeded == 1
        assert b.succeeded == 0

    def test_graph_metrics_covers_all_registered_nodes(self):
        """``get_graph_metrics`` 应覆盖所有已登记节点。"""
        observer = MetricsObserver()
        observer.on_node_added("a")
        observer.on_node_added("b")

        snapshot = observer.get_graph_metrics()

        assert set(snapshot) == {"a", "b"}
