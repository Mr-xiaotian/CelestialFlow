from collections.abc import Mapping, Sequence
from typing import Any

from celestialflow.observer import (
    Observer,
    ObserverHub,
    ReporterFailureEvent,
)
from celestialflow.reporter import TaskReporter


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
        self.observers = ObserverHub()

    def get_graph_id(self) -> str:
        """返回固定 graph_id，便于断言拉取与注入携带的会话标识。"""
        return "pull@1000"

    def get_observers(self) -> ObserverHub:
        """返回图级观察者 hub。"""
        return self.observers

    def inject_tasks(self, tasks: Mapping[str, Sequence[Any]]) -> None:
        """记录按节点名转交的注入任务。"""
        self.injected_tasks.append({name: list(items) for name, items in tasks.items()})

    def inject_terminations(self, nodes: Sequence[str]) -> None:
        """记录转交的终止符注入节点。"""
        self.injected_terminations.append(list(nodes))


class RecordingReporterObserver(Observer):
    """记录 reporter 上报过程中的失败事件。"""

    def __init__(self) -> None:
        self.failures: list[tuple[str, Exception]] = []

    def on_reporter_failure(self, event: ReporterFailureEvent) -> None:
        """记录失败类别与异常。"""
        self.failures.append((event.kind, event.exception))


class FakeStatusGraph:
    """提供 reporter 推送状态所需的最小图接口。"""

    def __init__(self, snapshot: dict[str, Any] | None = None) -> None:
        self.snapshots: dict[str, dict[str, Any]] = {
            "StageA": dict(snapshot or {"status": 0, "tasks_processed": 0})
        }
        self._graph_id = "demo@status"
        self.observers = ObserverHub()

    def get_graph_id(self) -> str:
        """返回当前 graph_id。"""
        return self._graph_id

    def get_observers(self) -> ObserverHub:
        """返回图级观察者 hub。"""
        return self.observers

    def get_status_snapshot(self) -> dict[str, dict[str, Any]]:
        """返回各节点快照的浅拷贝。"""
        return {name: dict(snap) for name, snap in self.snapshots.items()}


def test_reporter_accepts_split_task_and_termination_payload() -> None:
    """Reporter 能消费拆分后的任务与终止符注入载荷。"""
    graph = FakeTaskGraph()
    recorder = RecordingReporterObserver()
    graph.observers.add_observer(recorder)
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
    assert recorder.failures == []
    # 拉取注入时必须携带当前会话标识，避免注入到其它会话。
    url, params = reporter._session.gets[0]
    assert url.endswith("/api/pull_injection")
    assert params["graph_id"] == "pull@1000"


def test_reporter_forwards_tasks_and_termination_for_same_node() -> None:
    """同一节点同时存在任务与终止符时，两者都应被转交（先任务后终止符）。"""
    graph = FakeTaskGraph()
    recorder = RecordingReporterObserver()
    graph.observers.add_observer(recorder)
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
    assert recorder.failures == []


def test_reporter_reports_injection_failure_as_inject_kind() -> None:
    """任务注入抛出的异常会上报为 kind='inject'，且不影响终止符注入。"""

    class RaisingTaskGraph(FakeTaskGraph):
        """模拟 inject_tasks 抛错的图。"""

        def inject_tasks(self, tasks: Mapping[str, Sequence[Any]]) -> None:
            """模拟注入失败。"""
            raise RuntimeError("unknown node")

    graph = RaisingTaskGraph()
    recorder = RecordingReporterObserver()
    graph.observers.add_observer(recorder)
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakeSession(
        {"tasks": {"StageA": [1, 2]}, "terminations": ["StageB"]}
    )

    reporter._pull_injection()

    assert [kind for kind, _exc in recorder.failures] == ["inject"]
    # 终止符注入与任务注入相互独立，任务注入失败不应阻止终止符注入。
    assert graph.injected_terminations == [["StageB"]]


def test_reporter_pushes_status_only_when_snapshot_changes() -> None:
    """状态快照未变时不应重复推送，变化后才推送新快照。"""
    graph = FakeStatusGraph()
    recorder = RecordingReporterObserver()
    graph.observers.add_observer(recorder)
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakePushSession()
    reporter._server_has_status = True

    reporter._push_status()
    reporter._push_status()

    assert recorder.failures == []
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


def test_reporter_forces_status_push_on_context_switch() -> None:
    """服务端会话尚无状态缓存时，即使快照未变也必须强制推送一次。"""
    graph = FakeStatusGraph()
    recorder = RecordingReporterObserver()
    graph.observers.add_observer(recorder)
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakePushSession()
    reporter._server_has_status = True

    reporter._push_status()
    assert len(reporter._session.posts) == 1

    # 服务端会话被移除后重建，has_status 返回 False。
    reporter._server_has_status = False
    reporter._push_status()

    assert recorder.failures == []
    assert len(reporter._session.posts) == 2


def test_reporter_notifies_shutdown() -> None:
    """Reporter 停止前会向服务端发送会话结束通知。"""
    graph = FakeStatusGraph()
    recorder = RecordingReporterObserver()
    graph.observers.add_observer(recorder)
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakePushSession()

    reporter._notify_shutdown()

    assert recorder.failures == []
    assert len(reporter._session.posts) == 1
    url, payload, _timeout = reporter._session.posts[0]
    assert url.endswith("/api/shutdown_session")
    assert payload == {"graph_id": "demo@status"}
