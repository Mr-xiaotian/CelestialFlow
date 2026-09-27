from collections.abc import Mapping, Sequence
from typing import Any

import pytest

from celestialflow import TaskExecutor, TaskGraph
from celestialflow.observability import TaskReporter


class FakeResponse:
    """模拟 reporter 拉取注入任务时的 HTTP 响应。"""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.ok = True
        self.status_code = 200
        self._payload = payload

    def json(self) -> dict[str, Any]:
        """返回预设 JSON 载荷。"""
        return self._payload


class FakeSession:
    """模拟 requests.Session，只覆盖 reporter 需要的 get 接口。"""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.gets: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, params: dict[str, Any] | None = None, **_kwargs: Any) -> FakeResponse:
        """返回固定注入任务响应，并记录请求参数。"""
        self.gets.append((url, params or {}))
        return FakeResponse(self.payload)


class FakePostResponse:
    """模拟 reporter 推送时的 HTTP 响应。"""

    def __init__(self) -> None:
        self.ok = True
        self.status_code = 200

    def json(self) -> dict[str, bool]:
        """返回成功响应。"""
        return {"ok": True}


class FakePushSession:
    """记录 reporter 的 POST 请求。"""

    def __init__(self) -> None:
        self.posts: list[tuple[str, dict[str, Any], float]] = []

    def post(self, url: str, json: dict[str, Any], timeout: float) -> FakePostResponse:
        """记录推送目标与 payload。"""
        self.posts.append((url, json, timeout))
        return FakePostResponse()


class FakeTaskGraph:
    """记录 reporter 转交的任务与终止符注入调用。"""

    def __init__(self) -> None:
        self.injected_tasks: list[dict[str, list[Any]]] = []
        self.injected_terminations: list[list[str]] = []

    def get_graph_id(self) -> str:
        """返回固定 graph_id，便于断言拉取与注入携带的会话标识。"""
        return "pull@1000"

    def inject_tasks(self, tasks: Mapping[str, Sequence[Any]]) -> None:
        """记录按节点名转交的注入任务。"""
        self.injected_tasks.append({name: list(items) for name, items in tasks.items()})

    def inject_terminations(self, nodes: Sequence[str]) -> None:
        """记录转交的终止符注入节点。"""
        self.injected_terminations.append(list(nodes))


class FakeErrorGraph:
    """提供 reporter 推送错误所需的最小图接口。"""

    def __init__(
        self, records: list[dict[str, Any]] | None = None, graph_id: str = "demo@1000"
    ) -> None:
        self._records = list(records or [])
        self._graph_id = graph_id
        self.after_event_ids: list[int | None] = []

    def get_graph_id(self) -> str:
        """返回当前 graph_id。"""
        return self._graph_id

    def load_failed_records(self, after_event_id: int | None) -> list[dict[str, Any]]:
        """按水位线返回预设的失败记录，并记录调用参数。"""
        self.after_event_ids.append(after_event_id)
        if after_event_id is None:
            return list(self._records)
        return [r for r in self._records if int(r["event_id"]) > after_event_id]


class FakeLogInlet:
    """记录 reporter 上报过程中的失败日志。"""

    def __init__(self) -> None:
        self.pull_failures: list[Exception] = []
        self.push_error_failures: list[Exception] = []
        self.push_status_failures: list[Exception] = []
        self.shutdown_failures: list[Exception] = []

    def pull_tasks_failed(self, error: Exception) -> None:
        """记录拉取失败。"""
        self.pull_failures.append(error)

    def push_errors_failed(self, error: Exception) -> None:
        """记录错误推送失败。"""
        self.push_error_failures.append(error)

    def push_status_failed(self, error: Exception) -> None:
        """记录状态推送失败。"""
        self.push_status_failures.append(error)

    def shutdown_failed(self, error: Exception) -> None:
        """记录会话结束通知失败。"""
        self.shutdown_failures.append(error)


