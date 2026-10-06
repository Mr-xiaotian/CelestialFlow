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
    处理器无需自行计数。该值可在运行期经 :meth:`set_tick_period` 调整。
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

    def set_tick_period(self, tick_period: int) -> None:
        """
        设置本处理器每隔多少拍被触发一次，下一拍起生效。

        分发路径每拍都会重新读取 :attr:`tick_period`，因此变更无需重启节拍器即可
        对 :class:`~celestialflow.ticker.core_hub.TickHub` 与
        :class:`~celestialflow.ticker.core_ticker.Ticker` 生效。过滤仍以
        :attr:`~celestialflow.ticker.core_event.TickEvent.seq` 为基准（第 1 拍始终
        命中），因此调整后相位重新锚定到 ``seq == 1``。

        :param tick_period: 每隔多少拍触发一次，必须为正整数
        :raises ConfigurationError: ``tick_period`` 小于 1
        """
        if tick_period < 1:
            raise ConfigurationError(
                f"tick_period must be a positive integer, got {tick_period}"
            )
        self.tick_period = tick_period

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
