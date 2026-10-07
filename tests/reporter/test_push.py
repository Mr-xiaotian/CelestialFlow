from typing import Any

import pytest

import celestialflow.reporter.core_push as push_module
from celestialflow.observer import GraphEndEvent, GraphStartEvent, TaskFailEvent
from celestialflow.reporter.core_push import (
    NullPushSpout,
    PushInlet,
    PushRecord,
    PushSpout,
)
from celestialflow.runtime.util_errors import ReporterError
from conftest import wait_until


class FakePostResponse:
    """模拟推送时的 HTTP 响应。"""

    def __init__(self, ok: bool = True, status_code: int = 200) -> None:
        self.ok = ok
        self.status_code = status_code


class FakePushSession:
    """记录推送的 POST 请求，并模拟会话关闭。"""

    def __init__(self, ok: bool = True) -> None:
        self.ok = ok
        self.posts: list[tuple[str, dict[str, Any], float]] = []
        self.closed = False

    def post(self, url: str, json: dict[str, Any], timeout: float) -> FakePostResponse:
        """记录推送目标与 payload。"""
        self.posts.append((url, json, timeout))
        return FakePostResponse(self.ok, 200 if self.ok else 500)

    def close(self) -> None:
        """标记会话已关闭。"""
        self.closed = True


def _fail_event(
    *,
    error_id: int = 21,
    node: str = "s1",
    task: Any = "data1",
    exc: Exception | None = None,
) -> TaskFailEvent:
    """构造一个任务失败事件。"""
    exception = ValueError("oops") if exc is None else exc
    return TaskFailEvent(node, task, f"({task})", exception, 1, error_id)


def _start_event() -> GraphStartEvent:
    """构造一个携带图元信息的任务图启动事件。"""
    return GraphStartEvent(
        graph="g1",
        graph_mode="thread",
        start_time=123.0,
        class_name="TaskGraph",
        is_dag=True,
        nodes=["s1", "s2"],
        edges={"s1": ["s2"], "s2": []},
        source_nodes=["s1"],
        node_meta={
            "s1": {
                "class_name": "TaskExecutor",
                "execution_mode": "thread",
                "max_workers": 2,
            },
            "s2": {
                "class_name": "TaskExecutor",
                "execution_mode": "serial",
                "max_workers": 4,
            },
        },
    )


def _end_event() -> GraphEndEvent:
    """构造一个任务图结束事件。"""
    return GraphEndEvent(graph="g1", elapsed=1.5)


def _dequeue(spout: PushSpout) -> PushRecord:
    """取出 spout 队列中的单条记录。"""
    record = spout.get_queue().get()
    assert isinstance(record, PushRecord)
    return record


def test_inlet_maps_task_fail_event() -> None:
    """失败事件会被映射为 ``kind="task_fail"`` 的推送记录。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    inlet = PushInlet().bind_spout(spout)

    inlet.on_task_fail(_fail_event(error_id=7, node="s2", task={"value": 1},
                                   exc=TypeError("bad")))

    record = _dequeue(spout)
    assert record.kind == "task_fail"
    assert record.event_id == 7
    assert record.node == "s2"
    assert record.task_json == {"value": 1}
    assert record.error_type == "TypeError"
    assert record.error_message == "bad"
    assert record.ts > 0


def test_inlet_maps_graph_start_event() -> None:
    """图启动事件会被映射为 ``kind="graph_start"`` 的推送记录。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    inlet = PushInlet().bind_spout(spout)

    inlet.on_graph_start(_start_event())

    record = _dequeue(spout)
    assert record.kind == "graph_start"
    assert record.graph == "g1"
    assert record.graph_mode == "thread"
    assert record.start_time == 123.0
    assert record.class_name == "TaskGraph"
    assert record.is_dag is True
    assert record.nodes == ["s1", "s2"]
    assert record.edges == {"s1": ["s2"], "s2": []}
    assert record.source_nodes == ["s1"]
    assert record.node_meta["s1"]["max_workers"] == 2