class FakeStatusGraph:
    """提供 reporter 推送状态所需的最小图接口。"""

    def __init__(self, snapshot: dict[str, Any] | None = None) -> None:
        self.snapshots: dict[str, dict[str, Any]] = {
            "StageA": dict(snapshot or {"status": 0, "tasks_processed": 0})
        }
        self._graph_id = "demo@status"

    def get_graph_id(self) -> str:
        """返回当前 graph_id。"""
        return self._graph_id

    def get_status_snapshot(self) -> dict[str, dict[str, Any]]:
        """返回各节点快照的浅拷贝。"""
        return {name: dict(snap) for name, snap in self.snapshots.items()}


def test_reporter_accepts_split_task_and_termination_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reporter 能消费拆分后的任务与终止符注入载荷。"""
    graph = FakeTaskGraph()
    log_inlet = FakeLogInlet()
    monkeypatch.setattr(
        "celestialflow.observability.core_report.get_log_inlet",
        lambda: log_inlet,
    )
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakeSession(
        {
            "tasks": {"StageA": [1, 2, 3]},
            "terminations": ["StageB"],
        }
    )

    reporter._pull_injection()

    assert graph.injected_tasks == [{"StageA": [1, 2, 3]}]
    assert graph.injected_terminations == [["StageB"]]
    assert log_inlet.pull_failures == []
    # 拉取注入时必须携带当前会话标识，避免注入到其它会话。
    url, params = reporter._session.gets[0]
    assert url.endswith("/api/pull_injection")
    assert params["graph_id"] == "pull@1000"


def test_reporter_forwards_tasks_and_termination_for_same_stage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """同一节点同时存在任务与终止符时，两者都应被转交（先任务后终止符）。"""
    graph = FakeTaskGraph()
    log_inlet = FakeLogInlet()
    monkeypatch.setattr(
        "celestialflow.observability.core_report.get_log_inlet",
        lambda: log_inlet,
    )
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakeSession(
        {
            "tasks": {"StageA": [1, 2, 3]},
            "terminations": ["StageA"],
        }
    )

    reporter._pull_injection()

    assert graph.injected_tasks == [{"StageA": [1, 2, 3]}]
    assert graph.injected_terminations == [["StageA"]]
    assert log_inlet.pull_failures == []


def test_reporter_pushes_errors_via_push_errors_endpoint_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reporter 只通过 push_errors 推送错误内容。"""
    record = {
        "event_id": 1,
        "stage": "s1",
        "status": "failed",
        "error_type": "ValueError",
        "error_message": "bad value",
        "ts": 1.0,
        "task_json": {"value": 1},
    }
    graph = FakeErrorGraph([record])
    log_inlet = FakeLogInlet()
    monkeypatch.setattr(
        "celestialflow.observability.core_report.get_log_inlet",
        lambda: log_inlet,
    )
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakePushSession()

    reporter._push_errors()

    assert log_inlet.push_error_failures == []
    # 服务端尚无水位线时应全量读取。
    assert graph.after_event_ids == [None]
    assert len(reporter._session.posts) == 1
    url, payload, _timeout = reporter._session.posts[0]
    assert url.endswith("/api/push_errors")
    assert payload["graph_id"] == "demo@1000"
    assert payload["errors"] == [record]


