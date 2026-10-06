from __future__ import annotations

import time

import pytest

from celestialflow.ticker import TickEvent, TickHandler, TickHub, Ticker
from celestialflow.runtime.util_errors import ConfigurationError
from conftest import assert_stays_true, wait_until


class RecordingHandler(TickHandler):
    """记录收到的节拍事件。"""

    def __init__(self, tick_period: int = 1) -> None:
        """初始化记录器。

        :param tick_period: 每隔多少拍记录一次
        """
        self.tick_period = tick_period
        self.events: list[TickEvent] = []

    def on_tick(self, event: TickEvent) -> None:
        """记录节拍事件。

        :param event: 当前节拍事件
        """
        self.events.append(event)


def test_ticker_fires_periodically_and_stops() -> None:
    """节拍器应按周期持续触发，并在停止后不再产生新节拍。"""
    handler = RecordingHandler()
    ticker = Ticker(0.02, handler)

    ticker.start()
    wait_until(lambda: len(handler.events) >= 3, timeout=2.0)
    ticker.stop()

    assert not ticker.is_running()
    assert [event.seq for event in handler.events] == list(
        range(1, len(handler.events) + 1)
    )

    count = len(handler.events)
    assert_stays_true(
        lambda: len(handler.events) == count,
        duration=0.1,
        message="ticker kept firing after stop",
    )


def test_ticker_honors_handler_tick_period() -> None:
    """处理器声明的 ``tick_period`` 应生效，仅命中节拍被触发。"""
    handler = RecordingHandler(tick_period=2)
    ticker = Ticker(0.02, handler)

    ticker.start()
    try:
        wait_until(lambda: len(handler.events) >= 2, timeout=2.0)
    finally:
        ticker.stop()

    assert handler.events != []
    assert all(event.seq % 2 == 1 for event in handler.events)


def test_ticker_set_interval_takes_effect() -> None:
    """``set_interval`` 应即时生效并重新锚定计划时刻。"""
    handler = RecordingHandler()
    ticker = Ticker(30.0, handler)

    ticker.start()
    try:
        assert handler.events == []
        ticker.set_interval(0.02)
        wait_until(lambda: len(handler.events) >= 1, timeout=2.0)
    finally:
        ticker.stop()

    assert ticker.get_interval() == 0.02


def test_ticker_reports_skipped_ticks_on_overrun() -> None:
    """单拍处理耗时超过周期时，应跳过错拍并记录 ``skipped``。"""

    class SlowHandler(TickHandler):
        """每拍睡眠远超周期的处理器。"""

        def __init__(self) -> None:
            self.events: list[TickEvent] = []

        def on_tick(self, event: TickEvent) -> None:
            """记录事件后睡眠，制造超时。"""
            self.events.append(event)
            time.sleep(0.05)

    handler = SlowHandler()
    ticker = Ticker(0.01, handler)

    ticker.start()
    try:
        wait_until(
            lambda: any(event.skipped > 0 for event in handler.events),
            timeout=3.0,
        )
    finally:
        ticker.stop()


def test_ticker_isolates_handler_exceptions() -> None:
    """处理器抛出的异常应交给自身处理，且不中断后续节拍。"""

    class FailingHandler(TickHandler):
        """持续抛异常的处理器。"""

        def __init__(self) -> None:
            self.count = 0
            self.errors: list[Exception] = []

        def on_tick(self, event: TickEvent) -> None:
            """每次触发都抛异常。"""
            self.count += 1
            raise RuntimeError("boom")

        def handle_exception(self, exception: Exception) -> None:
            """收集异常。"""
            self.errors.append(exception)

    handler = FailingHandler()
    ticker = Ticker(0.01, handler)

    ticker.start()
    try:
        wait_until(
            lambda: handler.count >= 3 and len(handler.errors) >= 3,
            timeout=2.0,
        )
    finally:
        ticker.stop()


def test_ticker_backstops_handler_exception_via_root_hub() -> None:
    """根为 TickHub 时，子处理器逃逸的异常由 hub 的 handle_exception 兜底，循环存活。"""

    class BadHandler(TickHandler):
        """回调与异常处理均抛异常的处理器。"""

        def on_tick(self, event: TickEvent) -> None:
            """抛异常。"""
            raise RuntimeError("boom")

        def handle_exception(self, exception: Exception) -> None:
            """再次抛异常。"""
            raise RuntimeError("also boom")

    class RecordingHub(TickHub):
        """记录兜底异常的 hub。"""

        def __init__(self) -> None:
            super().__init__()
            self.fallbacks: list[Exception] = []

        def handle_exception(self, exception: Exception) -> None:
            """收集兜底异常。"""
            self.fallbacks.append(exception)

    hub = RecordingHub()
    hub.add_handler(BadHandler())
    ticker = Ticker(0.01, hub)

    ticker.start()
    try:
        wait_until(lambda: len(hub.fallbacks) >= 1, timeout=2.0)
        assert ticker.is_running()
    finally:
        ticker.stop()


def test_ticker_rejects_non_positive_interval() -> None:
    """非正的构造周期与 ``set_interval`` 取值应被拒绝。"""
    handler = RecordingHandler()

    with pytest.raises(ConfigurationError):
        Ticker(0.0, handler)

    ticker = Ticker(0.1, handler)
    with pytest.raises(ConfigurationError):
        ticker.set_interval(-1.0)
