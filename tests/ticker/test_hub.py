from __future__ import annotations

import pytest

from celestialflow.runtime.util_errors import ConfigurationError
from celestialflow.ticker import TickEvent, TickHandler, TickHub


def make_event(seq: int = 1) -> TickEvent:
    """
    构造一个测试用节拍事件。

    :param seq: 节拍序号
    :return: 节拍事件
    """
    return TickEvent(
        seq=seq,
        interval=1.0,
        scheduled_at=float(seq),
        fired_at=float(seq),
        wall_time=float(seq),
        drift=0.0,
        skipped=0,
    )


class RecordingHandler(TickHandler):
    """记录命中的节拍序号。"""

    def __init__(self, tick_period: int = 1) -> None:
        """初始化记录器。

        :param tick_period: 每隔多少拍记录一次
        """
        self.tick_period = tick_period
        self.seqs: list[int] = []

    def on_tick(self, event: TickEvent) -> None:
        """记录节拍序号。

        :param event: 当前节拍事件
        """
        self.seqs.append(event.seq)


def test_hub_fans_out_to_all_handlers() -> None:
    """同一拍应分发给所有注册处理器。"""
    hub = TickHub()
    first = RecordingHandler()
    second = RecordingHandler()
    hub.add_handler(first)
    hub.add_handler(second)

    hub.on_tick(make_event(1))

    assert first.seqs == [1]
    assert second.seqs == [1]


def test_hub_filters_by_tick_period() -> None:
    """各处理器应按自身 ``tick_period`` 独立过滤。"""
    hub = TickHub()
    every = RecordingHandler(tick_period=1)
    every_other = RecordingHandler(tick_period=2)
    hub.add_handler(every)
    hub.add_handler(every_other)

    for seq in range(1, 6):
        hub.on_tick(make_event(seq))

    assert every.seqs == [1, 2, 3, 4, 5]
    assert every_other.seqs == [1, 3, 5]


def test_hub_picks_up_runtime_tick_period_change() -> None:
    """运行中调用 ``set_tick_period`` 应立即影响后续分发。"""
    hub = TickHub()
    handler = RecordingHandler(tick_period=1)
    hub.add_handler(handler)

    for seq in range(1, 4):
        hub.on_tick(make_event(seq))
    assert handler.seqs == [1, 2, 3]

    handler.set_tick_period(3)
    for seq in range(4, 10):
        hub.on_tick(make_event(seq))

    assert handler.seqs == [1, 2, 3, 4, 7]


def test_hub_rejects_self_registration() -> None:
    """hub 不能注册自身。"""
    hub = TickHub()

    with pytest.raises(ConfigurationError):
        hub.add_handler(hub)


def test_hub_rejects_cycle_registration() -> None:
    """会形成循环引用的 hub 注册应被拒绝。"""
    hub_a = TickHub()
    hub_b = TickHub()
    hub_a.add_handler(hub_b)

    with pytest.raises(ConfigurationError):
        hub_b.add_handler(hub_a)


def test_hub_rejects_invalid_tick_period() -> None:
    """``tick_period`` 小于 1 的处理器应被拒绝注册。"""
    hub = TickHub()

    with pytest.raises(ConfigurationError):
        hub.add_handler(RecordingHandler(tick_period=0))


def test_hub_isolates_handler_exceptions() -> None:
    """单个处理器抛异常不应影响其余处理器，异常交由该处理器自身处理。"""

    class FailingHandler(TickHandler):
        """抛异常并收集异常的处理器。"""

        def __init__(self) -> None:
            self.errors: list[Exception] = []

        def on_tick(self, event: TickEvent) -> None:
            """抛异常。"""
            raise RuntimeError("boom")

        def handle_exception(self, exception: Exception) -> None:
            """收集异常。"""
            self.errors.append(exception)

    hub = TickHub()
    failing = FailingHandler()
    ok = RecordingHandler()
    hub.add_handler(failing)
    hub.add_handler(ok)

    hub.on_tick(make_event(1))

    assert len(failing.errors) == 1
    assert ok.seqs == [1]


class LifecycleHandler(TickHandler):
    """记录启停调用并可选择性失败的处理器。"""

    def __init__(
        self,
        log: list[str],
        name: str,
        *,
        fail_on_start: bool = False,
        fail_on_stop: bool = False,
    ) -> None:
        self._log = log
        self._name = name
        self._fail_on_start = fail_on_start
        self._fail_on_stop = fail_on_stop

    def start(self) -> None:
        """记录启动或抛出预设异常。"""
        if self._fail_on_start:
            raise RuntimeError(f"{self._name} start")
        self._log.append(f"start:{self._name}")

    def stop(self) -> None:
        """记录停止或抛出预设异常。"""
        if self._fail_on_stop:
            raise RuntimeError(f"{self._name} stop")
        self._log.append(f"stop:{self._name}")


def test_hub_starts_in_order_and_stops_in_reverse() -> None:
    """hub 应按注册顺序启动，按逆序停止。"""
    log: list[str] = []
    hub = TickHub()
    hub.add_handler(LifecycleHandler(log, "a"))
    hub.add_handler(LifecycleHandler(log, "b"))

    hub.start()
    assert log == ["start:a", "start:b"]

    log.clear()
    hub.stop()
    assert log == ["stop:b", "stop:a"]


def test_hub_rolls_back_started_handlers_on_start_failure() -> None:
    """启动失败时应逆序回滚已启动的处理器，不再启动后续处理器。"""
    log: list[str] = []
    hub = TickHub()
    hub.add_handler(LifecycleHandler(log, "a"))
    hub.add_handler(LifecycleHandler(log, "b", fail_on_start=True))
    hub.add_handler(LifecycleHandler(log, "c"))

    with pytest.raises(RuntimeError, match="b start"):
        hub.start()

    assert log == ["start:a", "stop:a"]


def test_hub_stop_aggregates_failures_and_keeps_stopping() -> None:
    """单个处理器停止失败不应中断其余处理器，异常最终聚合抛出。"""
    log: list[str] = []
    hub = TickHub()
    hub.add_handler(LifecycleHandler(log, "a"))
    hub.add_handler(LifecycleHandler(log, "b", fail_on_stop=True))

    with pytest.raises(ExceptionGroup):
        hub.stop()

    assert log == ["stop:a"]
