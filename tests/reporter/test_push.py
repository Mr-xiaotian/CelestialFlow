from typing import Any

import pytest

import celestialflow.reporter.core_push as push_module
from celestialflow.observer import TaskFailEvent
from celestialflow.reporter.core_push import (
    NullPushSpout,
    PushInlet,
    PushSpout,
    to_error_record,
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


def test_to_error_record_maps_fail_event() -> None:
    """失败事件会被映射为服务端接受的上报记录。"""
    event = _fail_event(error_id=7, node="s2", task={"value": 1}, exc=TypeError("bad"))

    record = to_error_record(event)

    assert record["event_id"] == 7
    assert record["node"] == "s2"
    assert record["status"] == "failed"
    assert record["error_type"] == "TypeError"
    assert record["error_message"] == "bad"
    assert record["task_json"] == {"value": 1}
    assert record["ts"] > 0


def test_spout_pushes_record_to_push_errors_endpoint() -> None:
    """单条失败记录会以 push_errors 推送，载荷携带会话标识与记录内容。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1", batch_size=1)
    session = FakePushSession()
    spout._session = session
    inlet = PushInlet().bind_spout(spout)

    inlet.on_task_fail(_fail_event(error_id=7, node="s2"))
    spout._handle_record(spout.get_queue().get())

    assert len(session.posts) == 1
    url, payload, _timeout = session.posts[0]
    assert url == "http://host:1/api/push_errors"
    assert payload["graph_id"] == "g1"
    assert len(payload["errors"]) == 1
    record = payload["errors"][0]
    assert record["event_id"] == 7
    assert record["node"] == "s2"
    assert record["status"] == "failed"
    assert record["error_type"] == "ValueError"
    assert record["error_message"] == "oops"


def test_spout_thread_pushes_records(monkeypatch) -> None:
    """后台线程启动后，入队的失败记录会被推送并关闭会话。"""
    session = FakePushSession()
    monkeypatch.setattr(push_module.requests, "Session", lambda: session)

    spout = PushSpout(graph_id="g1", base_url="http://host:1", flush_interval=0.05)
    inlet = PushInlet().bind_spout(spout)

    spout.start()
    try:
        inlet.on_task_fail(_fail_event(error_id=7))
        wait_until(
            lambda: len(session.posts) == 1 and spout.get_pending_count() == 0,
            message="error record was not pushed in time",
        )
    finally:
        spout.stop()

    assert session.closed
    _url, payload, _timeout = session.posts[0]
    assert payload["errors"][0]["event_id"] == 7


def test_post_raises_on_push_failure() -> None:
    """服务端返回非 2xx 时，`_post` 抛出 ReporterError。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    spout._session = FakePushSession(ok=False)

    with pytest.raises(ReporterError):
        spout._post([{"event_id": 1}])


def test_flush_swallows_push_failure(capsys) -> None:
    """`_flush` 推送失败时不向外抛出，且缓冲已被取走、不会重复发送。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1")
    session = FakePushSession(ok=False)
    spout._session = session
    spout._handle_record({"event_id": 1})

    spout._flush()

    assert "ReporterError" in capsys.readouterr().err
    assert len(session.posts) == 1
    assert spout._buffer == []


def test_flush_batches_buffered_records() -> None:
    """缓冲达到 batch_size 时，多条记录合并为一次 push_errors 请求。"""
    spout = PushSpout(graph_id="g1", base_url="http://host:1", batch_size=3)
    session = FakePushSession()
    spout._session = session

    for event_id in range(3):
        spout._handle_record({"event_id": event_id})

    assert len(session.posts) == 1
    _url, payload, _timeout = session.posts[0]
    assert [record["event_id"] for record in payload["errors"]] == [0, 1, 2]


def test_stop_flushes_remaining_records(monkeypatch) -> None:
    """stop() 会冲刷未达 batch_size 的尾部记录。"""
    session = FakePushSession()
    monkeypatch.setattr(push_module.requests, "Session", lambda: session)

    spout = PushSpout(
        graph_id="g1",
        base_url="http://host:1",
        batch_size=10,
        flush_interval=0,
    )
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

    assert len(session.posts) == 1
    _url, payload, _timeout = session.posts[0]
    assert payload["errors"][0]["event_id"] == 7


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
        wait_until(
            lambda: spout.get_pending_count() == 0,
            message="null spout did not drain records in time",
        )
    finally:
        spout.stop()