def test_reporter_pushes_only_errors_after_server_max_event_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reporter 只推送 failed 中 event_id 大于服务端水位线的记录。"""
    graph = FakeErrorGraph(
        [
            {"event_id": 1, "stage": "s1", "status": "failed", "task_json": {}},
            {"event_id": 5, "stage": "s1", "status": "failed", "task_json": {}},
            {"event_id": 7, "stage": "s2", "status": "failed", "task_json": {}},
        ]
    )
    log_inlet = FakeLogInlet()
    monkeypatch.setattr(
        "celestialflow.observability.core_report.get_log_inlet",
        lambda: log_inlet,
    )
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakePushSession()
    reporter._server_max_event_id_in_fail = 3

    reporter._push_errors()

    assert log_inlet.push_error_failures == []
    assert graph.after_event_ids == [3]
    assert len(reporter._session.posts) == 1
    url, payload, _timeout = reporter._session.posts[0]
    assert url.endswith("/api/push_errors")
    assert payload["graph_id"] == "demo@1000"
    assert [item["event_id"] for item in payload["errors"]] == [5, 7]


def test_reporter_pushes_graph_meta_in_one_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """图结构、节点元信息与分析结果随单次 push_graph_meta 推送，状态推送与它们互不相交。"""

    def identity(value: int) -> int:
        """测试用恒等函数。"""
        return value

    source = TaskExecutor("StageA", identity, execution_mode="thread", max_workers=3)
    sink = TaskExecutor("StageB", identity)

    graph = TaskGraph("push_graph_meta")
    graph.set_nodes(nodes=[source, sink])
    graph.connect([source], [sink])

    log_inlet = FakeLogInlet()
    monkeypatch.setattr(
        "celestialflow.observability.core_report.get_log_inlet",
        lambda: log_inlet,
    )
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakePushSession()

    reporter._push_graph_meta()
    reporter._push_status()

    assert len(reporter._session.posts) == 2
    meta_url, meta_payload, _timeout = reporter._session.posts[0]
    status_url, status_payload, _timeout = reporter._session.posts[1]
    assert meta_url.endswith("/api/push_graph_meta")
    assert status_url.endswith("/api/push_status")

    # 图级与节点级元信息在同一次请求中一并到达，不存在半初始化窗口。
    assert meta_payload["nodes"] == ["StageA", "StageB"]
    assert meta_payload["analysis"]["graphId"] == graph.get_graph_id()
    assert meta_payload["analysis"]["layersDict"]

    meta = meta_payload["node_meta"]
    assert set(meta) == {"StageA", "StageB"}
    assert meta["StageA"] == {
        "class_name": "TaskExecutor",
        "execution_mode": "thread",
        "max_workers": 3,
    }
    assert meta["StageB"]["class_name"] == "TaskExecutor"
    assert meta["StageB"]["execution_mode"] == "serial"

    # 两份 payload 必须职责互斥：状态里不得重复任何构建期字段。
    for node_name, node_status in status_payload["status"].items():
        assert set(node_status).isdisjoint(meta[node_name])


def test_reporter_pushes_status_only_when_snapshot_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """状态快照未变时不应重复推送，变化后才推送新快照。"""
    graph = FakeStatusGraph()
    log_inlet = FakeLogInlet()
    monkeypatch.setattr(
        "celestialflow.observability.core_report.get_log_inlet",
        lambda: log_inlet,
    )
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakePushSession()
    reporter._server_has_status = True

    reporter._push_status()
    reporter._push_status()

    assert log_inlet.push_status_failures == []
    assert len(reporter._session.posts) == 1

    graph.snapshots["StageA"] = {"status": 1, "tasks_processed": 3}
    reporter._push_status()

    assert len(reporter._session.posts) == 2
    url, payload, _timeout = reporter._session.posts[1]
    assert url.endswith("/api/push_status")
    assert payload["status"]["StageA"] == {"status": 1, "tasks_processed": 3}

    # 变化推送后再次采集相同快照，应重新回到静默。
    reporter._push_status()
    assert len(reporter._session.posts) == 2


def test_reporter_forces_status_push_on_context_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """服务端会话尚无状态缓存时，即使快照未变也必须强制推送一次。"""
    graph = FakeStatusGraph()
    log_inlet = FakeLogInlet()
    monkeypatch.setattr(
        "celestialflow.observability.core_report.get_log_inlet",
        lambda: log_inlet,
    )
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakePushSession()
    reporter._server_has_status = True

    reporter._push_status()
    assert len(reporter._session.posts) == 1

    # 服务端会话被移除后重建，has_status 返回 False。
    reporter._server_has_status = False
    reporter._push_status()

    assert log_inlet.push_status_failures == []
    assert len(reporter._session.posts) == 2


def test_reporter_notifies_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reporter 停止前会向服务端发送会话结束通知。"""
    graph = FakeStatusGraph()
    log_inlet = FakeLogInlet()
    monkeypatch.setattr(
        "celestialflow.observability.core_report.get_log_inlet",
        lambda: log_inlet,
    )
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakePushSession()

    reporter._notify_shutdown()

    assert log_inlet.shutdown_failures == []
    assert len(reporter._session.posts) == 1
    url, payload, _timeout = reporter._session.posts[0]
    assert url.endswith("/api/shutdown_session")
    assert payload == {"graph_id": "demo@status"}
