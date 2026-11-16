from __future__ import annotations

import pytest

from celestialflow.runtime.util_errors import ConfigurationError
from celestialflow.ticker import Ticker, TickEvent, TickHub


def make_event(seq: int = 1) -> TickEvent:
    """
    构造一个测试用节拍事件。

    :param seq: 节拍序号
    :return: 节拍事件
    """
    return TickEvent(seq=seq, fired_at=float(seq), wall_time=float(seq))


class RecordingTicker(Ticker):
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


class LifecycleTicker(Ticker):
    """记录启停调用并可选择性失败的 ticker。"""

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


# ==== 分发 ====


def test_hub_fans_out_to_all_tickers() -> None:
    """同一拍应分发给所有注册 ticker。"""
    hub = TickHub()
    first = RecordingTicker()
    second = RecordingTicker()
    hub.add_ticker(first)
    hub.add_ticker(second)

    hub.on_tick(make_event(1))

    assert first.seqs == [1]
    assert second.seqs == [1]


def test_hub_filters_by_tick_period() -> None:
    """各 ticker 应按自身 ``tick_period`` 独立过滤。"""
    hub = TickHub()
    every = RecordingTicker(tick_period=1)
    every_other = RecordingTicker(tick_period=2)
    hub.add_ticker(every)
    hub.add_ticker(every_other)

    for seq in range(1, 6):
        hub.on_tick(make_event(seq))

    assert every.seqs == [1, 2, 3, 4, 5]
    assert every_other.seqs == [1, 3, 5]


def test_hub_picks_up_runtime_tick_period_change() -> None:
    """运行中调用 ``set_tick_period`` 应立即影响后续分发。"""
    hub = TickHub()
    ticker = RecordingTicker(tick_period=1)
    hub.add_ticker(ticker)

    for seq in range(1, 4):
        hub.on_tick(make_event(seq))
    assert ticker.seqs == [1, 2, 3]

    ticker.set_tick_period(3)
    for seq in range(4, 10):
        hub.on_tick(make_event(seq))

    assert ticker.seqs == [1, 2, 3, 4, 7]


def test_hub_forwards_to_nested_hub() -> None:
    """嵌套 hub 应逐层过滤后把节拍送达下层 ticker。"""
    inner = TickHub()
    inner.set_tick_period(2)
    ticker = RecordingTicker(tick_period=3)
    inner.add_ticker(ticker)

    outer = TickHub()
    outer.add_ticker(inner)

    for seq in range(1, 10):
        outer.on_tick(make_event(seq))

    # 嵌套周期按 ``(seq - 1)`` 的最小公倍数复合：lcm(2, 3) = 6。
    assert ticker.seqs == [1, 7]


def test_hub_isolates_ticker_exceptions() -> None:
    """单个 ticker 抛异常不应影响其余 ticker，异常交由该 ticker 自身处理。"""

    class FailingTicker(Ticker):
        """抛异常并收集异常的 ticker。"""

        def __init__(self) -> None:
            self.errors: list[Exception] = []

        def on_tick(self, event: TickEvent) -> None:
            """抛异常。"""
            raise RuntimeError("boom")

        def handle_exception(self, exception: Exception) -> None:
            """收集异常。"""
            self.errors.append(exception)

    hub = TickHub()
    failing = FailingTicker()
    ok = RecordingTicker()
    hub.add_ticker(failing)
    hub.add_ticker(ok)

    hub.on_tick(make_event(1))

    assert len(failing.errors) == 1
    assert ok.seqs == [1]


def test_hub_backstops_ticker_exception() -> None:
    """ticker 自身的 ``handle_exception`` 再抛时，由 hub 兜底且不影响后续 ticker。"""

    class BadTicker(Ticker):
        """回调与异常处理均抛异常的 ticker。"""

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
    ok = RecordingTicker()
    hub.add_ticker(BadTicker())
    hub.add_ticker(ok)

    hub.on_tick(make_event(1))

    assert len(hub.fallbacks) == 1
    assert ok.seqs == [1]


# ==== 查询 ====


def test_hub_find_returns_direct_ticker() -> None:
    """``find`` 应返回本层直接注册的匹配 ticker。"""
    hub = TickHub()
    ticker = RecordingTicker()
    hub.add_ticker(ticker)

    assert hub.find(RecordingTicker) is ticker


def test_hub_find_recurses_into_nested_hub() -> None:
    """``find`` 未命中本层时应递归进入嵌套 hub。"""
    inner = TickHub()
    ticker = RecordingTicker()
    inner.add_ticker(ticker)

    outer = TickHub()
    outer.add_ticker(inner)

    assert outer.find(RecordingTicker) is ticker


def test_hub_find_prefers_direct_registration() -> None:
    """本层直接注册的 ticker 优先于嵌套 hub 中的匹配项。"""
    inner = TickHub()
    inner.add_ticker(RecordingTicker())

    direct = RecordingTicker()
    outer = TickHub()
    outer.add_ticker(inner)
    outer.add_ticker(direct)

    assert outer.find(RecordingTicker) is direct


def test_hub_find_matches_subclass() -> None:
    """``find`` 使用 ``isinstance`` 匹配，子类实例同样命中。"""

    class SpecialTicker(RecordingTicker):
        """``RecordingTicker`` 的子类。"""

    hub = TickHub()
    ticker = SpecialTicker()
    hub.add_ticker(ticker)

    assert hub.find(Ticker) is ticker


def test_hub_find_returns_none_when_missing() -> None:
    """没有匹配项时 ``find`` 返回 ``None``。"""
    hub = TickHub()
    hub.add_ticker(RecordingTicker())

    assert hub.find(LifecycleTicker) is None


