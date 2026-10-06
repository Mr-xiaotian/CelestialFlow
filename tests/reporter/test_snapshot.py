from __future__ import annotations

from typing import Any

from celestialflow.reporter import PushSnapshotHandler, PushSpout
from celestialflow.reporter.core_push import PushInlet, PushRecord
from celestialflow.reporter.core_snapshot import to_status_snapshot
from celestialflow.runtime.util_types import NodeMetrics, NodeStatus
from celestialflow.ticker import TickEvent


class FakeMetricsView:
    """提供固定整图指标的 ``MetricsView`` 替身。"""

    def __init__(self, metrics: dict[str, NodeMetrics]) -> None:
        self._metrics = metrics
        self.graph_calls = 0

    def get_node_metrics(self, node: str) -> NodeMetrics | None:
        """返回指定节点的指标快照。"""
        return self._metrics.get(node)

    def get_graph_metrics(self) -> dict[str, NodeMetrics]:
        """返回整图指标快照并记录调用次数。"""
        self.graph_calls += 1
        return dict(self._metrics)


class FakePushSession:
    """记录推送 POST 请求的 ``requests.Session`` 替身。"""

    def __init__(self) -> None:
        self.posts: list[tuple[str, dict[str, Any], float]] = []

    def post(self, url: str, json: dict[str, Any], timeout: float) -> Any:
        """记录推送目标与载荷并返回成功响应。"""
        self.posts.append((url, json, timeout))

        class _Response:
            ok = True
            status_code = 200

        return _Response()


def make_metrics(node: str, *, succeeded: int = 0) -> NodeMetrics:
    """
    构造一个运行中的节点指标快照。

    :param node: 节点名称
    :param succeeded: 成功任务数
    :return: 节点指标快照
    """
    return NodeMetrics(
        node=node,
        status=NodeStatus.RUNNING,
        start_time=1.0,
        external_input=succeeded,
        upstream_input=0,
        input_total=succeeded,
        succeeded=succeeded,
        failed=0,
        skipped=0,
        processed=succeeded,
        pending=0,
        upstream_counts={},
        downstream_counts={},
    )


def make_event(seq: int = 1) -> TickEvent:
    """
    构造一个测试用节拍事件。

    :param seq: 节拍序号
    :return: 节拍事件
    """
    return TickEvent(
        seq=seq,
        interval=1.0,
        scheduled_at=0.0,
        fired_at=0.0,
        wall_time=0.0,
        drift=0.0,
        skipped=0,
    )


def test_to_status_snapshot_projects_node_metrics() -> None:
    """投影函数应输出推送所需的全部状态字段。"""
    snapshot = to_status_snapshot({"s1": make_metrics("s1", succeeded=3)})

    assert set(snapshot) == {"s1"}
    node = snapshot["s1"]
    assert node["status"] == NodeStatus.RUNNING
    assert node["tasks_input"] == 3
    assert node["tasks_succeeded"] == 3
    assert node["upstream_counts"] == {}
    assert node["downstream_counts"] == {}


def test_handler_enqueues_snapshot_record() -> None:
    """处理器被唤醒时应把当前快照入队为 ``kind="snapshot"`` 记录。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    inlet = PushInlet().bind_spout(spout)
    view = FakeMetricsView({"s1": make_metrics("s1", succeeded=2)})
    handler = PushSnapshotHandler(view, inlet)

    handler.on_tick(make_event())

    record = spout.get_queue().get()
    assert isinstance(record, PushRecord)
    assert record.kind == "snapshot"
    assert record.snapshot["s1"]["tasks_succeeded"] == 2
    assert view.graph_calls == 1


def test_spout_pushes_snapshot_to_push_status_endpoint() -> None:
    """快照记录会被推送到 ``/api/push_status``，载荷携带会话与状态。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    session = FakePushSession()
    spout._session = session
    inlet = PushInlet().bind_spout(spout)

    inlet.push_snapshot({"s1": {"status": 1}})
    spout._handle_record(spout.get_queue().get())

    assert len(session.posts) == 1
    url, payload, _timeout = session.posts[0]
    assert url == "http://host:1/api/push_status"
    assert payload["graph_id"] == "g1"
    assert payload["status"] == {"s1": {"status": 1}}
    assert payload["timestamp"] > 0
