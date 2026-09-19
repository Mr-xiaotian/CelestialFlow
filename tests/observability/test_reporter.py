from pathlib import Path
from typing import Any

import pytest

from celestialflow import TaskExecutor, TaskGraph
from celestialflow.observability import TaskReporter
from celestialflow.persistence.util_sqlite import append_records
from celestialflow.runtime.util_types import TERMINATION_SIGNAL


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

    def get(self, *_args: Any, **_kwargs: Any) -> FakeResponse:
        """返回固定注入任务响应。"""
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


class FakeNode:
    """记录显式任务注入调用。"""

    def __init__(self) -> None:
        self.task_calls: list[Any] = []
        self.signal_calls = 0

    def put_task(self, task: Any) -> None:
        """记录单次任务注入。"""
        self.task_calls.append(task)

    def put_signal(self) -> None:
        """记录终止信号注入。"""
        self.signal_calls += 1


class FakeTaskGraph:
    """提供 reporter 拉取注入所需的最小图接口。"""

    def __init__(self) -> None:
        self.node_dict: dict[str, FakeNode] = {
            "StageA": FakeNode(),
            "StageB": FakeNode(),
        }


class FakeErrorGraph:
    """提供 reporter 推送错误所需的最小图接口。"""

    def __init__(self, lifecycle_path: Path, graph_id: str = "demo@1000") -> None:
        self._lifecycle_path = str(lifecycle_path)
        self._graph_id = graph_id

    def get_lifecycle_path(self) -> str:
        """返回 lifecycle sqlite 路径。"""
        return self._lifecycle_path

    def get_graph_id(self) -> str:
        """返回当前 graph_id。"""
        return self._graph_id


class FakeLogInlet:
    """记录 reporter 注入成功/失败日志。"""

    def __init__(self) -> None:
        self.successes: list[tuple[str, list[Any]]] = []
        self.failures: list[tuple[str, list[Any], Exception]] = []
        self.pull_failures: list[Exception] = []
        self.push_error_failures: list[Exception] = []

    def inject_tasks_success(self, target_node: str, task_datas: list[Any]) -> None:
        """记录节点注入成功。"""
        self.successes.append((target_node, task_datas))

    def inject_tasks_failed(
        self, target_node: str, task_datas: list[Any], error: Exception
    ) -> None:
        """记录节点注入失败。"""
        self.failures.append((target_node, task_datas, error))

    def pull_tasks_failed(self, error: Exception) -> None:
        """记录拉取失败。"""
        self.pull_failures.append(error)

    def push_errors_failed(self, error: Exception) -> None:
        """记录错误推送失败。"""
        self.push_error_failures.append(error)


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

    assert graph.node_dict["StageA"].task_calls == [1, 2, 3]
    assert graph.node_dict["StageA"].signal_calls == 0
    assert graph.node_dict["StageB"].task_calls == []
    assert graph.node_dict["StageB"].signal_calls == 1
    assert log_inlet.successes == [
        ("StageA", [1, 2, 3]),
        ("StageB", [TERMINATION_SIGNAL]),
    ]
    assert log_inlet.failures == []
    assert log_inlet.pull_failures == []


def test_reporter_merges_tasks_and_termination_for_same_stage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """同一节点同时存在任务与终止符时，应保留任务并在末尾追加终止符。"""
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

    assert graph.node_dict["StageA"].task_calls == [1, 2, 3]
    assert graph.node_dict["StageA"].signal_calls == 1
    assert log_inlet.successes == [
        ("StageA", [1, 2, 3]),
        ("StageA", [TERMINATION_SIGNAL]),
    ]
    assert log_inlet.failures == []
    assert log_inlet.pull_failures == []


def test_reporter_pushes_errors_via_push_errors_endpoint_only(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reporter 只通过 push_errors 推送错误内容。"""
    sqlite_path = tmp_path / "lifecycle.sqlite3"
    appended = append_records(
        sqlite_path,
        [
            {
                "event_id": 1,
                "stage": "s1",
                "status": "failed",
                "error_type": "ValueError",
                "error_message": "bad value",
                "ts": 1.0,
                "task_json": {"value": 1},
            }
        ],
    )
    assert appended == 1

    graph = FakeErrorGraph(sqlite_path)
    log_inlet = FakeLogInlet()
    monkeypatch.setattr(
        "celestialflow.observability.core_report.get_log_inlet",
        lambda: log_inlet,
    )
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakePushSession()
    reporter._server_has_current_graph = False

    reporter._push_errors()

    assert log_inlet.push_error_failures == []
    assert len(reporter._session.posts) == 1
    url, payload, _timeout = reporter._session.posts[0]
    assert url.endswith("/api/push_errors")
    assert payload["graph_id"] == "demo@1000"
    assert payload["errors"] == [
        {
            "id": 1,
            "event_id": 1,
            "stage": "s1",
            "status": "failed",
            "error_type": "ValueError",
            "error_message": "bad value",
            "ts": 1.0,
            "task_json": {"value": 1},
            "result_json": None,
            "retry_times": 0,
        }
    ]


def test_reporter_pushes_only_errors_after_server_max_event_id(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reporter 只推送 failed 中 event_id 大于服务端水位线的记录。"""
    sqlite_path = tmp_path / "lifecycle.sqlite3"
    appended = append_records(
        sqlite_path,
        [
            {
                "event_id": 1,
                "stage": "s1",
                "status": "failed",
                "error_type": "ValueError",
                "error_message": "old",
                "ts": 1.0,
                "task_json": {"value": 1},
            },
            {
                "event_id": 5,
                "stage": "s1",
                "status": "failed",
                "error_type": "RuntimeError",
                "error_message": "newer",
                "ts": 5.0,
                "task_json": {"value": 5},
            },
            {
                "event_id": 7,
                "stage": "s2",
                "status": "failed",
                "error_type": "TypeError",
                "error_message": "latest",
                "ts": 7.0,
                "task_json": {"value": 7},
            },
        ],
    )
    assert appended == 3

    graph = FakeErrorGraph(sqlite_path)
    log_inlet = FakeLogInlet()
    monkeypatch.setattr(
        "celestialflow.observability.core_report.get_log_inlet",
        lambda: log_inlet,
    )
    reporter = TaskReporter("127.0.0.1", 8000, graph)
    reporter._session = FakePushSession()
    reporter._server_has_current_graph = True
    reporter._server_max_event_id_in_fail = 3

    reporter._push_errors()

    assert log_inlet.push_error_failures == []
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
