from pathlib import Path
from typing import Any

from celestialflow.observability import TaskReporter
from celestialflow.persistence.util_sqlite import append_records
from celestialflow.runtime.util_types import TERMINATION_SIGNAL


class FakeResponse:
    """模拟 reporter 拉取注入任务时的 HTTP 响应。"""

    def __init__(self, payload: dict[str, list[Any]]) -> None:
        self.ok = True
        self.status_code = 200
        self._payload = payload

    def json(self) -> dict[str, list[Any]]:
        """返回预设 JSON 载荷。"""
        return self._payload


class FakeSession:
    """模拟 requests.Session，只覆盖 reporter 需要的 get 接口。"""

    def __init__(self, payload: dict[str, list[Any]]) -> None:
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


class FakeTaskGraph:
    """记录 put_stage_queue 调用参数。"""

    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, list[Any]], bool]] = []

    def put_stage_queue(
        self, tasks_dict: dict[str, list[Any]], put_termination_signal: bool = True
    ) -> None:
        """保存 reporter 注入到图中的任务字典。"""
        self.calls.append((tasks_dict, put_termination_signal))


class FakeErrorGraph:
    """提供 reporter 推送错误所需的最小图接口。"""

    def __init__(self, fallback_path: Path, graph_id: str = "demo@1000") -> None:
        self._fallback_path = str(fallback_path)
        self._graph_id = graph_id

    def get_fallback_path(self) -> str:
        """返回 fallback sqlite 路径。"""
        return self._fallback_path

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


def test_reporter_accepts_node_to_tasklist_mapping() -> None:
    """Reporter 能消费 {node_name: [tasklist]} 映射并一次性注入整包任务。"""
    graph = FakeTaskGraph()
    log_inlet = FakeLogInlet()
    reporter = TaskReporter("127.0.0.1", 8000, graph, log_inlet)
    reporter._session = FakeSession(
        {
            "StageA": [1, 2, 3],
            "StageB": ["TERMINATION_SIGNAL"],
        }
    )

    reporter._pull_and_inject_tasks()

    assert graph.calls == [
        (
            {
                "StageA": [1, 2, 3],
                "StageB": [TERMINATION_SIGNAL],
            },
            False,
        )
    ]
    assert log_inlet.successes == [
        ("StageA", [1, 2, 3]),
        ("StageB", [TERMINATION_SIGNAL]),
    ]
    assert log_inlet.failures == []
    assert log_inlet.pull_failures == []


def test_reporter_pushes_errors_via_push_errors_endpoint_only(tmp_path) -> None:
    """Reporter 只通过 push_errors 推送错误内容。"""
    sqlite_path = tmp_path / "fallback.sqlite3"
    appended = append_records(
        sqlite_path,
        [
            {
                "event_id": 1,
                "stage": "s1",
                "error_type": "ValueError",
                "error_message": "bad value",
                "error_ts": 1.0,
                "task": {"value": 1},
            }
        ],
    )
    assert appended == 1

    graph = FakeErrorGraph(sqlite_path)
    log_inlet = FakeLogInlet()
    reporter = TaskReporter("127.0.0.1", 8000, graph, log_inlet)
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
            "error_ts": 1.0,
            "task": {"value": 1},
            "result": None,
        }
    ]


def test_reporter_pushes_only_errors_after_server_max_event_id(tmp_path) -> None:
    """Reporter 只推送 failed 中 event_id 大于服务端水位线的记录。"""
    sqlite_path = tmp_path / "fallback.sqlite3"
    appended = append_records(
        sqlite_path,
        [
            {
                "event_id": 1,
                "stage": "s1",
                "error_type": "ValueError",
                "error_message": "old",
                "error_ts": 1.0,
                "task": {"value": 1},
            },
            {
                "event_id": 5,
                "stage": "s1",
                "error_type": "RuntimeError",
                "error_message": "newer",
                "error_ts": 5.0,
                "task": {"value": 5},
            },
            {
                "event_id": 7,
                "stage": "s2",
                "error_type": "TypeError",
                "error_message": "latest",
                "error_ts": 7.0,
                "task": {"value": 7},
            },
        ],
    )
    assert appended == 3

    graph = FakeErrorGraph(sqlite_path)
    log_inlet = FakeLogInlet()
    reporter = TaskReporter("127.0.0.1", 8000, graph, log_inlet)
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
