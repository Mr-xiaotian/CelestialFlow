from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from celestialflow.observer import Observer, ObserverHub, ReporterFailureEvent
from celestialflow.reporter import InjectionHandler
from celestialflow.ticker import TickEvent


class FakeResponse:
    """模拟成功拉取注入时的 HTTP 响应。"""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.ok = True
        self.status_code = 200
        self._payload = payload

    def json(self) -> dict[str, Any]:
        """返回预设 JSON 载荷。"""
        return self._payload


class FakeFailResponse:
    """模拟拉取失败（非 2xx）的 HTTP 响应。"""

    ok = False
    status_code = 500

    def json(self) -> dict[str, Any]:
        """返回空载荷（调用方不应访问）。"""
        return {}


class FakeSession:
    """记录拉取请求并返回预设响应的 ``requests.Session`` 替身。"""

    def __init__(self, response: Any) -> None:
        self._response = response
        self.gets: list[tuple[str, dict[str, Any], float]] = []

    def get(
        self, url: str, params: dict[str, Any] | None = None, timeout: float = 0.0
    ) -> Any:
        """记录拉取目标与参数并返回预设响应。"""
        self.gets.append((url, params or {}, timeout))
        return self._response


class FakeTarget:
    """记录注入调用的 ``InjectionTarget`` 替身。"""

    def __init__(self) -> None:
        self.tasks: list[Mapping[str, Sequence[Any]]] = []
        self.terminations: list[Sequence[str]] = []

    def inject_tasks(self, tasks: Mapping[str, Sequence[Any]]) -> None:
        """记录注入的任务。"""
        self.tasks.append(tasks)

    def inject_terminations(self, nodes: Sequence[str]) -> None:
        """记录注入的终止符。"""
        self.terminations.append(nodes)


class RecordingObserver(Observer):
    """记录上报器失败事件。"""

    def __init__(self) -> None:
        self.failures: list[tuple[str, Exception]] = []

    def on_reporter_failure(self, event: ReporterFailureEvent) -> None:
        """记录失败类别与异常。"""
        self.failures.append((event.kind, event.exception))


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


def make_observer() -> tuple[ObserverHub, RecordingObserver]:
    """构造带记录器的图级观察者 hub。"""
    observers = ObserverHub()
    recorder = RecordingObserver()
    observers.add_observer(recorder)
    return observers, recorder


def test_injection_handler_pulls_and_injects() -> None:
    """处理器应从 ``/api/pull_injection`` 拉取并分别注入任务与终止符。"""
    observers, recorder = make_observer()
    target = FakeTarget()
    session = FakeSession(
        FakeResponse({"tasks": {"StageA": [1, 2]}, "terminations": ["StageB"]})
    )
    handler = InjectionHandler("http://host:1", "g1", target, observers, session)

    handler.on_tick(make_event())

    assert target.tasks == [{"StageA": [1, 2]}]
    assert target.terminations == [["StageB"]]
    assert recorder.failures == []
    url, params, _timeout = session.gets[0]
    assert url == "http://host:1/api/pull_injection"
    assert params["graph_id"] == "g1"


def test_injection_handler_reports_pull_failure() -> None:
    """拉取失败时应上报 ``kind="pull_tasks"`` 且不注入任何内容。"""
    observers, recorder = make_observer()
    target = FakeTarget()
    session = FakeSession(FakeFailResponse())
    handler = InjectionHandler("http://host:1", "g1", target, observers, session)

    handler.on_tick(make_event())

    assert [kind for kind, _exc in recorder.failures] == ["pull_tasks"]
    assert target.tasks == []
    assert target.terminations == []


def test_injection_handler_isolates_inject_failures() -> None:
    """任务注入失败不应阻止终止符注入，且上报 ``kind="inject"``。"""

    class RaisingTarget(FakeTarget):
        """任务注入抛错的注入目标。"""

        def inject_tasks(self, tasks: Mapping[str, Sequence[Any]]) -> None:
            """模拟注入失败。"""
            raise RuntimeError("unknown node")

    observers, recorder = make_observer()
    target = RaisingTarget()
    session = FakeSession(
        FakeResponse({"tasks": {"StageA": [1]}, "terminations": ["StageB"]})
    )
    handler = InjectionHandler("http://host:1", "g1", target, observers, session)

    handler.on_tick(make_event())

    assert [kind for kind, _exc in recorder.failures] == ["inject"]
    assert target.terminations == [["StageB"]]


def test_injection_handler_tick_period_is_five() -> None:
    """处理器以 5 拍为周期触发（基准周期 1 秒时即每 5 秒）。"""
    observers, _recorder = make_observer()
    handler = InjectionHandler(
        "http://host:1", "g1", FakeTarget(), observers, FakeSession(FakeResponse({}))
    )

    assert handler.tick_period == 5
    assert [
        seq for seq in range(1, 12) if handler.should_tick(make_event(seq))
    ] == [1, 6, 11]