def test_hub_contains_reports_direct_registration() -> None:
    """``in`` 只判断直接注册，不递归嵌套 hub。"""
    ticker = RecordingTicker()
    inner = TickHub()
    inner.add_ticker(ticker)

    outer = TickHub()
    outer.add_ticker(inner)

    assert ticker in inner
    assert ticker not in outer
    assert inner in outer


# ==== 注册校验 ====


def test_hub_rejects_self_registration() -> None:
    """hub 不能注册进自身。"""
    hub = TickHub()

    with pytest.raises(ConfigurationError):
        hub.add_ticker(hub)


def test_hub_rejects_cycle_registration() -> None:
    """会形成循环引用的 hub 注册应被拒绝。"""
    hub_a = TickHub()
    hub_b = TickHub()
    hub_a.add_ticker(hub_b)

    with pytest.raises(ConfigurationError):
        hub_b.add_ticker(hub_a)


def test_hub_rejects_duplicate_registration() -> None:
    """同一个 ticker 不能被重复注册。"""
    hub = TickHub()
    ticker = RecordingTicker()
    hub.add_ticker(ticker)

    with pytest.raises(ConfigurationError):
        hub.add_ticker(ticker)


def test_hub_rejects_invalid_tick_period() -> None:
    """``tick_period`` 小于 1 的 ticker 应被拒绝注册。"""
    hub = TickHub()

    with pytest.raises(ConfigurationError):
        hub.add_ticker(RecordingTicker(tick_period=0))


def test_hub_remove_ticker() -> None:
    """注销后不再分发，且可以重新注册。"""
    hub = TickHub()
    ticker = RecordingTicker()
    hub.add_ticker(ticker)

    hub.remove_ticker(ticker)
    hub.on_tick(make_event(1))
    assert ticker.seqs == []

    hub.add_ticker(ticker)
    hub.on_tick(make_event(2))
    assert ticker.seqs == [2]


def test_hub_remove_unknown_ticker_raises() -> None:
    """注销未注册的 ticker 应报错。"""
    hub = TickHub()

    with pytest.raises(ConfigurationError):
        hub.remove_ticker(RecordingTicker())


# ==== 生命周期 ====


def test_hub_starts_in_order_and_stops_in_reverse() -> None:
    """hub 应按注册顺序启动，按逆序停止。"""
    log: list[str] = []
    hub = TickHub()
    hub.add_ticker(LifecycleTicker(log, "a"))
    hub.add_ticker(LifecycleTicker(log, "b"))

    hub.start()
    assert log == ["start:a", "start:b"]

    hub.stop()
    assert log == ["start:a", "start:b", "stop:b", "stop:a"]


def test_hub_start_and_stop_are_idempotent() -> None:
    """重复启动/停止不应重复触碰 ticker 资源。"""
    log: list[str] = []
    hub = TickHub()
    hub.add_ticker(LifecycleTicker(log, "a"))

    hub.start()
    hub.start()
    assert log == ["start:a"]

    hub.stop()
    hub.stop()
    assert log == ["start:a", "stop:a"]


def test_hub_rolls_back_started_tickers_on_start_failure() -> None:
    """启动失败时应逆序回滚已启动的 ticker，不再启动后续 ticker。"""
    log: list[str] = []
    hub = TickHub()
    hub.add_ticker(LifecycleTicker(log, "a"))
    hub.add_ticker(LifecycleTicker(log, "b", fail_on_start=True))
    hub.add_ticker(LifecycleTicker(log, "c"))

    with pytest.raises(RuntimeError, match="b start"):
        hub.start()

    assert log == ["start:a", "stop:a"]


def test_hub_start_retry_after_failure_starts_all_tickers() -> None:
    """启动失败后再次启动应重新尝试全部 ticker。"""
    log: list[str] = []
    hub = TickHub()
    hub.add_ticker(LifecycleTicker(log, "a"))
    failing = LifecycleTicker(log, "b", fail_on_start=True)
    hub.add_ticker(failing)

    with pytest.raises(RuntimeError):
        hub.start()

    failing._fail_on_start = False
    hub.start()

    assert log == ["start:a", "stop:a", "start:a", "start:b"]
    hub.stop()


def test_hub_stop_aggregates_failures_and_keeps_stopping() -> None:
    """单个 ticker 停止失败不应中断其余 ticker，异常最终聚合抛出。"""
    log: list[str] = []
    hub = TickHub()
    hub.add_ticker(LifecycleTicker(log, "a"))
    hub.add_ticker(LifecycleTicker(log, "b", fail_on_stop=True))

    hub.start()
    log.clear()

    with pytest.raises(ExceptionGroup):
        hub.stop()

    assert log == ["stop:a"]


def test_hub_add_ticker_while_started_starts_resources() -> None:
    """运行期加入的 ticker 应立即启动资源。"""
    log: list[str] = []
    hub = TickHub()
    hub.start()

    late = LifecycleTicker(log, "late")
    hub.add_ticker(late)
    assert log == ["start:late"]

    hub.stop()
    assert log == ["start:late", "stop:late"]


def test_hub_remove_ticker_while_started_stops_resources() -> None:
    """运行期摘除的 ticker 应立即释放资源。"""
    log: list[str] = []
    hub = TickHub()
    ticker = LifecycleTicker(log, "a")
    hub.add_ticker(ticker)
    hub.start()

    hub.remove_ticker(ticker)
    assert log == ["start:a", "stop:a"]

    hub.stop()
    assert log == ["start:a", "stop:a"]
