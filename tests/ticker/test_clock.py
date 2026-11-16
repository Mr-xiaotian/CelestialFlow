from __future__ import annotations

import time

import pytest
from conftest import assert_stays_true, wait_until

from celestialflow.runtime.util_errors import ConfigurationError
from celestialflow.ticker import TickClock, Ticker, TickEvent, TickHub


class RecordingTicker(Ticker):
    """记录命中的节拍事件。"""

    def __init__(self) -> None:
        self.events: list[TickEvent] = []

    def on_tick(self, event: TickEvent) -> None:
        """记录节拍事件。

        :param event: 当前节拍事件
        """
        self.events.append(event)


def test_clock_fires_periodically_and_stops() -> None:
    """时钟应按周期持续触发，并在停止后不再产生新节拍。"""
    ticker = RecordingTicker()
    hub = TickHub()
    hub.add_ticker(ticker)
    clock = TickClock(0.02, hub)

    clock.start()
    try:
        wait_until(lambda: len(ticker.events) >= 3, timeout=2.0)
    finally:
        clock.stop()

    assert not clock.is_running()
    assert [event.seq for event in ticker.events] == list(
        range(1, len(ticker.events) + 1)
    )

    count = len(ticker.events)
    assert_stays_true(
        lambda: len(ticker.events) == count,
        duration=0.1,
        message="clock kept firing after stop",
    )


def test_clock_drives_single_ticker() -> None:
    """时钟可以绕过 hub，直接驱动单个 ticker。"""
    ticker = RecordingTicker()
    clock = TickClock(0.02, ticker)

    clock.start()
    try:
        wait_until(lambda: len(ticker.events) >= 1, timeout=2.0)
    finally:
        clock.stop()

    assert ticker.events[0].seq == 1


def test_clock_honors_root_tick_period() -> None:
    """根 ticker 自身的 ``tick_period`` 同样参与过滤。"""
    ticker = RecordingTicker()
    ticker.set_tick_period(2)
    clock = TickClock(0.01, ticker)

    clock.start()
    try:
        wait_until(lambda: len(ticker.events) >= 2, timeout=2.0)
    finally:
        clock.stop()

    assert all(event.seq % 2 == 1 for event in ticker.events)


def test_clock_set_interval_takes_effect() -> None:
    """``set_interval`` 应即时生效并重新锚定计划时刻。"""
    ticker = RecordingTicker()
    clock = TickClock(30.0, ticker)

    clock.start()
    try:
        assert ticker.events == []
        clock.set_interval(0.02)
        wait_until(lambda: len(ticker.events) >= 1, timeout=2.0)
    finally:
        clock.stop()

    assert clock.get_interval() == 0.02


def test_clock_does_not_catch_up_after_slow_tick() -> None:
    """单拍处理超过周期时应跳过错拍，恢复后不补发积压的节拍。"""

    class StallOnceTicker(Ticker):
        """首拍睡眠造成迟滞，之后记录每拍的触发时刻。"""

        def __init__(self) -> None:
            self.fired_at: list[float] = []
            self._stalled = False

        def on_tick(self, event: TickEvent) -> None:
            """记录触发时刻；首拍额外睡眠，制造错拍。"""
            self.fired_at.append(event.fired_at)
            if not self._stalled:
                self._stalled = True
                time.sleep(0.1)

    ticker = StallOnceTicker()
    clock = TickClock(0.01, ticker)

    clock.start()
    try:
        wait_until(lambda: len(ticker.fired_at) >= 3, timeout=2.0)
    finally:
        clock.stop()

    gaps = [
        later - earlier
        for earlier, later in zip(ticker.fired_at, ticker.fired_at[1:])
    ]
    # 若不跳过错拍，恢复后会立刻补发一串积压节拍，相邻触发间隔接近 0。
    assert min(gaps) > 0.001


def test_clock_continues_after_ticker_exception() -> None:
    """hub 已隔离 ticker 异常时，时钟应持续运行。"""

    class FailingTicker(Ticker):
        """持续抛异常的 ticker。"""

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

    ticker = FailingTicker()
    hub = TickHub()
    hub.add_ticker(ticker)
    clock = TickClock(0.01, hub)

    clock.start()
    try:
        wait_until(
            lambda: ticker.count >= 3 and len(ticker.errors) >= 3,
            timeout=2.0,
        )
        assert clock.is_running()
    finally:
        clock.stop()


def test_clock_survives_failing_root_handler(capsys) -> None:
    """作为根的 ticker 连兜底都抛出时，时钟仍应打印回溯并继续运行。"""

    class BadRoot(Ticker):
        """回调与异常处理均抛异常的根 ticker。"""

        def on_tick(self, event: TickEvent) -> None:
            """抛异常。"""
            raise RuntimeError("boom")

        def handle_exception(self, exception: Exception) -> None:
            """再次抛异常。"""
            raise RuntimeError("also boom")

    clock = TickClock(0.01, BadRoot())
    clock.start()
    try:
        wait_until(lambda: "also boom" in capsys.readouterr().err, timeout=2.0)
        assert clock.is_running()
    finally:
        clock.stop()


def test_clock_rejects_non_positive_interval() -> None:
    """非正的构造周期与 ``set_interval`` 取值应被拒绝。"""
    clock_ticker = RecordingTicker()

    with pytest.raises(ConfigurationError):
        TickClock(0.0, clock_ticker)

    clock = TickClock(0.1, clock_ticker)
    with pytest.raises(ConfigurationError):
        clock.set_interval(-1.0)
