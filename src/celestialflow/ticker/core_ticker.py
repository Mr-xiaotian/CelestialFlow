# ticker/core_ticker.py
from __future__ import annotations

import traceback

from ..runtime.util_errors import ConfigurationError
from .core_event import TickEvent


def ensure_tick_period(tick_period: int) -> None:
    """
    校验 ``tick_period`` 合法（不小于 1）。

    仅供本包内部使用：:meth:`Ticker.set_tick_period` 与
    :meth:`~celestialflow.ticker.core_hub.TickHub.add_ticker` 在写入前调用本函数。

    :param tick_period: 待校验的节拍周期
    :raises ConfigurationError: ``tick_period`` 小于 1
    """
    if tick_period < 1:
        raise ConfigurationError(
            f"tick_period must be a positive integer, got {tick_period}"
        )


class Ticker:
    """按固定周期接收节拍的定时器叶子。

    与事件驱动的 :class:`~celestialflow.observer.core_observer.Observer` 对称：
    所有回调均提供默认实现，实现方继承本基类后只需覆写关心的 :meth:`on_tick`。

    本类本身不产生节拍，也不持有线程：时间由
    :class:`~celestialflow.ticker.core_clock.TickClock` 产生，经
    :class:`~celestialflow.ticker.core_hub.TickHub` 逐层分发，因此 ``Ticker``
    只声明"我每隔多少拍关心一次"以及"收到节拍时做什么"。

    :attr:`tick_period` 声明本定时器每隔多少拍被触发一次（默认每拍都触发）。
    :class:`~celestialflow.ticker.core_hub.TickHub` 在分发前依据该值过滤，因此
    实现方无需自行计数。该值可在运行期经 :meth:`set_tick_period` 调整。
    """

    tick_period: int = 1

    def should_tick(self, event: TickEvent) -> bool:
        """
        判断本定时器是否应在当前拍被触发。

        :param event: 当前节拍事件
        :return: 命中 :attr:`tick_period` 节拍时返回 ``True``
        :rtype: bool
        """
        return (event.seq - 1) % self.tick_period == 0

    def set_tick_period(self, tick_period: int) -> None:
        """
        设置本定时器每隔多少拍被触发一次，下一拍起生效。

        分发路径每拍都会重新读取 :attr:`tick_period`，因此变更无需重启节拍器即可
        对 :class:`~celestialflow.ticker.core_hub.TickHub` 生效。过滤仍以
        :attr:`~celestialflow.ticker.core_event.TickEvent.seq` 为基准（第 1 拍始终
        命中），因此调整后相位重新锚定到 ``seq == 1``。

        :param tick_period: 每隔多少拍触发一次，必须为正整数
        :raises ConfigurationError: ``tick_period`` 小于 1
        """
        ensure_tick_period(tick_period)
        self.tick_period = tick_period

    def on_tick(self, event: TickEvent) -> None:
        """
        节拍回调。

        :param event: 当前节拍事件
        """
        ...

    # ==== 生命周期 ====

    def start(self) -> None:
        """获取并启动本定时器持有的资源。

        默认实现不持有资源，什么都不做。子类可覆写以建立连接、打开文件等。
        :class:`~celestialflow.ticker.core_hub.TickHub` 在启动后台线程前按注册
        顺序调用本方法。实现必须是幂等的，且在失败时不残留半初始化状态。
        """
        ...

    def stop(self) -> None:
        """释放并关闭本定时器持有的资源。

        默认实现不持有资源，什么都不做。子类可覆写以关闭连接或文件。
        :class:`~celestialflow.ticker.core_hub.TickHub` 在后台线程结束后按注册
        顺序的**逆序**调用本方法。实现必须是幂等的。
        """
        ...

    def handle_exception(self, exception: Exception) -> None:
        """
        节拍回调自身抛出异常时的处理回调。

        默认实现将异常回溯打印到标准错误；子类可覆写以实现自定义策略（如收集、
        上报或忽略）。若本方法自身也抛出异常，则异常交由所属
        :class:`~celestialflow.ticker.core_hub.TickHub` 的 ``handle_exception``
        兜底，节拍循环不会因此退出。

        :param exception: 节拍回调抛出的异常
        """
        traceback.print_exception(exception)
