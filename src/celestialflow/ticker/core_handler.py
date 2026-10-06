# ticker/core_handler.py
from __future__ import annotations

import traceback

from ..runtime.util_errors import ConfigurationError
from .core_event import TickEvent


class TickHandler:
    """时钟节拍处理器基类。

    与事件驱动的 :class:`~celestialflow.observer.core_observer.Observer` 对称：
    所有回调均提供默认实现，实现方继承本基类即可只覆写关心的 :meth:`on_tick`。

    :attr:`tick_period` 声明本处理器每隔多少拍被触发一次（默认每拍都触发）。
    :class:`~celestialflow.ticker.core_ticker.Ticker` 与
    :class:`~celestialflow.ticker.core_hub.TickHub` 在分发前会依据该值过滤，因此
    处理器无需自行计数。
    """

    tick_period: int = 1

    def should_tick(self, event: TickEvent) -> bool:
        """
        判断本处理器是否应在当前拍被触发。

        :param event: 当前节拍事件
        :return: 命中 :attr:`tick_period` 节拍时返回 ``True``
        :rtype: bool
        """
        return (event.seq - 1) % self.tick_period == 0

    def on_tick(self, event: TickEvent) -> None:
        """
        节拍回调。

        :param event: 当前节拍事件
        """
        ...

    def handle_exception(self, exception: Exception) -> None:
        """
        节拍回调自身抛出异常时的处理回调。

        默认实现将异常回溯打印到标准错误；子类可覆写以实现自定义策略（如收集、
        上报或忽略）。若本方法自身也抛出异常，异常会继续向上传播：作为
        :class:`~celestialflow.ticker.core_hub.TickHub` 的子处理器时，由该 hub 的
        ``handle_exception`` 兜底；作为
        :class:`~celestialflow.ticker.core_ticker.Ticker` 的根处理器时，异常会逃逸
        并终止节拍线程。

        :param exception: 节拍回调抛出的异常
        """
        traceback.print_exception(exception)


def validate_tick_period(handler: TickHandler) -> None:
    """
    校验处理器的 ``tick_period`` 合法（不小于 1）。

    :param handler: 待校验的处理器
    :raises ConfigurationError: ``tick_period`` 小于 1
    """
    if handler.tick_period < 1:
        raise ConfigurationError(
            f"tick_period must be a positive integer, got {handler.tick_period}"
        )
