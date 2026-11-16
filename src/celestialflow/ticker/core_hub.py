# ticker/core_hub.py
from __future__ import annotations

from contextlib import suppress
from threading import Lock

from ..runtime.util_errors import ConfigurationError
from .core_event import TickEvent
from .core_ticker import Ticker, ensure_tick_period


class TickHub(Ticker):
    """节拍分发中心。

    本身即 :class:`~celestialflow.ticker.core_ticker.Ticker`，与
    :class:`~celestialflow.observer.core_hub.ObserverHub` 对称：既可以被注册进上层
    hub（从而接入更大范围的节拍），也可以把下层 hub 收进来。每一拍按各子 ticker
    自身的 :attr:`~celestialflow.ticker.core_ticker.Ticker.tick_period` 过滤后转发；
    单个回调抛出的异常交由该 ticker 自身的 ``handle_exception`` 处理，不会中断其余
    定时器的分发，若其再抛出则由本 hub 的 ``handle_exception`` 兜底。

    本类不持有时钟，也不产生节拍：时间由
    :class:`~celestialflow.ticker.core_clock.TickClock` 提供，并在装配层驱动整棵
    节拍树的根。因此 hub 可以在根与枝之间自由嵌套，只有时钟才是唯一的时间源头。

    子 ticker 列表采用写时复制（copy-on-write）：写入方在 :attr:`_write_lock` 保护下
    用新的不可变元组整体替换 :attr:`_tickers`，读路径 :meth:`_snapshot` 直接返回
    当前引用，不加锁也不拷贝。由于元组不可变、且 CPython 对属性的读取与替换不会
    撕裂，读到的永远是某个完整版本的快照。

    hub 自身被启动后（:meth:`start`），运行期通过 :meth:`add_ticker` 加入的 ticker
    会立即启动资源，:meth:`remove_ticker` 摘除的 ticker 会立即释放资源，便于外部在
    运行期增删周期任务。
    """

    def __init__(self) -> None:
        """初始化分发中心。"""
        self._tickers: tuple[Ticker, ...] = ()
        self._write_lock = Lock()
        self._started = False

    # ==== 注册 ====

    def add_ticker(self, ticker: Ticker) -> None:
        """
        注册 ticker。

        若本 hub 已启动，则先启动该 ticker 的资源再发布，保证运行期加入的 ticker
        在收到第一拍时已就绪。

        :param ticker: 待注册的 ticker
        :raises ConfigurationError: 该 ticker 已注册、注册会形成 hub 循环引用，
            或 ticker 的 ``tick_period`` 非法
        """
        ensure_tick_period(ticker.tick_period)
        self._reject_cycle(ticker)
        with self._write_lock:
            if any(existing is ticker for existing in self._tickers):
                raise ConfigurationError("ticker is already registered")
            started = self._started

        if started:
            ticker.start()

        with self._write_lock:
            self._tickers = (*self._tickers, ticker)

    def remove_ticker(self, ticker: Ticker) -> None:
        """
        注销 ticker。

        若本 hub 已启动，则摘除后立即释放该 ticker 的资源。

        :param ticker: 待注销的 ticker
        :raises ConfigurationError: 该 ticker 未注册
        """
        with self._write_lock:
            if not any(existing is ticker for existing in self._tickers):
                raise ConfigurationError("ticker is not registered")
            self._tickers = tuple(
                existing for existing in self._tickers if existing is not ticker
            )
            started = self._started

        if started:
            ticker.stop()

    def __contains__(self, ticker: object) -> bool:
        """
        判断某个 ticker 是否直接注册在本 hub 上。

        :param ticker: 待查询的对象
        :return: 直接注册时返回 ``True``；不递归检查下层 hub
        :rtype: bool
        """
        return any(existing is ticker for existing in self._snapshot())

    def _snapshot(self) -> tuple[Ticker, ...]:
        """
        返回当前 ticker 元组。

        :return: 当前 ticker 元组
        """
        return self._tickers

    def _reject_cycle(self, ticker: Ticker) -> None:
        """
        拒绝会形成 hub 循环引用的注册，避免分发时无限递归。

        :param ticker: 待注册的 ticker
        :raises ConfigurationError: 该 ticker 已（间接）持有当前 hub
        """
        if ticker is self:
            raise ConfigurationError("cannot register a TickHub into itself")
        if not isinstance(ticker, TickHub):
            return

        stack: list[TickHub] = [ticker]
        seen: set[int] = set()
        while stack:
            hub = stack.pop()
            if id(hub) in seen:
                continue
            seen.add(id(hub))
            if hub is self:
                raise ConfigurationError(
                    "cyclic TickHub registration detected: cannot register a hub "
                    "into a hub that already (directly or transitively) contains it"
                )
            stack.extend(
                child for child in hub._snapshot() if isinstance(child, TickHub)
            )

    # ==== 查询 ====

    def find[T: Ticker](self, ticker_type: type[T]) -> T | None:
        """
        查找指定类型的 ticker。

        先扫描本层直接注册的 ticker，未命中时再按注册顺序递归进入嵌套 hub，
        因此越靠近调用方的注册越优先。匹配使用 :func:`isinstance`，子类实例
        同样会命中。

        :param ticker_type: 期望的 ticker 类型
        :return: 第一个匹配的 ticker；未找到时返回 ``None``
        """
        tickers = self._snapshot()

        for ticker in tickers:
            if isinstance(ticker, ticker_type):
                return ticker

        for ticker in tickers:
            if isinstance(ticker, TickHub):
                found = ticker.find(ticker_type)
                if found is not None:
                    return found

        return None

    # ==== 生命周期 ====

    def start(self) -> None:
        """按注册顺序启动所有 ticker 持有的资源（幂等）。

        若某个 ticker 的 ``start`` 抛出异常，则按逆序回滚已启动的 ticker 后，将原
        异常重新抛出；尚未启动的 ticker 不会被处理。
        """
        with self._write_lock:
            if self._started:
                return
            self._started = True

        started: list[Ticker] = []
        try:
            for ticker in self._snapshot():
                ticker.start()
                started.append(ticker)
        except Exception:
            for ticker in reversed(started):
                with suppress(Exception):
                    ticker.stop()
            with self._write_lock:
                self._started = False
            raise

    def stop(self) -> None:
        """按注册顺序的逆序停止所有 ticker 持有的资源（幂等）。

        单个 ticker ``stop`` 抛出的异常不会中断其余 ticker 的回收；全部处理完成后，
        若存在异常则汇总为 :class:`ExceptionGroup` 抛出。
        """
        with self._write_lock:
            if not self._started:
                return
            self._started = False

        exceptions: list[Exception] = []
        for ticker in reversed(self._snapshot()):
            try:
                ticker.stop()
            except Exception as exception:
                exceptions.append(exception)
        if exceptions:
            raise ExceptionGroup("failed to stop tickers", exceptions)

    # ==== 分发 ====

    def on_tick(self, event: TickEvent) -> None:
        """
        将当前拍按 ``tick_period`` 过滤后转发给所有命中 ticker。

        子 hub 会继续向下转发，因此嵌套层次只影响过滤与异常隔离的边界，不改变
        节拍来源。

        :param event: 当前节拍事件
        """
        for ticker in self._snapshot():
            if not ticker.should_tick(event):
                continue
            try:
                ticker.on_tick(event)
            except Exception as exception:
                try:
                    ticker.handle_exception(exception)
                except Exception as fallback:
                    self.handle_exception(fallback)