def test_inlet_maps_graph_end_event() -> None:
    """图结束事件会被映射为 ``kind="graph_end"`` 的推送记录。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    inlet = PushInlet().bind_spout(spout)

    inlet.on_graph_end(_end_event())

    record = _dequeue(spout)
    assert record.kind == "graph_end"


def test_spout_pushes_task_fail_to_push_error_endpoint() -> None:
    """失败记录会以 push_error 推送，载荷携带会话标识与记录内容。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    session = FakePushSession()
    spout._session = session
    inlet = PushInlet().bind_spout(spout)

    inlet.on_task_fail(_fail_event(error_id=7, node="s2"))
    spout._handle_record(_dequeue(spout))

    assert len(session.posts) == 1
    url, payload, _timeout = session.posts[0]
    assert url == "http://host:1/api/push_error"
    assert payload["graph_id"] == "g1"
    assert payload["event_id"] == 7
    assert payload["node"] == "s2"
    assert payload["error_type"] == "ValueError"
    assert payload["error_message"] == "oops"
    assert payload["ts"] > 0


def test_spout_pushes_graph_start_to_graph_meta_endpoint() -> None:
    """图元信息会以顶层字段推送到 ``/api/push_graph_meta``。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    session = FakePushSession()
    spout._session = session
    inlet = PushInlet().bind_spout(spout)

    inlet.on_graph_start(_start_event())
    spout._handle_record(_dequeue(spout))

    assert len(session.posts) == 1
    url, payload, _timeout = session.posts[0]
    assert url == "http://host:1/api/push_graph_meta"
    assert payload["graph_id"] == "g1"
    assert payload["graph"] == "g1"
    assert payload["graph_mode"] == "thread"
    assert payload["is_dag"] is True
    assert payload["nodes"] == ["s1", "s2"]
    assert payload["node_meta"]["s1"]["max_workers"] == 2


def test_spout_pushes_graph_end_to_shutdown_endpoint() -> None:
    """图结束记录会推送到 ``/api/shutdown_session``，载荷只带会话标识。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    session = FakePushSession()
    spout._session = session
    inlet = PushInlet().bind_spout(spout)

    inlet.on_graph_end(_end_event())
    spout._handle_record(_dequeue(spout))

    assert len(session.posts) == 1
    url, payload, _timeout = session.posts[0]
    assert url == "http://host:1/api/shutdown_session"
    assert payload == {"graph_id": "g1"}


def test_handle_record_raises_reporter_error_on_failure() -> None:
    """服务端返回非 2xx 时，``_handle_record`` 抛出 ``ReporterError``。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    spout._session = FakePushSession(ok=False)

    with pytest.raises(ReporterError):
        spout._handle_record(PushRecord(kind="task_fail", event_id=1))


def test_spout_thread_drains_records_and_closes_session(monkeypatch) -> None:
    """后台线程启动后，入队的记录会被推送并在 stop 时关闭会话。"""
    session = FakePushSession()
    monkeypatch.setattr(push_module.requests, "Session", lambda: session)

    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    inlet = PushInlet().bind_spout(spout)

    spout.start()
    try:
        inlet.on_task_fail(_fail_event(error_id=7))
        inlet.on_graph_start(_start_event())
        wait_until(
            lambda: len(session.posts) == 2 and spout.get_pending_count() == 0,
            message="records were not pushed in time",
        )
    finally:
        spout.stop()

    assert session.closed
    assert {url for url, _payload, _timeout in session.posts} == {
        "http://host:1/api/push_error",
        "http://host:1/api/push_graph_meta",
    }


def test_spout_thread_survives_push_failure(monkeypatch) -> None:
    """单条推送失败不致死线程：记录被消费完后线程仍能正常 stop。"""
    session = FakePushSession(ok=False)
    monkeypatch.setattr(push_module.requests, "Session", lambda: session)

    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    inlet = PushInlet().bind_spout(spout)

    spout.start()
    try:
        inlet.on_task_fail(_fail_event(error_id=7))
        wait_until(
            lambda: spout.get_pending_count() == 0,
            message="record was not consumed in time",
        )
    finally:
        spout.stop()

    assert session.closed


def test_null_spout_discards_records(monkeypatch) -> None:
    """Null 版本不建立 HTTP 会话，消费到的记录被直接丢弃。"""
    monkeypatch.setattr(
        push_module.requests,
        "Session",
        lambda: pytest.fail("NullPushSpout must not create a session"),
    )
    spout = NullPushSpout()
    inlet = PushInlet().bind_spout(spout)

    spout.start()
    try:
        inlet.on_task_fail(_fail_event())
        inlet.on_graph_start(_start_event())
        wait_until(
            lambda: spout.get_pending_count() == 0,
            message="null spout did not drain records in time",
        )
    finally:
        spout.stop()
